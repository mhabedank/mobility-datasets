"""Waymo Open Dataset loader and utilities."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mobility_datasets.common.base import BaseDataset, DatasetConfig, Sample


class WaymoDataset(BaseDataset):
    """Waymo Open Dataset for autonomous driving.

    The Waymo Open Dataset is one of the largest and most diverse autonomous driving
    datasets, featuring data collected from Waymo's self-driving vehicles.

    Reference: https://waymo.com/open/
    """

    DATASET_INFO = {
        "name": "Waymo Open Dataset",
        "description": "Waymo Open Dataset for autonomous driving",
        "url": "https://waymo.com/open/",
        "splits": ["training", "validation", "testing"],
        "modalities": ["camera", "lidar"],
    }

    def __init__(self, config: DatasetConfig) -> None:
        """Initialize Waymo dataset.

        Args:
            config: Dataset configuration.
        """
        super().__init__(config)
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that the configuration is valid for Waymo."""
        if self.config.split not in self.DATASET_INFO["splits"]:
            raise ValueError(
                f"Invalid split '{self.config.split}'. "
                f"Must be one of {self.DATASET_INFO['splits']}"
            )

    def _load_samples(self) -> List[Sample]:
        """Load samples from Waymo Open Dataset.

        Returns:
            List of Sample objects.
        """
        samples: List[Sample] = []

        # Check if dataset exists
        if not self.config.root_dir.exists():
            return samples

        # Look for TFRecord files
        split_dir = self.config.root_dir / self.config.split
        if not split_dir.exists():
            return samples

        # Waymo uses TFRecord format - simplified loading
        tfrecord_files = list(split_dir.glob("*.tfrecord"))
        for i, tfrecord_file in enumerate(tfrecord_files):
            sample_id = tfrecord_file.stem
            samples.append(
                Sample(
                    sample_id=sample_id,
                    timestamp=float(i) * 0.1,  # Waymo typically 10Hz
                    sensor_data={"tfrecord_path": str(tfrecord_file)},
                    metadata={"dataset": "Waymo", "split": self.config.split},
                )
            )

        return samples

    def download(self, output_dir: Optional[Path] = None) -> None:
        """Download the Waymo Open Dataset.

        Args:
            output_dir: Directory to download the dataset to.
                       If None, uses the root_dir from config.

        Note:
            Waymo dataset requires Google Cloud authentication and can be downloaded
            using gsutil or the Waymo Open Dataset API.
        """
        target_dir = output_dir or self.config.root_dir

        instructions = f"""
Waymo Open Dataset Download Instructions:
==========================================

The Waymo Open Dataset is hosted on Google Cloud Storage.

Option 1: Using gsutil (recommended)
-------------------------------------
1. Install Google Cloud SDK: https://cloud.google.com/sdk/install
2. Authenticate: gcloud auth login
3. Download using gsutil:

   # Download perception dataset
   gsutil -m cp -r \\
     "gs://waymo_open_dataset_v_1_4_0/individual_files/training/*.tfrecord" \\
     {target_dir}/training/

   gsutil -m cp -r \\
     "gs://waymo_open_dataset_v_1_4_0/individual_files/validation/*.tfrecord" \\
     {target_dir}/validation/

Option 2: Using the Waymo Open Dataset API
-------------------------------------------
1. Visit: {self.DATASET_INFO['url']}
2. Sign up and agree to the terms
3. Access the download page
4. Use the provided download scripts

Expected directory structure:
{target_dir}/
├── training/
│   ├── segment-*.tfrecord
│   └── ...
├── validation/
│   └── segment-*.tfrecord
└── testing/
    └── segment-*.tfrecord

For more information, see the Waymo Open Dataset documentation.
"""
        print(instructions)

    def get_info(self) -> Dict[str, Any]:
        """Get Waymo dataset information.

        Returns:
            Dictionary containing dataset metadata and statistics.
        """
        info = {
            **self.DATASET_INFO,
            "num_samples": len(self),
            "split": self.config.split,
            "root_dir": str(self.config.root_dir),
        }
        return info
