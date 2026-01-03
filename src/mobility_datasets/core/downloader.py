"""Download dataset files from any configured datasource with resume capability."""

import hashlib
import tarfile
import zipfile
from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Optional

import humanize
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


class DatasetDownloader:
    """Download and extract dataset files from any configured datasource.

    This class handles downloading and extracting dataset components with
    support for resuming interrupted downloads. It validates file integrity
    using MD5 checksums and automatically retries failed downloads with
    configurable retry limits. Works with any dataset (KITTI, nuScenes,
    Waymo, etc.) via YAML configuration.

    Parameters
    ----------
    dataset : str, optional
        Dataset name to download (e.g., "kitti", "nuscenes", "waymo").
        Must match a YAML config file name. Default is "kitti".
    data_dir : str, optional
        Base directory where dataset files will be downloaded and extracted.
        A subdirectory with the dataset name will be created.
        Default is "./data", resulting in "./data/{dataset}".

    Attributes
    ----------
    data_dir : pathlib.Path
        Path object pointing to the dataset-specific directory.
    config : DatasetConfig
        Loaded dataset configuration from YAML.

    Raises
    ------
    FileNotFoundError
        If dataset YAML configuration file does not exist.
    ValueError
        If YAML configuration is invalid.

    Examples
    --------
    Download a specific session from KITTI:

    >>> downloader = DatasetDownloader(dataset="kitti")
    >>> downloader.download("raw_data", sessions=["2011_09_26_drive_0001"])

    Download multiple sessions and keep ZIP files:

    >>> downloader = DatasetDownloader(dataset="kitti", data_dir="/mnt/data")
    >>> downloader.download(
    ...     "raw_data",
    ...     sessions=["2011_09_26_drive_0001", "2011_09_26_drive_0002"],
    ...     keep_zip=True
    ... )

    Download from nuScenes:

    >>> downloader = DatasetDownloader(dataset="nuscenes")
    >>> downloader.download("v1.0-trainval", sessions=["scene-0001"])

    Download all sessions in all collections:

    >>> downloader = DatasetDownloader(dataset="kitti")
    >>> downloader.download_all(keep_zip=False)
    """

    def __init__(self, dataset: str = "kitti", data_dir: str = "./data"):
        """Initialize downloader for a specific dataset.

        Parameters
        ----------
        dataset : str, optional
            Dataset name (e.g., "kitti", "nuscenes", "waymo").
            Default is "kitti".
        data_dir : str, optional
            Base directory for downloads. A subdirectory will be created
            for the dataset. Default is "./data".

        Raises
        ------
        FileNotFoundError
            If dataset YAML config does not exist.
        ValueError
            If YAML config is invalid.
        """

        self.config = ConfigProvider().get_from_datasource(dataset)
        self.data_dir = Path(data_dir) / dataset
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download(
        self,
        collection_id: str,
        sessions: List[str],
        keep_zip: bool = False,
        with_optional: bool = False,
    ):
        """Download dataset files for specified sessions in a collection.

        Downloads selected sessions with their associated parts. Validates
        file integrity using MD5 checksums, supports resuming interrupted
        downloads, and extracts archives. Optional parts are skipped unless
        `with_optional=True`.

        Parameters
        ----------
        collection_id : str
            Collection ID to download from (e.g., "raw_data", "synced_data",
            "v1.0-trainval"). Must exist in dataset configuration.
        sessions : List[str]
            List of session IDs to download. Sessions that don't exist in
            the collection are skipped with a warning.
        keep_zip : bool, optional
            If True, keep archive files after extraction. If False (default),
            remove them to save disk space.
        with_optional : bool, optional
            If True, also download optional parts (marked in config).
            If False (default), skip optional parts.

        Returns
        -------
        None
            Prints status messages to console.

        Raises
        ------
        ValueError
            If collection_id does not exist in dataset configuration.

        Examples
        --------
        Download specific sessions from KITTI raw_data:

        >>> downloader = DatasetDownloader(dataset="kitti")
        >>> downloader.download(
        ...     collection_id="raw_data",
        ...     sessions=["2011_09_26_drive_0001", "2011_09_26_drive_0002"],
        ...     keep_zip=False
        ... )

        Download from nuScenes with optional parts:

        >>> downloader = DatasetDownloader(dataset="nuscenes")
        >>> downloader.download(
        ...     "v1.0-trainval",
        ...     sessions=["scene-0001"],
        ...     with_optional=True
        ... )

        Notes
        -----
        For each session, downloads all parts and:
        1. Validates existing files against MD5 checksums
        2. Resumes incomplete downloads if possible
        3. Retries failed downloads up to 3 times
        4. Extracts archives based on format (zip, tar.gz, etc.)
        5. Optionally removes archives after extraction
        """

        collection = self.config.get_collection_or_raise(collection_id)

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

            for part in session.parts:
                if part.optional and not with_optional:
                    continue

                self._download_part(part)
                self._extract_file(part, keep_zip)

    def download_all(self, keep_zip: bool = False, with_optional: bool = False):
        """Download all sessions from all collections.

        Convenience method to download the complete dataset.
        Iterates through all available collections and downloads all sessions
        within each collection.

        Parameters
        ----------
        keep_zip : bool, optional
            If True, keep archive files after extraction. If False (default),
            remove them after successful extraction.
        with_optional : bool, optional
            If True, also download optional parts. If False (default),
            skip optional parts.

        Returns
        -------
        None
            Prints status messages to console.

        Warnings
        --------
        Downloading all components may require significant disk space
        (hundreds of GB for large datasets). Ensure sufficient disk space
        and network bandwidth are available before starting.

        Examples
        --------
        Download complete KITTI dataset with default settings:

        >>> downloader = DatasetDownloader(dataset="kitti")
        >>> downloader.download_all()

        Download all with optional parts and keep archives:

        >>> downloader = DatasetDownloader(dataset="nuscenes")
        >>> downloader.download_all(keep_zip=True, with_optional=True)

        Notes
        -----
        This operation may take several hours depending on internet
        connection speed and disk I/O performance. The download can be
        interrupted and resumed later - already downloaded files will
        be skipped automatically.

        See Also
        --------
        download : Download specific sessions from a collection
        health_check : Check if all files are available before downloading
        """

        for collection in self.config.collections:

            session_ids = [session.id for session in collection.sessions]
            self.download(
                collection_id=collection.id,
                sessions=session_ids,
                keep_zip=keep_zip,
                with_optional=with_optional,
            )

    def _calculate_md5(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate MD5 checksum of a file.

        Reads file in chunks to handle large files efficiently.

        Parameters
        ----------
        file_path : Path
            Path to file to hash.
        chunk_size : int, optional
            Number of bytes to read per iteration. Default 8192 bytes.

        Returns
        -------
        str
            Hexadecimal MD5 hash string.
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _validate_file(self, part: Part) -> FileStatus:
        """Validate downloaded file integrity.

        Checks existence, size, and MD5 checksum against expected values
        stored in configuration.

        Parameters
        ----------
        part : Part
            Part with download metadata to validate against.

        Returns
        -------
        FileStatus
            Status indicating file state:
            - VALID: File exists, size matches, MD5 matches
            - MISSING: File does not exist
            - PARTIAL: File exists but size is less than expected
            - WRONG_MD5: File size matches but MD5 differs
        """
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

    def _download_from_start(self, part: Part) -> None:
        """Download file from beginning.

        Removes any existing partial file and downloads from scratch.
        Shows progress bar using tqdm.

        Parameters
        ----------
        part : Part
            Part to download.
        """
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

    def _download_resume(self, part: Part) -> None:
        """Resume interrupted download using HTTP range requests.

        Checks server support for partial requests (Accept-Ranges header),
        then requests missing bytes. Falls back to full re-download if
        resume is not supported.

        Parameters
        ----------
        part : Part
            Part to resume downloading.
        """
        output_path = self.data_dir / part.download.filename
        current_size = output_path.stat().st_size
        expected_size = part.download.size_bytes
        url = part.download.url

        # Step 1: Check if server supports range requests
        try:
            head_response = requests.head(url, timeout=10)
            accepts_ranges = head_response.headers.get("accept-ranges", "").lower() == "bytes"
        except requests.exceptions.RequestException:
            print("⚠ Cannot check range support, re-downloading from start...")
            self._download_from_start(part)
            return

        # Step 2: Fallback if ranges not supported
        if not accepts_ranges:
            print("⚠ Server does not support partial downloads, re-downloading from start...")
            self._download_from_start(part)
            return

        # Step 3: Resume request with range header
        headers = {"Range": f"bytes={current_size}-"}

        try:
            response = requests.get(url, headers=headers, stream=True, timeout=10)

            # 206 = Partial Content (resume OK)
            # 200 = OK (server ignored range, full file returned)
            if response.status_code not in (206, 200):
                response.raise_for_status()

            # Step 4: Fallback if server ignored range
            if response.status_code == 200:
                print("⚠ Server returned full file, re-downloading from start...")
                self._download_from_start(part)
                return

            # Step 5: Continue in append mode
            remaining_bytes = expected_size - current_size

            with open(output_path, "ab") as f:
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

    def _download_part(self, part: Part, retries: int = 3) -> None:
        """Download and validate file with automatic retries.

        Validates existing file, resumes if partial, retries on failure.
        Automatically selects between fresh download and resume based on
        file state.

        Parameters
        ----------
        part : Part
            Part to download.
        retries : int, optional
            Number of retry attempts on failure. Default 3.
        """
        status = self._validate_file(part)

        if status == FileStatus.VALID:
            print(f"✓ {part.download.filename} already exists and is valid, skipping download")
            return

        while status != FileStatus.VALID:
            if retries <= 0:
                print(f"✗ Failed to download {part.download.filename} after multiple attempts.")
                return

            if status == FileStatus.PARTIAL:
                print(f"✗ {part.download.filename} is partially downloaded, resuming")
                self._download_resume(part)

            elif status == FileStatus.WRONG_MD5:
                print(f"✗ {part.download.filename} has wrong MD5 checksum, re-downloading")
                self._download_from_start(part)

            elif status == FileStatus.MISSING:
                print(f"Downloading {part.download.filename}...")
                self._download_from_start(part)

            status = self._validate_file(part)
            retries -= 1

    def _extract_file(self, part: Part, keep_zip: bool) -> None:
        """Extract archive based on format from config.

        Dispatches to appropriate extractor (ZIP, TAR.GZ, etc.).
        Some formats (like TFRecord) don't need extraction.

        Parameters
        ----------
        part : Part
            Part to extract. Format specified in part.download.format.
        keep_zip : bool
            If True, keep archive after extraction. If False, remove it.
        """
        file_path = self.data_dir / part.download.filename

        if not file_path.exists():
            print(f"✗ {part.download.filename} not found, skipping extraction")
            return

        format = part.download.format

        if format == "zip":
            print(f"Extracting {file_path.name}...")
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(self.data_dir)
            print(f"✓ Extracted {file_path.name}")

        elif format == "tar.gz":
            print(f"Extracting {file_path.name}...")
            with tarfile.open(file_path, "r:gz") as tar_ref:
                tar_ref.extractall(self.data_dir)
            print(f"✓ Extracted {file_path.name}")

        elif format == "tfrecord":
            # TFRecords are used directly, no extraction needed
            print(f"✓ {file_path.name} is ready to use (no extraction needed)")
            return

        else:
            print(f"⚠ Unknown format: {format}, skipping extraction")
            return

        if not keep_zip:
            file_path.unlink()
            print(f"✓ Removed {file_path.name}")

    def health_check(self) -> Dict[str, bool]:
        """Check if all dataset files are available on remote server.

        Performs HTTP HEAD requests to verify that all files referenced
        in the configuration are still available and accessible. Does not
        download files, only checks URLs.

        Returns
        -------
        Dict[str, bool]
            Dictionary mapping file IDs to availability status.
            Key format: "collection_id/session_id/part_id"
            Value: True if available (HTTP 200), False otherwise.

        Examples
        --------
        Check KITTI availability before downloading:

        >>> downloader = DatasetDownloader(dataset="kitti")
        >>> status = downloader.health_check()
        >>> unavailable = [k for k, v in status.items() if not v]
        >>> if unavailable:
        ...     print(f"Warning: {len(unavailable)} files unavailable")

        Notes
        -----
        This method:
        - Does not download files (safe to run anytime)
        - Prints progress to console
        - Takes time proportional to number of files (one HEAD request per file)
        - Useful before long downloads to catch missing files early
        """
        print("Checking dataset availability...")
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

    def get_download_size(
        self,
        collection_id: str,
        sessions: Optional[List[str]] = None,
        with_optional: bool = False,
    ) -> Dict[str, int | str | dict]:
        """Calculate total download size for selected sessions.

        Parameters
        ----------
        collection_id : str
            Collection to estimate.
        sessions : List[str], optional
            Sessions to include. If None, all sessions.
        with_optional : bool, optional
            Include optional parts. Default False.

        Returns
        -------
        Dict
            Size breakdown:
            {
                "total_bytes": 1234567890,
                "total_readable": "1.2 GB",
                "parts": {
                    "part_id": 1000000,
                    ...
                },
                "sessions_count": 5,
                "parts_count": 15,
            }

        Examples
        --------
        >>> downloader = DatasetDownloader("kitti")
        >>> size = downloader.get_download_size(
        ...     "raw_data",
        ...     sessions=["2011_09_26_drive_0001"]
        ... )
        >>> print(size["total_readable"])
        1.2 GB
        >>> print(size["total_bytes"])
        1234567890
        """

        collection = self.config.get_collection_or_raise(collection_id)

        # Validate sessions
        valid_sessions = []
        if sessions is None:
            valid_sessions = collection.sessions

        else:
            for session_id in sessions:
                session = collection.get_session_by_id(session_id)
                if session is None:
                    print(f"⚠ Session '{session_id}' not found")
                else:
                    valid_sessions.append(session)

        # Calculate sizes
        total_bytes = 0
        parts_breakdown = {}
        for session in valid_sessions:
            for part in session.parts:
                if part.optional and not with_optional:
                    continue

                size_bytes = part.download.size_bytes
                total_bytes += size_bytes
                if part.id not in parts_breakdown:
                    parts_breakdown[part.id] = 0
                parts_breakdown[part.id] += size_bytes

        return {
            "total_bytes": total_bytes,
            "total_readable": humanize.naturalsize(total_bytes),
            "parts": parts_breakdown,
            "sessions_count": len(valid_sessions),
            "parts_count": sum(len(s.parts) for s in valid_sessions),
        }
