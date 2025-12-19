"""Coordinate system transformations and utilities."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import numpy as np
from scipy.spatial.transform import Rotation


class CoordinateSystem(Enum):
    """Supported coordinate systems for autonomous driving datasets."""

    CAMERA = "camera"  # Camera coordinate system (x: right, y: down, z: forward)
    LIDAR = "lidar"  # LiDAR coordinate system (x: forward, y: left, z: up)
    VEHICLE = "vehicle"  # Vehicle coordinate system (x: forward, y: left, z: up)
    WORLD = "world"  # World/global coordinate system


@dataclass
class Transform:
    """Represents a spatial transformation (rotation + translation).

    Attributes:
        rotation: 3x3 rotation matrix or None for identity.
        translation: 3D translation vector or None for zero translation.
        from_coord: Source coordinate system.
        to_coord: Target coordinate system.
    """

    rotation: Optional[np.ndarray] = None
    translation: Optional[np.ndarray] = None
    from_coord: Optional[CoordinateSystem] = None
    to_coord: Optional[CoordinateSystem] = None

    def __post_init__(self) -> None:
        """Validate and initialize transformation matrices."""
        if self.rotation is None:
            self.rotation = np.eye(3)
        else:
            self.rotation = np.asarray(self.rotation)
            if self.rotation.shape != (3, 3):
                raise ValueError(f"Rotation must be 3x3, got {self.rotation.shape}")

        if self.translation is None:
            self.translation = np.zeros(3)
        else:
            self.translation = np.asarray(self.translation)
            if self.translation.shape != (3,):
                raise ValueError(f"Translation must be 3D, got {self.translation.shape}")

    @classmethod
    def from_matrix(cls, matrix: np.ndarray) -> "Transform":
        """Create transform from a 4x4 homogeneous transformation matrix.

        Args:
            matrix: 4x4 transformation matrix.

        Returns:
            Transform object.

        Raises:
            ValueError: If matrix shape is not 4x4.
        """
        matrix = np.asarray(matrix)
        if matrix.shape != (4, 4):
            raise ValueError(f"Matrix must be 4x4, got {matrix.shape}")

        rotation = matrix[:3, :3]
        translation = matrix[:3, 3]

        return cls(rotation=rotation, translation=translation)

    def to_matrix(self) -> np.ndarray:
        """Convert transform to a 4x4 homogeneous transformation matrix.

        Returns:
            4x4 transformation matrix.
        """
        matrix = np.eye(4)
        matrix[:3, :3] = self.rotation
        matrix[:3, 3] = self.translation
        return matrix

    def transform_points(self, points: np.ndarray) -> np.ndarray:
        """Transform a set of 3D points.

        Args:
            points: Array of 3D points with shape (N, 3) or (3, N).

        Returns:
            Transformed points with the same shape as input.

        Raises:
            ValueError: If points shape is invalid.
        """
        points = np.asarray(points)

        # Handle both (N, 3) and (3, N) formats
        if len(points.shape) == 1 and points.shape[0] == 3:
            # Single point (3,) format
            assert self.rotation is not None
            assert self.translation is not None
            transformed = self.rotation @ points + self.translation
        elif len(points.shape) == 2 and points.shape[1] == 3:
            # (N, 3) format - most common format
            assert self.rotation is not None
            assert self.translation is not None
            transformed = (self.rotation @ points.T).T + self.translation
        elif len(points.shape) == 2 and points.shape[0] == 3:
            # (3, N) format
            assert self.rotation is not None
            assert self.translation is not None
            transformed = self.rotation @ points + self.translation[:, np.newaxis]
        else:
            raise ValueError(f"Points must have shape (N, 3), (3, N), or (3,), got {points.shape}")

        return transformed

    def inverse(self) -> "Transform":
        """Compute the inverse transformation.

        Returns:
            Inverse Transform object.
        """
        assert self.rotation is not None
        assert self.translation is not None
        inv_rotation = self.rotation.T
        inv_translation = -inv_rotation @ self.translation

        return Transform(
            rotation=inv_rotation,
            translation=inv_translation,
            from_coord=self.to_coord,
            to_coord=self.from_coord,
        )

    def compose(self, other: "Transform") -> "Transform":
        """Compose this transform with another (self applied first).

        Args:
            other: Transform to compose with.

        Returns:
            Composed Transform object.
        """
        assert self.rotation is not None
        assert self.translation is not None
        assert other.rotation is not None
        assert other.translation is not None
        composed_rotation = other.rotation @ self.rotation
        composed_translation = other.rotation @ self.translation + other.translation

        return Transform(
            rotation=composed_rotation,
            translation=composed_translation,
            from_coord=self.from_coord,
            to_coord=other.to_coord,
        )

    @classmethod
    def from_euler(
        cls,
        angles: Tuple[float, float, float],
        sequence: str = "xyz",
        degrees: bool = False,
        translation: Optional[np.ndarray] = None,
    ) -> "Transform":
        """Create transform from Euler angles.

        Args:
            angles: Euler angles as (x, y, z) tuple.
            sequence: Rotation sequence (e.g., 'xyz', 'zyx').
            degrees: Whether angles are in degrees (default: radians).
            translation: Optional translation vector.

        Returns:
            Transform object.
        """
        rotation = Rotation.from_euler(sequence, angles, degrees=degrees).as_matrix()
        return cls(rotation=rotation, translation=translation)

    def to_euler(self, sequence: str = "xyz", degrees: bool = False) -> Tuple[float, float, float]:
        """Convert rotation to Euler angles.

        Args:
            sequence: Rotation sequence (e.g., 'xyz', 'zyx').
            degrees: Whether to return angles in degrees (default: radians).

        Returns:
            Euler angles as (x, y, z) tuple.
        """
        rot = Rotation.from_matrix(self.rotation)
        angles = rot.as_euler(sequence, degrees=degrees)
        return tuple(angles)
