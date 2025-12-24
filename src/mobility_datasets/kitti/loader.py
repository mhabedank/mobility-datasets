"""Download KITTI tracking dataset from S3 with resume capability."""

import hashlib
import zipfile
from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Optional

import requests
from tqdm import tqdm

from mobility_datasets.config.provider import ConfigProvider, Part


class FileStatus(IntEnum):
    """File validation status enumeration.

    Attributes
    ----------
    VALID : int
        File exists, has correct size, and MD5 checksum matches.
    MISSING : int
        File does not exist on disk.
    PARTIAL : int
        File exists but size is less than expected (incomplete download).
    WRONG_MD5 : int
        File exists with correct size but MD5 checksum does not match.
    """

    VALID = 1
    MISSING = 2
    PARTIAL = 3
    WRONG_MD5 = 4


class KITTIDownloader:
    """Download KITTI tracking dataset files from AWS S3.

    This class handles downloading and extracting KITTI tracking dataset
    components with support for resuming interrupted downloads. It validates
    file integrity using MD5 checksums and automatically retries failed
    downloads with configurable retry limits.

    Parameters
    ----------
    data_dir : str, optional
        Directory where dataset files will be downloaded and extracted.
        Default is "./data/kitti". The directory will be created if it
        doesn't exist.

    Attributes
    ----------
    data_dir : pathlib.Path
        Path object pointing to the data directory.
    config : DatasetConfig
        Loaded KITTI dataset configuration from YAML.

    Examples
    --------
    Download a specific session with default settings:

    >>> downloader = KITTIDownloader(data_dir="./data/kitti")
    >>> downloader.download("raw_data", sessions=["2011_09_26_drive_0001"])

    Download multiple sessions and keep ZIP files:

    >>> downloader.download(
    ...     "raw_data",
    ...     sessions=["2011_09_26_drive_0001", "2011_09_26_drive_0002"],
    ...     keep_zip=True
    ... )

    Download all sessions in all collections:

    >>> downloader.download_all(keep_zip=False)
    """

    def __init__(self, data_dir: str = "./data/kitti"):
        """Initialize the KITTI downloader.

        Parameters
        ----------
        data_dir : str, optional
            Target directory for downloads. Default is "./data/kitti".
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config = ConfigProvider().get_from_datasource("kitti")

    def download(
        self,
        collection_id: str = "raw_data",
        sessions: Optional[List[str]] = None,
        keep_zip: bool = False,
        with_unsynced: bool = False,
    ):
        """Download dataset files for specified sessions in a collection.

        Downloads selected sessions with their associated parts (synced, calib,
        tracklets, and optionally unsynced). Extracts ZIP files and optionally
        removes them after extraction.

        Parameters
        ----------
        collection_id : str, optional
            Collection ID to download from (e.g., "raw_data", "synced_data").
            Default is "raw_data".
        sessions : List[str], optional
            List of session IDs to download. If None, defaults to
            ["2011_09_26_drive_0001"]. Sessions that don't exist in the
            collection are skipped with a warning.
        keep_zip : bool, optional
            If True, keep ZIP files after extraction. If False (default),
            remove ZIP files to save disk space.
        with_unsynced : bool, optional
            If True, also download unsynced_rectified variant. If False
            (default), only download synced_rectified, calib, and tracklets.

        Returns
        -------
        None
            Prints status messages to console.

        Raises
        ------
        None
            Non-existent collections or sessions are printed as warnings
            and skipped gracefully.

        Examples
        --------
        Download raw_data collection with 3 sessions:

        >>> downloader.download(
        ...     collection_id="raw_data",
        ...     sessions=["2011_09_26_drive_0001", "2011_09_26_drive_0002"],
        ...     keep_zip=False
        ... )

        Download with unsynced variants included:

        >>> downloader.download(
        ...     "raw_data",
        ...     sessions=["2011_09_26_drive_0001"],
        ...     with_unsynced=True
        ... )

        Notes
        -----
        For each session, downloads the following parts in order:

        - unsynced_rectified (if with_unsynced=True)
        - synced_rectified
        - calib (calibration files)
        - tracklets (annotation files)

        Each part is downloaded, validated, and extracted independently.
        """
        if sessions is None:
            sessions = ["2011_09_26_drive_0001"]

        collection = self.config.collection_by_id(collection_id)

        if collection is None:
            print(f"Collection '{collection_id}' not found in config.")
            return

        valid_sessions = []
        for session_id in sessions:
            session = collection.get_session_by_id(session_id)
            if session is None:
                print(
                    f"Session '{session_id}' not found in collection "
                    f"'{collection_id}'. Skipping."
                )
            else:
                valid_sessions.append(session)

        for session in valid_sessions:
            print(f"Downloading session: {session.name}")

            if with_unsynced:
                unsynced = session.get_part_by_id("unsynced_rectified")
                self._download_part(unsynced)
                self._unzip_file(unsynced, keep_zip)

            synced = session.get_part_by_id("synced_rectified")
            calib = session.get_part_by_id("calib")
            tracklets = session.get_part_by_id("tracklets")

            for part in [synced, calib, tracklets]:
                self._download_part(part)
                self._unzip_file(part, keep_zip)

    def download_all(self, keep_zip: bool = False, with_unsynced: bool = False):
        """Download all sessions from all collections.

        Convenience method to download the complete KITTI tracking dataset.
        Iterates through all available collections and downloads all sessions
        within each collection.

        Parameters
        ----------
        keep_zip : bool, optional
            If True, keep ZIP files after extraction. If False (default),
            remove ZIP files after successful extraction.
        with_unsynced : bool, optional
            If True, download unsynced_rectified variant for each session.
            If False (default), only download synced_rectified, calib,
            and tracklets.

        Returns
        -------
        None
            Prints status messages to console.

        Warnings
        --------
        Downloading all components requires significant disk space
        (~170 GB for raw_data collection). Ensure sufficient disk space
        is available before starting.

        Examples
        --------
        Download complete dataset with default settings:

        >>> downloader = KITTIDownloader()
        >>> downloader.download_all()

        Download all with unsynced variants and keep ZIPs:

        >>> downloader.download_all(keep_zip=True, with_unsynced=True)

        Notes
        -----
        This operation may take several hours depending on internet
        connection speed and disk I/O performance. The download can be
        interrupted and resumed later - already downloaded files will
        be skipped.

        See Also
        --------
        download : Download specific sessions
        """

        for collection in self.config.collections:

            session_ids = [session.id for session in collection.sessions]
            self.download(
                collection_id=collection.id,
                sessions=session_ids,
                keep_zip=keep_zip,
                with_unsynced=with_unsynced,
            )

    def _calculate_md5(self, file_path: Path, chunk_size: int = 8192) -> str:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _validate_file(self, part: Part) -> FileStatus:
        file_path = self.data_dir / part.download.filename

        if not file_path.exists():
            return FileStatus.MISSING

        actual_size = file_path.stat().st_size
        if actual_size != part.download.size_bytes:
            return FileStatus.PARTIAL

        existing_md5 = self._calculate_md5(file_path)
        if existing_md5 != part.download.md5:
            return FileStatus.WRONG_MD5

        return FileStatus.VALID

    def _download_from_start(self, part: Part):

        output_path = self.data_dir / part.download.filename
        expected_size = part.download.size_bytes

        if output_path.exists():
            output_path.unlink()

        response = requests.get(part.download.url, stream=True, timeout=10)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", expected_size))

        with open(output_path, "wb") as f:
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=part.download.filename,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

    def _download_resume(self, part: Part):
        output_path = self.data_dir / part.download.filename
        current_size = output_path.stat().st_size
        expected_size = part.download.size_bytes
        url = part.download.url

        # Schritt 1: Prüfe ob Server Range-Requests unterstützt
        try:
            head_response = requests.head(url, timeout=10)
            accepts_ranges = head_response.headers.get("accept-ranges", "").lower() == "bytes"
        except requests.exceptions.RequestException:
            print("⚠ Cannot check range support, re-downloading from start...")
            self._download_from_start(part)
            return

        # Schritt 2: Fallback wenn keine Ranges unterstützt
        if not accepts_ranges:
            print("⚠ Server does not support partial downloads, re-downloading from start...")
            self._download_from_start(part)
            return

        # Schritt 3: Resume-Request mit Range Header
        headers = {"Range": f"bytes={current_size}-"}

        try:
            response = requests.get(url, headers=headers, stream=True, timeout=10)

            # 206 = Partial Content (Resume OK)
            # 200 = OK (Server ignorierte Range, ganze Datei)
            if response.status_code not in (206, 200):
                response.raise_for_status()

            # Schritt 4: Fallback wenn Server Range ignorierte
            if response.status_code == 200:
                print("⚠ Server returned full file, re-downloading from start...")
                self._download_from_start(part)
                return

            # Schritt 5: Fortsetzen (Append Mode!)
            remaining_bytes = expected_size - current_size

            with open(output_path, "ab") as f:  # Append, nicht overwrite!
                with tqdm(
                    total=remaining_bytes,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=f"{part.download.filename} (resume)",
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            if self._validate_file(part) != FileStatus.VALID:
                print("⚠ Downloaded file is still invalid after resume.")
                print("⚠ Re-downloading from start...")
                output_path.unlink()
                self._download_from_start(part)

        except requests.exceptions.RequestException as e:
            print(f"⚠ Error during resume: {e}")
            print("⚠ Re-downloading from start...")
            self._download_from_start(part)

    def _download_part(self, part: Part, retries: int = 3):

        status = self._validate_file(part)

        if status == FileStatus.VALID:
            print(f"✓ {part.download.filename} already exists and is ", "valid, skipping download")
            return

        while status != FileStatus.VALID:
            if retries <= 0:
                print(f"✗ Failed to download {part.download.filename} after ", "multiple attempts.")
                return

            if status == FileStatus.PARTIAL:
                print(f"✗ {part.download.filename} is partially downloaded, ", "re-downloading")
                self._download_resume(part)

            elif status == FileStatus.WRONG_MD5:
                print(f"✗ {part.download.filename} has wrong MD5 checksum, " "re-downloading")
                self._download_from_start(part)

            elif status == FileStatus.MISSING:
                print(f"Downloading {part.download.filename}...")
                self._download_from_start(part)

            status = self._validate_file(part)
            retries -= 1

    def _unzip_file(self, part: Part, keep_zip: bool):
        zip_path = self.data_dir / part.download.filename

        if not zip_path.exists():
            print(f"✗ {part.download.filename} not found, skipping extraction")
            return

        print(f"Extracting {part.download.filename}...")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(self.data_dir)

        print(f"✓ Extracted {part.download.filename}")

        if not keep_zip:
            zip_path.unlink()
            print(f"✓ Removed {part.download.filename}")

    def health_check(self) -> Dict[str, bool]:

        print("Checking KITTI dataset availability on S3...")
        print("-" * 60)

        status = {}

        for collection in self.config.collections:
            for session in collection.sessions:
                for part in session.parts:

                    long_id = f"{collection.id}/{session.id}/{part.id}"
                    try:
                        response = requests.head(part.download.url, timeout=10)

                        if response.status_code == 200:
                            print(f"✓ {long_id}: {part.download.filename:40s} (Available)")
                            status[long_id] = True
                        else:
                            print(
                                f"✗ {long_id}: {part.download.filename:40s} (HTTP {response.status_code})"
                            )
                            status[long_id] = False

                    except requests.exceptions.RequestException as e:
                        print(
                            f"✗ {long_id}: {part.download.filename:40s} (Error: {type(e).__name__})"
                        )
                        status[long_id] = False

        print("-" * 60)
        available = sum(status.values())
        total = len(status)
        print(f"Summary: {available}/{total} files available")

        return status
