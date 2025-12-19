"""KITTI dataset loader and utilities."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mobility_datasets.common.base import BaseDataset, DatasetConfig, Sample


class KITTIDataset(BaseDataset):
    """KITTI Vision Benchmark Suite dataset.

    The KITTI dataset is one of the most popular benchmarks for autonomous driving,
    providing stereo images, LiDAR point clouds, and 3D object annotations.

    Reference: http://www.cvlibs.net/datasets/kitti/
    """

    DATASET_INFO = {
        "name": "KITTI",
        "description": "KITTI Vision Benchmark Suite",
        "url": "http://www.cvlibs.net/datasets/kitti/",
        "splits": ["training", "testing"],
        "modalities": ["camera", "lidar", "gps"],
    }

    def __init__(self, config: DatasetConfig) -> None:
        """Initialize KITTI dataset.

        Args:
            config: Dataset configuration.
        """
        super().__init__(config)
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that the configuration is valid for KITTI."""
        if self.config.split not in self.DATASET_INFO["splits"]:
            raise ValueError(
                f"Invalid split '{self.config.split}'. "
                f"Must be one of {self.DATASET_INFO['splits']}"
            )

    def _load_samples(self) -> List[Sample]:
        """Load samples from KITTI dataset.

        Returns:
            List of Sample objects.
        """
        samples: List[Sample] = []

        # Check if dataset exists
        if not self.config.root_dir.exists():
            return samples

        # Look for data files in the root directory
        split_dir = self.config.root_dir / self.config.split
        if not split_dir.exists():
            return samples

        # Load image files (simplified implementation)
        image_dir = split_dir / "image_2"
        if image_dir.exists():
            image_files = sorted(image_dir.glob("*.png"))
            for i, img_file in enumerate(image_files):
                sample_id = img_file.stem
                samples.append(
                    Sample(
                        sample_id=sample_id,
                        timestamp=float(i),  # KITTI doesn't have explicit timestamps
                        sensor_data={"image_path": str(img_file)},
                        metadata={"dataset": "KITTI", "split": self.config.split},
                    )
                )

        return samples

    def download(self, output_dir: Optional[Path] = None) -> None:
        """Download the KITTI dataset.

        Args:
            output_dir: Directory to download the dataset to.
                       If None, uses the root_dir from config.

        Note:
            KITTI dataset requires manual download from the official website.
            This method provides instructions on how to download.
        """
        target_dir = output_dir or self.config.root_dir

        instructions = f"""
KITTI Dataset Download Instructions:
=====================================

The KITTI dataset requires manual download from the official website.

1. Visit: {self.DATASET_INFO['url']}
2. Navigate to the desired benchmark (e.g., Object Detection, Tracking)
3. Download the required data:
   - Left color images
   - Right color images (optional)
   - Velodyne point clouds (optional)
   - Training labels
   - Calibration files

4. Extract all files to: {target_dir}

Expected directory structure:
{target_dir}/
├── training/
│   ├── image_2/
│   ├── image_3/ (optional)
│   ├── velodyne/ (optional)
│   ├── label_2/
│   └── calib/
└── testing/
    ├── image_2/
    └── calib/

For more information, see the KITTI development kit and documentation.
"""
        print(instructions)

    def get_info(self) -> Dict[str, Any]:
        """Get KITTI dataset information.

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
