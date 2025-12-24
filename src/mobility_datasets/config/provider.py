"""
Config provider for loading and managing dataset configurations.

Module: src/mobility_datasets/config/provider.py
Purpose: Load YAML configs and return typed dataclass objects
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class License:
    """License information."""

    name: str
    url: Optional[str] = None
    details: Optional[str] = None


@dataclass
class Citation:
    """Citation information."""

    bibtex: Optional[str] = None


@dataclass
class Metadata:
    """Dataset metadata."""

    name: str
    description: str
    license: License
    citation: Optional[Citation] = None


@dataclass
class DownloadInfo:
    """Download information for a variant."""

    url: str
    filename: str
    size_bytes: int
    md5: str
    format: str


@dataclass
class Part:
    """Dataset variant (e.g., synced/unsynced)."""

    id: str
    name: str
    download: DownloadInfo


@dataclass
class Session:
    """Recording session."""

    id: str
    name: str
    date: str
    location_type: str
    parts: List[Part]

    def get_part_by_id(self, part_id: str) -> Optional[Part]:
        """Get part by ID."""
        for p in self.parts:
            if p.id == part_id:
                return p
        return None


@dataclass
class Collection:
    """Collection of sessions."""

    id: str
    name: str
    description: str
    sessions: List[Session]

    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        for s in self.sessions:
            if s.id == session_id:
                return s
        return None


@dataclass
class DatasetConfig:
    """Complete dataset configuration."""

    metadata: Metadata
    collections: List[Collection]

    def id_in_collections(self, collection_id: str) -> bool:
        """Check if collection ID exists."""
        return any(c.id == collection_id for c in self.collections)

    def collection_by_id(self, collection_id: str) -> Optional[Collection]:
        """Get collection by ID."""
        for c in self.collections:
            if c.id == collection_id:
                return c
        return None


class ConfigLoader:
    """Load YAML config files and return typed objects."""

    @staticmethod
    def load_yaml(file_path: Path) -> Dict[str, Any]:
        """
        Load YAML file.

        Parameters
        ----------
        file_path : Path
            Path to YAML file

        Returns
        -------
        dict
            Parsed YAML content

        Raises
        ------
        FileNotFoundError
            If file does not exist
        yaml.YAMLError
            If YAML is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {file_path}: {e}") from e

    @staticmethod
    def _dict_to_download_info(data: Dict[str, Any]) -> DownloadInfo:
        """Convert dict to DownloadInfo."""
        return DownloadInfo(
            url=data["url"],
            filename=data["filename"],
            size_bytes=data.get("size_bytes", 0),
            md5=data.get("md5", "unknown"),
            format=data.get("format", "zip"),
        )

    @staticmethod
    def _dict_to_part(data: Dict[str, Any]) -> Part:
        """Convert dict to Part."""
        return Part(
            id=data["id"],
            name=data["name"],
            download=ConfigLoader._dict_to_download_info(data["download"]),
        )

    @staticmethod
    def _dict_to_session(data: Dict[str, Any]) -> Session:
        """Convert dict to Session."""
        return Session(
            id=data["id"],
            name=data["name"],
            date=data["date"],
            location_type=data["location_type"],
            parts=[ConfigLoader._dict_to_part(v) for v in data.get("parts", [])],
        )

    @staticmethod
    def _dict_to_collection(data: Dict[str, Any]) -> Collection:
        """Convert dict to Collection."""
        return Collection(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            sessions=[ConfigLoader._dict_to_session(s) for s in data.get("sessions", [])],
        )

    @staticmethod
    def _dict_to_license(data: Dict[str, Any]) -> License:
        """Convert dict to License."""
        return License(
            name=data["name"],
            url=data.get("url"),
            details=data.get("details"),
        )

    @staticmethod
    def _dict_to_citation(data: Dict[str, Any]) -> Citation:
        """Convert dict to Citation."""
        return Citation(
            bibtex=data.get("bibtex"),
        )

    @staticmethod
    def _dict_to_metadata(data: Dict[str, Any]) -> Metadata:
        """Convert dict to Metadata."""
        return Metadata(
            name=data["name"],
            description=data["description"],
            license=ConfigLoader._dict_to_license(data["license"]),
            citation=(
                ConfigLoader._dict_to_citation(data["citation"]) if "citation" in data else None
            ),
        )

    @staticmethod
    def dict_to_config(data: Dict[str, Any]) -> DatasetConfig:
        """
        Convert dict to DatasetConfig.

        Parameters
        ----------
        data : dict
            Configuration dictionary

        Returns
        -------
        DatasetConfig
            Typed configuration object

        Raises
        ------
        KeyError
            If required fields are missing
        ValueError
            If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data)}")

        return DatasetConfig(
            metadata=ConfigLoader._dict_to_metadata(data["metadata"]),
            collections=[ConfigLoader._dict_to_collection(c) for c in data.get("collections", [])],
        )


class ConfigProvider:
    """
    Provide access to dataset configurations.

    This class loads YAML config files and returns typed DatasetConfig objects.

    Example
    -------
    >>> provider = ConfigProvider()
    >>> kitti_config = provider.get_from_datasource("kitti")
    >>> print(kitti_config.metadata.name)
    The KITTI Vision Benchmark Suite
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config provider.

        Parameters
        ----------
        config_dir : Path, optional
            Directory containing config files.
            Default: src/mobility_datasets/config
        """
        if config_dir is None:
            # Default to config directory relative to this module
            config_dir = Path(__file__).parent

        if not config_dir.exists():
            raise ValueError(f"Config directory does not exist: {config_dir}")

        self.config_dir = config_dir
        self._cache: Dict[str, DatasetConfig] = {}

    def get_from_datasource(self, datasource_name: str) -> DatasetConfig:
        """
        Load and return config for a datasource.

        Parameters
        ----------
        datasource_name : str
            Name of datasource (e.g., "kitti", "nuscenes")

        Returns
        -------
        DatasetConfig
            Configuration object with metadata, collections, sessions

        Raises
        ------
        FileNotFoundError
            If config file does not exist
        yaml.YAMLError
            If YAML is invalid
        KeyError
            If required fields are missing

        Example
        -------
        >>> kitti_config = provider.get_from_datasource("kitti")
        >>> print(kitti_config.metadata.name)
        The KITTI Vision Benchmark Suite
        """
        # Return from cache if available
        if datasource_name in self._cache:
            return self._cache[datasource_name]

        # Load from file
        config_file = self.config_dir / f"{datasource_name}.yaml"

        try:
            raw_config = ConfigLoader.load_yaml(config_file)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Config not found for '{datasource_name}'. " f"Expected: {config_file}"
            ) from None

        # Parse into typed object
        try:
            dataset_config = ConfigLoader.dict_to_config(raw_config)
        except KeyError as e:
            raise KeyError(f"Invalid config structure for '{datasource_name}': {e}") from e

        # Cache and return
        self._cache[datasource_name] = dataset_config
        return dataset_config

    def list_available_datasources(self) -> List[str]:
        """
        List available datasource configs.

        Returns
        -------
        list of str
            Names of available datasources (without .yaml extension)

        Example
        -------
        >>> provider = ConfigProvider()
        >>> provider.list_available_datasources()
        ['kitti', 'nuscenes', 'waymo']
        """
        yaml_files = self.config_dir.glob("*.yaml")
        return sorted([f.stem for f in yaml_files])

    def list_available_collections(self, datasource_name: str) -> List[str]:
        """
        List available collections for a given datasource.

        Parameters
        ----------
        datasource_name : str
            Name of datasource (e.g., "kitti", "nuscenes")

        Returns
        -------
        list of str
            Names of available collections

        Example
        -------
        >>> provider = ConfigProvider()
        >>> provider.list_available_collections("kitti")
        ['raw_data', 'object_tracking']
        """
        config = self.get_from_datasource(datasource_name)
        return [collection.id for collection in config.collections]

    def clear_cache(self) -> None:
        """Clear the config cache."""
        self._cache.clear()
