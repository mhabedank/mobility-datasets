"""Tests for dataset implementations."""

from pathlib import Path

import pytest

from mobility_datasets.common.base import DatasetConfig
from mobility_datasets.kitti.dataset import KITTIDataset
from mobility_datasets.nuscenes.dataset import NuScenesDataset
from mobility_datasets.waymo.dataset import WaymoDataset


class TestKITTIDataset:
    """Test KITTI dataset implementation."""

    def test_init(self, tmp_path: Path) -> None:
        """Test KITTI dataset initialization."""
        config = DatasetConfig(root_dir=tmp_path, split="training")
        dataset = KITTIDataset(config)
        assert dataset.config.root_dir == tmp_path
        assert dataset.config.split == "training"

    def test_invalid_split(self, tmp_path: Path) -> None:
        """Test that invalid split raises error."""
        config = DatasetConfig(root_dir=tmp_path, split="invalid")
        with pytest.raises(ValueError, match="Invalid split"):
            KITTIDataset(config)

    def test_get_info(self, tmp_path: Path) -> None:
        """Test getting dataset information."""
        config = DatasetConfig(root_dir=tmp_path, split="training")
        dataset = KITTIDataset(config)
        info = dataset.get_info()
        assert info["name"] == "KITTI"
        assert info["split"] == "training"
        assert "num_samples" in info

    def test_empty_dataset(self, tmp_path: Path) -> None:
        """Test dataset with no data."""
        config = DatasetConfig(root_dir=tmp_path, split="training")
        dataset = KITTIDataset(config)
        assert len(dataset) == 0

    def test_download(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test download instructions."""
        config = DatasetConfig(root_dir=tmp_path, split="training")
        dataset = KITTIDataset(config)
        dataset.download()
        captured = capsys.readouterr()
        assert "KITTI Dataset Download Instructions" in captured.out


class TestNuScenesDataset:
    """Test nuScenes dataset implementation."""

    def test_init(self, tmp_path: Path) -> None:
        """Test nuScenes dataset initialization."""
        config = DatasetConfig(root_dir=tmp_path, split="train")
        dataset = NuScenesDataset(config)
        assert dataset.config.root_dir == tmp_path
        assert dataset.config.split == "train"

    def test_invalid_split(self, tmp_path: Path) -> None:
        """Test that invalid split raises error."""
        config = DatasetConfig(root_dir=tmp_path, split="invalid")
        with pytest.raises(ValueError, match="Invalid split"):
            NuScenesDataset(config)

    def test_get_info(self, tmp_path: Path) -> None:
        """Test getting dataset information."""
        config = DatasetConfig(root_dir=tmp_path, split="train")
        dataset = NuScenesDataset(config)
        info = dataset.get_info()
        assert info["name"] == "nuScenes"
        assert info["split"] == "train"
        assert "num_samples" in info

    def test_download(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test download instructions."""
        config = DatasetConfig(root_dir=tmp_path, split="train")
        dataset = NuScenesDataset(config)
        dataset.download()
        captured = capsys.readouterr()
        assert "nuScenes Dataset Download Instructions" in captured.out


class TestWaymoDataset:
    """Test Waymo dataset implementation."""

    def test_init(self, tmp_path: Path) -> None:
        """Test Waymo dataset initialization."""
        config = DatasetConfig(root_dir=tmp_path, split="training")
        dataset = WaymoDataset(config)
        assert dataset.config.root_dir == tmp_path
        assert dataset.config.split == "training"

    def test_invalid_split(self, tmp_path: Path) -> None:
        """Test that invalid split raises error."""
        config = DatasetConfig(root_dir=tmp_path, split="invalid")
        with pytest.raises(ValueError, match="Invalid split"):
            WaymoDataset(config)

    def test_get_info(self, tmp_path: Path) -> None:
        """Test getting dataset information."""
        config = DatasetConfig(root_dir=tmp_path, split="training")
        dataset = WaymoDataset(config)
        info = dataset.get_info()
        assert info["name"] == "Waymo Open Dataset"
        assert info["split"] == "training"
        assert "num_samples" in info

    def test_download(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test download instructions."""
        config = DatasetConfig(root_dir=tmp_path, split="training")
        dataset = WaymoDataset(config)
        dataset.download()
        captured = capsys.readouterr()
        assert "Waymo Open Dataset Download Instructions" in captured.out
