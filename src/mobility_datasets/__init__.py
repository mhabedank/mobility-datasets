"""
Mobility Datasets: A Python package for autonomous driving datasets.

This package provides a unified interface for working with popular autonomous
driving datasets including KITTI, nuScenes, and Waymo Open Dataset.
"""

__version__ = "0.1.0"

from mobility_datasets.common.base import BaseDataset, DatasetConfig, Sample
from mobility_datasets.common.coordinates import CoordinateSystem, Transform

__all__ = [
    "BaseDataset",
    "DatasetConfig",
    "Sample",
    "CoordinateSystem",
    "Transform",
]
