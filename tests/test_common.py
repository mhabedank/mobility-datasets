"""Tests for base classes and common utilities."""

import numpy as np
import pytest

from mobility_datasets.common.base import DatasetConfig, Sample
from mobility_datasets.common.coordinates import CoordinateSystem, Transform


class TestDatasetConfig:
    """Test DatasetConfig dataclass."""

    def test_init_with_strings(self) -> None:
        """Test initialization with string paths."""
        config = DatasetConfig(root_dir="/tmp/data", split="train")
        assert config.root_dir.as_posix() == "/tmp/data"
        assert config.split == "train"
        assert config.lazy_load is True

    def test_init_with_path(self) -> None:
        """Test initialization with Path objects."""
        from pathlib import Path

        config = DatasetConfig(root_dir=Path("/tmp/data"))
        assert config.root_dir.as_posix() == "/tmp/data"

    def test_cache_dir(self) -> None:
        """Test cache directory configuration."""
        config = DatasetConfig(root_dir="/tmp/data", cache_dir="/tmp/cache")
        assert config.cache_dir is not None
        assert config.cache_dir.as_posix() == "/tmp/cache"


class TestSample:
    """Test Sample dataclass."""

    def test_init(self) -> None:
        """Test sample initialization."""
        sample = Sample(sample_id="001", timestamp=1234.5)
        assert sample.sample_id == "001"
        assert sample.timestamp == 1234.5
        assert sample.sensor_data == {}
        assert sample.annotations == {}

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        sample = Sample(
            sample_id="001",
            timestamp=1234.5,
            sensor_data={"camera": "image.png"},
            annotations={"bbox": [0, 0, 10, 10]},
        )
        sample_dict = sample.to_dict()
        assert sample_dict["sample_id"] == "001"
        assert sample_dict["timestamp"] == 1234.5
        assert sample_dict["sensor_data"]["camera"] == "image.png"


class TestCoordinateSystem:
    """Test CoordinateSystem enum."""

    def test_coordinate_systems(self) -> None:
        """Test that all coordinate systems are defined."""
        assert CoordinateSystem.CAMERA.value == "camera"
        assert CoordinateSystem.LIDAR.value == "lidar"
        assert CoordinateSystem.VEHICLE.value == "vehicle"
        assert CoordinateSystem.WORLD.value == "world"


class TestTransform:
    """Test Transform class."""

    def test_identity_transform(self) -> None:
        """Test identity transformation."""
        transform = Transform()
        assert np.allclose(transform.rotation, np.eye(3))
        assert np.allclose(transform.translation, np.zeros(3))

    def test_from_matrix(self) -> None:
        """Test creating transform from 4x4 matrix."""
        matrix = np.eye(4)
        matrix[:3, 3] = [1, 2, 3]
        transform = Transform.from_matrix(matrix)
        assert np.allclose(transform.translation, [1, 2, 3])

    def test_to_matrix(self) -> None:
        """Test converting transform to 4x4 matrix."""
        transform = Transform(translation=np.array([1, 2, 3]))
        matrix = transform.to_matrix()
        assert matrix.shape == (4, 4)
        assert np.allclose(matrix[:3, 3], [1, 2, 3])

    def test_transform_points(self) -> None:
        """Test transforming 3D points."""
        # Translation only
        transform = Transform(translation=np.array([1, 0, 0]))
        points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        transformed = transform.transform_points(points)
        expected = np.array([[1, 0, 0], [2, 0, 0], [1, 1, 0]])
        assert np.allclose(transformed, expected)

    def test_inverse(self) -> None:
        """Test inverse transformation."""
        transform = Transform(translation=np.array([1, 2, 3]))
        inv_transform = transform.inverse()
        assert np.allclose(inv_transform.translation, [-1, -2, -3])

        # Check that applying transform and inverse gives identity
        points = np.array([[1, 2, 3]])
        transformed = transform.transform_points(points)
        back = inv_transform.transform_points(transformed)
        assert np.allclose(back, points)

    def test_compose(self) -> None:
        """Test composing two transforms."""
        t1 = Transform(translation=np.array([1, 0, 0]))
        t2 = Transform(translation=np.array([0, 1, 0]))
        composed = t1.compose(t2)
        assert np.allclose(composed.translation, [1, 1, 0])

    def test_from_euler(self) -> None:
        """Test creating transform from Euler angles."""
        transform = Transform.from_euler((0, 0, np.pi / 2), degrees=False)
        # Rotation around z-axis by 90 degrees
        point = np.array([1, 0, 0])
        rotated = transform.transform_points(point)
        assert np.allclose(rotated, [0, 1, 0], atol=1e-10)

    def test_invalid_rotation_shape(self) -> None:
        """Test that invalid rotation shape raises error."""
        with pytest.raises(ValueError, match="Rotation must be 3x3"):
            Transform(rotation=np.eye(2))

    def test_invalid_translation_shape(self) -> None:
        """Test that invalid translation shape raises error."""
        with pytest.raises(ValueError, match="Translation must be 3D"):
            Transform(translation=np.array([1, 2]))
