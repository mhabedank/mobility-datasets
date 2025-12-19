"""nuScenes dataset loader and utilities."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mobility_datasets.common.base import BaseDataset, DatasetConfig, Sample


class NuScenesDataset(BaseDataset):
    """nuScenes autonomous driving dataset.

    nuScenes is a large-scale dataset for autonomous driving with full sensor suite
    including cameras, LiDAR, radar, and IMU. It provides rich 3D annotations.

    Reference: https://www.nuscenes.org/
    """

    DATASET_INFO = {
        "name": "nuScenes",
        "description": "nuScenes autonomous driving dataset",
        "url": "https://www.nuscenes.org/",
        "splits": ["train", "val", "test", "mini"],
        "modalities": ["camera", "lidar", "radar", "can_bus"],
    }

    def __init__(self, config: DatasetConfig) -> None:
        """Initialize nuScenes dataset.

        Args:
            config: Dataset configuration.
        """
        super().__init__(config)
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that the configuration is valid for nuScenes."""
        if self.config.split not in self.DATASET_INFO["splits"]:
            raise ValueError(
                f"Invalid split '{self.config.split}'. "
                f"Must be one of {self.DATASET_INFO['splits']}"
            )

    def _load_samples(self) -> List[Sample]:
        """Load samples from nuScenes dataset.

        Returns:
            List of Sample objects.
        """
        samples: List[Sample] = []

        # Check if dataset exists
        if not self.config.root_dir.exists():
            return samples

        # Look for version directory
        version = f"v1.0-{self.config.split}"
        version_dir = self.config.root_dir / version
        if not version_dir.exists():
            return samples

        # In a real implementation, this would parse the JSON metadata files
        # For now, we create a basic structure
        samples_dir = self.config.root_dir / "samples"
        if samples_dir.exists():
            # Look for sample data
            camera_dirs = list(samples_dir.glob("CAM_*"))
            if camera_dirs:
                image_files = sorted(camera_dirs[0].glob("*.jpg"))
                for i, img_file in enumerate(image_files):
                    sample_id = img_file.stem
                    samples.append(
                        Sample(
                            sample_id=sample_id,
                            timestamp=float(i) * 0.5,  # nuScenes typically 2Hz
                            sensor_data={"image_path": str(img_file)},
                            metadata={"dataset": "nuScenes", "split": self.config.split},
                        )
                    )

        return samples

    def download(self, output_dir: Optional[Path] = None) -> None:
        """Download the nuScenes dataset.

        Args:
            output_dir: Directory to download the dataset to.
                       If None, uses the root_dir from config.

        Note:
            nuScenes dataset requires registration and manual download.
            This method provides instructions on how to download.
        """
        target_dir = output_dir or self.config.root_dir

        instructions = f"""
nuScenes Dataset Download Instructions:
========================================

The nuScenes dataset requires registration and manual download.

1. Visit: {self.DATASET_INFO['url']}
2. Create an account or log in
3. Navigate to the Download section
4. Download the required files:
   - Full dataset (v1.0): ~350 GB
   - Mini dataset (v1.0-mini): ~4 GB (recommended for testing)
   - Trainval metadata
   - Test metadata (optional)

5. Extract all files to: {target_dir}

Expected directory structure:
{target_dir}/
├── samples/
│   ├── CAM_BACK/
│   ├── CAM_BACK_LEFT/
│   ├── CAM_BACK_RIGHT/
│   ├── CAM_FRONT/
│   ├── CAM_FRONT_LEFT/
│   ├── CAM_FRONT_RIGHT/
│   ├── LIDAR_TOP/
│   └── RADAR_*/
├── sweeps/
├── v1.0-trainval/
├── v1.0-test/ (optional)
└── maps/

For more information, see the nuScenes devkit and documentation.
"""
        print(instructions)

    def get_info(self) -> Dict[str, Any]:
        """Get nuScenes dataset information.

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
