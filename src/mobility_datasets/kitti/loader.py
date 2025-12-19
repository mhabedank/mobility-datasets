"""Download KITTI tracking dataset from S3."""

import zipfile
from pathlib import Path
from typing import List

import requests
from tqdm import tqdm


class KITTIDownloader:
    """Download KITTI tracking dataset files."""

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
        Download and extract specified components.

        Parameters
        ----------
        components : List[str]
            List of components to download (e.g., ["oxts", "calib"])
        keep_zip : bool
            Keep zip files after extraction (default: False)
        """
        for component in components:
            if component not in self.AVAILABLE_FILES:
                print(f"Unknown component: {component}")
                continue

            self._download_file(component)
            self._unzip_file(component, keep_zip)

    def download_all(self, keep_zip: bool = False):
        """
        Download and extract all available components.

        Parameters
        ----------
        keep_zip : bool
            Keep zip files after extraction (default: False)
        """
        components = list(self.AVAILABLE_FILES.keys())
        print(f"Downloading {len(components)} components...")
        self.download(components, keep_zip)

    def _download_file(self, component: str):
        """Download a single file with progress bar."""
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
        """Unzip a single file."""
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
