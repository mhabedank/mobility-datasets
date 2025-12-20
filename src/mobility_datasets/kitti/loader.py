"""Download KITTI tracking dataset from S3."""

import zipfile
from pathlib import Path
from typing import List

import requests
from tqdm import tqdm


class KITTIDownloader:
    """
    Download KITTI tracking dataset files from AWS S3.

    This class handles downloading and extracting KITTI tracking dataset
    components from the official AWS S3 bucket. It supports selective
    downloading of specific components (GPS/IMU, calibration, images, etc.)
    and provides progress tracking for large downloads.

    The downloader automatically creates the target directory if it doesn't
    exist and can optionally keep or remove ZIP files after extraction.

    Parameters
    ----------
    data_dir : str, optional
        Directory where dataset files will be downloaded and extracted.
        Default is "./data/kitti". The directory will be created if it
        doesn't exist.

    Attributes
    ----------
    BASE_URL : str
        AWS S3 base URL for KITTI dataset files.
    AVAILABLE_FILES : dict
        Dictionary mapping component names to their ZIP filenames.
        Available components: oxts, calib, label, image_left, image_right, velodyne.
    data_dir : pathlib.Path
        Path object pointing to the data directory.

    Examples
    --------
    Download GPS/IMU and calibration data:

    >>> from mobility_datasets.kitti.loader import KITTIDownloader
    >>> downloader = KITTIDownloader(data_dir="./data/kitti")
    >>> downloader.download(["oxts", "calib"])
    Downloading data_tracking_oxts.zip...
    ✓ Downloaded data_tracking_oxts.zip
    Extracting data_tracking_oxts.zip...
    ✓ Extracted data_tracking_oxts.zip
    ✓ Removed data_tracking_oxts.zip

    Download all components and keep ZIP files:

    >>> downloader.download_all(keep_zip=True)
    Downloading 6 components...

    Notes
    -----
    The KITTI tracking dataset contains the following components:

    - **oxts** (8 MB): GPS/IMU data at 10-100 Hz
    - **calib** (0.1 MB): Camera and sensor calibration files
    - **label** (2.2 MB): Object detection labels
    - **image_left** (15 GB): Left camera images
    - **image_right** (14 GB): Right camera images
    - **velodyne** (35 GB): LiDAR point clouds

    Large components (images, velodyne) may take significant time to download
    depending on your internet connection.

    """

    BASE_URL = "https://s3.eu-central-1.amazonaws.com/avg-kitti/"

    AVAILABLE_FILES = {
        "oxts": "data_tracking_oxts.zip",
        "calib": "data_tracking_calib.zip",
        "label": "data_tracking_label_2.zip",
        "image_left": "data_tracking_image_2.zip",
        "image_right": "data_tracking_image_3.zip",
        "velodyne": "data_tracking_velodyne.zip",
    }

    def __init__(self, data_dir: str = "./data/kitti"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download(self, components: List[str], keep_zip: bool = False):
        """
        Download and extract specified dataset components.

        Downloads the requested components from AWS S3, extracts them to
        the data directory, and optionally removes the ZIP files after
        extraction. Already existing files are skipped.

        Parameters
        ----------
        components : List[str]
            List of component names to download. Valid options are:
            'oxts', 'calib', 'label', 'image_left', 'image_right', 'velodyne'.
            Invalid component names will be skipped with a warning message.
        keep_zip : bool, optional
            If True, keep ZIP files after extraction. If False (default),
            ZIP files are deleted after successful extraction to save disk space.

        Raises
        ------
        requests.exceptions.RequestException
            If download fails due to network issues or invalid URL.
        zipfile.BadZipFile
            If downloaded file is corrupted or not a valid ZIP archive.

        Examples
        --------
        Download only GPS/IMU data:

        >>> downloader = KITTIDownloader()
        >>> downloader.download(["oxts"])

        Download multiple components and keep ZIP files:

        >>> downloader.download(["oxts", "calib", "label"], keep_zip=True)

        Invalid component names are handled gracefully:

        >>> downloader.download(["oxts", "invalid_component"])
        Unknown component: invalid_component

        Notes
        -----
        The method will skip downloading if the ZIP file already exists in
        the target directory. To re-download, manually delete the existing
        ZIP file first.
        """
        for component in components:
            if component not in self.AVAILABLE_FILES:
                print(f"Unknown component: {component}")
                continue

            self._download_file(component)
            self._unzip_file(component, keep_zip)

    def download_all(self, keep_zip: bool = False):
        """
        Download and extract all available dataset components.

        Convenience method to download the complete KITTI tracking dataset.
        This includes all sensor data: GPS/IMU, calibration, labels, stereo
        images, and LiDAR point clouds.

        Parameters
        ----------
        keep_zip : bool, optional
            If True, keep ZIP files after extraction. If False (default),
            ZIP files are deleted after successful extraction. Default is False.

        Warnings
        --------
        Downloading all components requires approximately 64 GB of disk space
        for the ZIP files, plus additional space for extracted data. Ensure
        sufficient disk space is available before starting the download.

        Examples
        --------
        Download complete dataset:

        >>> downloader = KITTIDownloader(data_dir="/mnt/storage/kitti")
        >>> downloader.download_all()
        Downloading 6 components...

        Download and preserve ZIP files for backup:

        >>> downloader.download_all(keep_zip=True)

        Notes
        -----
        This operation may take several hours depending on your internet
        connection speed. The download can be safely interrupted and resumed
        later, as already downloaded files will be skipped.

        See Also
        --------
        download : Download specific components instead of all
        """
        components = list(self.AVAILABLE_FILES.keys())
        print(f"Downloading {len(components)} components...")
        self.download(components, keep_zip)

    def _download_file(self, component: str):
        """
        Download a single component file from S3.

        Internal method that handles the HTTP request, progress tracking,
        and file writing for a single dataset component.

        Parameters
        ----------
        component : str
            Component name (must be a key in AVAILABLE_FILES).

        Notes
        -----
        This is an internal method and should not be called directly.
        Use the `download()` or `download_all()` methods instead.
        """
        filename = self.AVAILABLE_FILES[component]
        url = self.BASE_URL + filename
        output_path = self.data_dir / filename

        if output_path.exists():
            print(f"✓ {filename} already exists")
            return

        print(f"Downloading {filename}...")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        with open(output_path, "wb") as f:
            with tqdm(total=total_size, unit="B", unit_scale=True, unit_divisor=1024) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"✓ Downloaded {filename}")

    def _unzip_file(self, component: str, keep_zip: bool):
        """
        Extract a downloaded ZIP file.

        Internal method that extracts the ZIP archive and optionally
        removes it after successful extraction.

        Parameters
        ----------
        component : str
            Component name (must be a key in AVAILABLE_FILES).
        keep_zip : bool
            Whether to keep the ZIP file after extraction.

        Notes
        -----
        This is an internal method and should not be called directly.
        Use the `download()` or `download_all()` methods instead.
        """
        filename = self.AVAILABLE_FILES[component]
        zip_path = self.data_dir / filename

        if not zip_path.exists():
            print(f"✗ {filename} not found, skipping extraction")
            return

        print(f"Extracting {filename}...")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(self.data_dir)

        print(f"✓ Extracted {filename}")

        if not keep_zip:
            zip_path.unlink()
            print(f"✓ Removed {filename}")
