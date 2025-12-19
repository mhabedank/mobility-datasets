"""Base classes for dataset implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import pandas as pd


@dataclass
class DatasetConfig:
    """Configuration for a dataset.

    Attributes:
        root_dir: Root directory of the dataset.
        split: Dataset split (e.g., 'train', 'val', 'test').
        lazy_load: Whether to use lazy loading for data.
        cache_dir: Optional directory for caching processed data.
    """

    root_dir: Path
    split: str = "train"
    lazy_load: bool = True
    cache_dir: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Convert root_dir and cache_dir to Path objects if they're strings."""
        if isinstance(self.root_dir, str):
            self.root_dir = Path(self.root_dir)
        if self.cache_dir is not None and isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir)


@dataclass
class Sample:
    """A single sample from a dataset.

    Attributes:
        sample_id: Unique identifier for the sample.
        timestamp: Timestamp of the sample.
        sensor_data: Dictionary containing sensor data (images, lidar, etc.).
        annotations: Dictionary containing annotations (bounding boxes, etc.).
        metadata: Additional metadata for the sample.
    """

    sample_id: str
    timestamp: float
    sensor_data: Dict[str, Any] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert sample to dictionary representation."""
        return {
            "sample_id": self.sample_id,
            "timestamp": self.timestamp,
            "sensor_data": self.sensor_data,
            "annotations": self.annotations,
            "metadata": self.metadata,
        }


class BaseDataset(ABC):
    """Abstract base class for all datasets.

    This class defines the interface that all dataset implementations must follow.
    It provides methods for loading data, accessing samples, and converting to
    different formats (pandas DataFrame, typed dataclasses).
    """

    def __init__(self, config: DatasetConfig) -> None:
        """Initialize the dataset.

        Args:
            config: Dataset configuration.
        """
        self.config = config
        self._samples: Optional[List[Sample]] = None
        self._df: Optional[pd.DataFrame] = None

    @abstractmethod
    def _load_samples(self) -> List[Sample]:
        """Load all samples from the dataset.

        This method should be implemented by subclasses to load samples
        according to the specific dataset format.

        Returns:
            List of Sample objects.
        """
        pass

    @property
    def samples(self) -> List[Sample]:
        """Get all samples from the dataset.

        Uses lazy loading if enabled in config.

        Returns:
            List of Sample objects.
        """
        if self._samples is None:
            self._samples = self._load_samples()
        return self._samples

    def __len__(self) -> int:
        """Get the number of samples in the dataset.

        Returns:
            Number of samples.
        """
        return len(self.samples)

    def __getitem__(self, idx: Union[int, str]) -> Sample:
        """Get a sample by index or ID.

        Args:
            idx: Sample index (int) or sample ID (str).

        Returns:
            Sample object.

        Raises:
            IndexError: If index is out of range.
            KeyError: If sample ID is not found.
        """
        if isinstance(idx, int):
            return self.samples[idx]
        else:
            # Find sample by ID
            for sample in self.samples:
                if sample.sample_id == idx:
                    return sample
            raise KeyError(f"Sample with ID '{idx}' not found")

    def __iter__(self) -> Iterator[Sample]:
        """Iterate over samples in the dataset.

        Returns:
            Iterator over Sample objects.
        """
        return iter(self.samples)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert dataset to pandas DataFrame.

        Returns:
            DataFrame containing all samples and their data.
        """
        if self._df is None:
            records = [sample.to_dict() for sample in self.samples]
            self._df = pd.DataFrame(records)
        return self._df

    @abstractmethod
    def download(self, output_dir: Optional[Path] = None) -> None:
        """Download the dataset.

        Args:
            output_dir: Directory to download the dataset to.
                       If None, uses the root_dir from config.
        """
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get dataset information.

        Returns:
            Dictionary containing dataset metadata and statistics.
        """
        pass
