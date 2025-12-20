"""Download nuScenes dataset from CloudFront."""

import tarfile
from pathlib import Path
from typing import Dict, List

import requests
from tqdm import tqdm


class NuScenesDownloader:
    """
    Download nuScenes dataset files from CloudFront CDN.

    This class handles downloading and extracting nuScenes dataset
    components from the official CloudFront distribution. It supports selective
    downloading of specific components (metadata, LiDAR, cameras, radar)
    and provides progress tracking for large downloads.

    The downloader automatically creates the target directory if it doesn't
    exist and can optionally keep or remove archive files after extraction.

    Parameters
    ----------
    data_dir : str, optional
        Directory where dataset files will be downloaded and extracted.
        Default is "./data/nuscenes". The directory will be created if it
        doesn't exist.
    version : str, optional
        Dataset version to download. Options are:
        - "mini": 10 scenes, ~10 GB total (default)
        - "trainval": 850 scenes, ~350 GB total
        - "test": 150 scenes, ~44 GB total

    Attributes
    ----------
    BASE_URL : str
        CloudFront base URL for nuScenes dataset files.
    AVAILABLE_FILES : dict
        Dictionary mapping component names to their archive filenames.
        Available components vary by version.
    data_dir : pathlib.Path
        Path object pointing to the data directory.
    version : str
        Dataset version being used.

    Examples
    --------
    Download metadata and LiDAR keyframes (minimal setup):

    >>> from mobility_datasets.nuscenes.loader import NuScenesDownloader
    >>> downloader = NuScenesDownloader(data_dir="./data/nuscenes")
    >>> downloader.download(["metadata", "lidar_keyframes"])
    Downloading v1.0-mini.tgz...
    ✓ Downloaded v1.0-mini.tgz
    Extracting v1.0-mini.tgz...
    ✓ Extracted v1.0-mini.tgz
    ✓ Removed v1.0-mini.tgz

    Download all components and keep archives:

    >>> downloader.download_all(keep_archive=True)
    Downloading all components for version 'mini'...

    Notes
    -----
    The nuScenes dataset contains the following types of components:

    - **metadata** (~100 MB): Required JSON files containing scene info,
      ego poses, calibration data, and sensor metadata
    - **lidar_keyframes** (500 MB mini / 150 GB full): LiDAR @ 2 Hz
    - **lidar_sweeps** (5 GB mini / 200 GB full): LiDAR @ 20 Hz
    - **cameras** (60 GB mini / 300 GB full): All 6 cameras @ 2 Hz
    - **radar** (10 GB mini / 50 GB full): All 5 radars @ 2 Hz

    Unlike KITTI which uses ZIP archives, nuScenes uses tar and tgz formats.

    Large components may take significant time to download depending on
    your internet connection.

    """

    BASE_URL = "https://d36yt3mvayqw5m.cloudfront.net/#public/v1.0/"

    # Version-specific file mappings
    _MINI_FILES = {
        "metadata": "v1.0-mini.tgz",
        "lidar_keyframes": "samples/LIDAR_TOP.tar",
        "lidar_sweeps": "sweeps/LIDAR_TOP.tar",
        "cam_front": "samples/CAM_FRONT.tar",
        "cam_front_left": "samples/CAM_FRONT_LEFT.tar",
        "cam_front_right": "samples/CAM_FRONT_RIGHT.tar",
        "cam_back": "samples/CAM_BACK.tar",
        "cam_back_left": "samples/CAM_BACK_LEFT.tar",
        "cam_back_right": "samples/CAM_BACK_RIGHT.tar",
        "radar_front": "samples/RADAR_FRONT.tar",
        "radar_front_left": "samples/RADAR_FRONT_LEFT.tar",
        "radar_front_right": "samples/RADAR_FRONT_RIGHT.tar",
        "radar_back_left": "samples/RADAR_BACK_LEFT.tar",
        "radar_back_right": "samples/RADAR_BACK_RIGHT.tar",
    }

    _TRAINVAL_FILES = {
        "metadata": "v1.0-trainval_meta.tgz",
        "lidar_keyframes": [f"v1.0-trainval{i:02d}_blobs.tar" for i in range(1, 11)],
        "cam_front": "samples/CAM_FRONT.tar",
        "cam_front_left": "samples/CAM_FRONT_LEFT.tar",
        "cam_front_right": "samples/CAM_FRONT_RIGHT.tar",
        "cam_back": "samples/CAM_BACK.tar",
        "cam_back_left": "samples/CAM_BACK_LEFT.tar",
        "cam_back_right": "samples/CAM_BACK_RIGHT.tar",
        "radar_front": "samples/RADAR_FRONT.tar",
        "radar_front_left": "samples/RADAR_FRONT_LEFT.tar",
        "radar_front_right": "samples/RADAR_FRONT_RIGHT.tar",
        "radar_back_left": "samples/RADAR_BACK_LEFT.tar",
        "radar_back_right": "samples/RADAR_BACK_RIGHT.tar",
    }

    _TEST_FILES = {
        "metadata": "v1.0-test_meta.tgz",
    }

    def __init__(self, data_dir: str = "./data/nuscenes", version: str = "mini"):
        """
        Initialize NuScenesDownloader.

        Parameters
        ----------
        data_dir : str, optional
            Target directory for downloads. Default is "./data/nuscenes".
        version : str, optional
            Dataset version: "mini", "trainval", or "test". Default is "mini".

        Raises
        ------
        ValueError
            If version is not one of: "mini", "trainval", "test".
        """
        if version not in ["mini", "trainval", "test"]:
            raise ValueError(f"Invalid version: {version}. Must be 'mini', 'trainval', or 'test'.")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.version = version

        # Select file mapping based on version
        if version == "mini":
            self.AVAILABLE_FILES = self._MINI_FILES
        elif version == "trainval":
            self.AVAILABLE_FILES = self._TRAINVAL_FILES
        else:  # test
            self.AVAILABLE_FILES = self._TEST_FILES

    def download(self, components: List[str], keep_archive: bool = False):
        """
        Download and extract specified dataset components.

        Downloads the requested components from CloudFront, extracts them to
        the data directory, and optionally removes the archive files after
        extraction. Already existing files are skipped.

        Parameters
        ----------
        components : List[str]
            List of component names to download. Valid options depend on version.

            Common components:
            - 'metadata': Scene info, ego poses, calibration (required for usage)
            - 'lidar_keyframes': LiDAR point clouds @ 2 Hz
            - 'lidar_sweeps': LiDAR point clouds @ 20 Hz (high frequency)

            Individual sensors:
            - 'cam_front', 'cam_back', 'cam_front_left', 'cam_front_right',
              'cam_back_left', 'cam_back_right'
            - 'radar_front', 'radar_front_left', 'radar_front_right',
              'radar_back_left', 'radar_back_right'

            Invalid component names will be skipped with a warning message.

        keep_archive : bool, optional
            If True, keep archive files after extraction. If False (default),
            archive files are deleted after successful extraction to save disk space.

        Raises
        ------
        requests.exceptions.RequestException
            If download fails due to network issues or invalid URL.
        tarfile.TarError
            If downloaded file is corrupted or not a valid tar archive.

        Examples
        --------
        Download minimal setup for sensor fusion:

        >>> downloader = NuScenesDownloader()
        >>> downloader.download(["metadata", "lidar_keyframes"])

        Download specific cameras:

        >>> downloader.download(["metadata", "cam_front", "cam_back"])

        Download and keep archives for backup:

        >>> downloader.download(["metadata", "lidar_keyframes"], keep_archive=True)

        Invalid component names are handled gracefully:

        >>> downloader.download(["metadata", "invalid_sensor"])
        Unknown component: invalid_sensor
        Available components: metadata, lidar_keyframes, cam_front, ...

        Notes
        -----
        The method will skip downloading if the archive file already exists in
        the target directory. To re-download, manually delete the existing
        archive file first.

        For the "trainval" version, the "lidar_keyframes" component consists
        of 10 separate archive files which will all be downloaded automatically.
        """
        for component in components:
            if component not in self.AVAILABLE_FILES:
                print(f"Unknown component: {component}")
                print(f"Available components: {', '.join(self.AVAILABLE_FILES.keys())}")
                continue

            files = self.AVAILABLE_FILES[component]

            # Handle both single file and list of files
            if isinstance(files, str):
                files = [files]

            # Download and extract each file
            for filename in files:
                self._download_file(filename)
                self._extract_file(filename, keep_archive)

    def download_all(self, keep_archive: bool = False):
        """
        Download and extract all available dataset components.

        Convenience method to download the complete nuScenes dataset version.
        This includes metadata and all sensor data.

        Parameters
        ----------
        keep_archive : bool, optional
            If True, keep archive files after extraction. If False (default),
            archive files are deleted after successful extraction. Default is False.

        Warnings
        --------
        Downloading all components requires significant disk space:

        - **mini**: ~10 GB download + extraction space
        - **trainval**: ~350 GB download + extraction space
        - **test**: ~44 GB download + extraction space

        Ensure sufficient disk space is available before starting the download.
        Downloads can take several hours depending on your internet connection.

        Examples
        --------
        Download complete mini dataset:

        >>> downloader = NuScenesDownloader(version="mini")
        >>> downloader.download_all()
        Downloading all components for version 'mini'...

        Download complete trainval and preserve archives:

        >>> downloader = NuScenesDownloader(
        ...     data_dir="/mnt/storage/nuscenes",
        ...     version="trainval"
        ... )
        >>> downloader.download_all(keep_archive=True)

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
        print(f"Downloading all components for version '{self.version}'...")
        self.download(components, keep_archive)

    def _download_file(self, filename: str):
        """
        Download a single file from CloudFront.

        Internal method that handles the HTTP request, progress tracking,
        and file writing for a single dataset component file.

        Parameters
        ----------
        filename : str
            Relative path/filename to download (e.g., "v1.0-mini.tgz" or
            "samples/LIDAR_TOP.tar").

        Notes
        -----
        This is an internal method and should not be called directly.
        Use the `download()` or `download_all()` methods instead.
        """
        url = self.BASE_URL + filename

        # Extract just the filename for local storage
        output_path = self.data_dir / Path(filename).name

        if output_path.exists():
            print(f"✓ {output_path.name} already exists")
            return

        print(f"Downloading {output_path.name}...")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        with open(output_path, "wb") as f:
            with tqdm(total=total_size, unit="B", unit_scale=True, unit_divisor=1024) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"✓ Downloaded {output_path.name}")

    def _extract_file(self, filename: str, keep_archive: bool):
        """
        Extract a downloaded tar/tgz archive.

        Internal method that extracts the tar archive and optionally
        removes it after successful extraction.

        Parameters
        ----------
        filename : str
            Relative path/filename to extract (e.g., "v1.0-mini.tgz").
        keep_archive : bool
            Whether to keep the archive file after extraction.

        Notes
        -----
        This is an internal method and should not be called directly.
        Use the `download()` or `download_all()` methods instead.
        """
        archive_path = self.data_dir / Path(filename).name

        if not archive_path.exists():
            print(f"✗ {archive_path.name} not found, skipping extraction")
            return

        print(f"Extracting {archive_path.name}...")

        # Determine compression type
        if archive_path.suffix in [".tgz", ".gz"]:
            mode = "r:gz"
        else:
            mode = "r"

        with tarfile.open(archive_path, mode) as tar:
            tar.extractall(self.data_dir)

        print(f"✓ Extracted {archive_path.name}")

        if not keep_archive:
            archive_path.unlink()
            print(f"✓ Removed {archive_path.name}")

    def health_check(self) -> Dict[str, bool]:
        """
        Check availability of all KITTI dataset files on S3.

        Performs HTTP HEAD requests to verify that all dataset files are
        accessible without downloading them. Useful for verifying download
        URLs before attempting large downloads or in integration tests.

        Returns
        -------
        Dict[str, bool]
            Dictionary mapping component names to their availability status.
            True if file exists and is accessible (HTTP 200), False otherwise.

        Examples
        --------
        Check availability before downloading:

        >>> from mobility_datasets.kitti.loader import KITTIDownloader
        >>> downloader = KITTIDownloader()
        >>> status = downloader.health_check()
        Checking KITTI dataset availability on S3...
        Base URL: https://s3.eu-central-1.amazonaws.com/avg-kitti/
        ----------------------------------------
        ✓ oxts            : data_tracking_oxts.zip (8.1 MB)
        ✓ calib           : data_tracking_calib.zip (0.1 MB)
        ✓ label           : data_tracking_label_2.zip (2.2 MB)
        ✓ image_left      : data_tracking_image_2.zip (15000.0 MB)
        ✓ image_right     : data_tracking_image_3.zip (14000.0 MB)
        ✓ velodyne        : data_tracking_velodyne.zip (35000.0 MB)
        ----------------------------------------
        Summary: 6/6 files available

        >>> print(status)
        {'oxts': True, 'calib': True, 'label': True, ...}

        >>> if all(status.values()):
        ...     downloader.download(["oxts", "calib"])

        Only download if files are available:

        >>> status = downloader.health_check()
        >>> available_components = [k for k, v in status.items() if v]
        >>> downloader.download(available_components)

        Notes
        -----
        This method only checks if files exist and are accessible via HTTP HEAD.
        It does not verify file integrity or completeness.

        Network errors or temporary unavailability will result in False status
        for affected components.

        The method has a 10-second timeout per file check.

        See Also
        --------
        download : Download dataset components
        download_all : Download all available components
        """
        print("Checking KITTI dataset availability on S3...")
        print(f"Base URL: {self.BASE_URL}")
        print("-" * 60)

        status = {}

        for component, filename in self.AVAILABLE_FILES.items():
            url = self.BASE_URL + filename

            try:
                response = requests.head(url, timeout=10)

                if response.status_code == 200:
                    # Extract file size from Content-Length header
                    size_bytes = int(response.headers.get("content-length", 0))
                    size_mb = size_bytes / (1024 * 1024)

                    print(f"✓ {component:15s}: {filename:40s} ({size_mb:.1f} MB)")
                    status[component] = True
                else:
                    print(f"✗ {component:15s}: {filename:40s} (HTTP {response.status_code})")
                    status[component] = False

            except requests.exceptions.RequestException as e:
                print(f"✗ {component:15s}: {filename:40s} (Error: {type(e).__name__})")
                status[component] = False

        print("-" * 60)
        available = sum(status.values())
        total = len(status)
        print(f"Summary: {available}/{total} files available")

        return status
