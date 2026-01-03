"""
Config provider for loading and managing dataset configurations.

Module: src/mobility_datasets/config/provider.py
Purpose: Load YAML configs and return typed dataclass objects
"""

from pathlib import Path
from typing import List, Optional, Union

import yaml
from pydantic import BaseModel, Field


class License(BaseModel):
    """License information."""

    name: str
    url: Optional[str] = None
    details: Optional[str] = None


class Citation(BaseModel):
    """Citation information."""

    bibtex: Optional[str] = None


class Metadata(BaseModel):
    """Dataset metadata."""

    name: str
    description: str
    license: License
    citation: Optional[Citation] = None


class DownloadInfo(BaseModel):
    """Download information for a part."""

    url: str
    filename: str
    size_bytes: int = 0
    md5: str = "unknown"
    format: str = "zip"


class Part(BaseModel):
    """Dataset part (e.g., synced_rectified, calib)."""

    id: str
    name: str
    download: DownloadInfo
    optional: bool = False


class Session(BaseModel):
    """Recording session."""

    id: str
    name: str
    date: str
    parts: List[Part] = Field(default_factory=list)

    def part_ids(self) -> List[str]:
        """Get list of part IDs.

        Returns
        -------
        List[str]
            Part IDs
        """
        return [p.id for p in self.parts]

    def has_part(self, part_id: str) -> bool:
        """Check if part with given ID exists.

        Parameters
        ----------
        part_id : str
            Part ID to check

        Returns
        -------
        bool
            True if part exists, False otherwise
        """
        return any(p.id == part_id for p in self.parts)

    def get_part_by_id(self, part_id: str) -> Optional[Part]:
        """Get part by ID.

        Parameters
        ----------
        part_id : str
            Part ID to search for

        Returns
        -------
        Optional[Part]
            Part if found, None otherwise
        """
        for p in self.parts:
            if p.id == part_id:
                return p
        return None

    def get_part_or_raise(self, part_id: str) -> Part:
        """Get part by ID or raise error if not found.

        Parameters
        ----------
        part_id : str
            Part ID to search for
        Returns
        -------
        Part
            Part if found
        Raises
        ------
        ValueError
            If part with given ID is not found
        """
        part = self.get_part_by_id(part_id)
        if part is None:
            raise ValueError(f"Part with ID '{part_id}' not found in session '{self.id}'")
        return part


class Collection(BaseModel):
    """Collection of sessions."""

    id: str
    name: str
    description: str
    sessions: List[Session] = Field(default_factory=list)

    def session_ids(self) -> List[str]:
        """Get list of session IDs.

        Returns
        -------
        List[str]
            Session IDs
        """
        return [s.id for s in self.sessions]

    def has_session(self, session_id: str) -> bool:
        """Check if session with given ID exists.

        Parameters
        ----------
        session_id : str
            Session ID to check
        Returns
        -------
        bool
            True if session exists, False otherwise
        """
        return any(s.id == session_id for s in self.sessions)

    def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID.

        Parameters
        ----------
        session_id : str
            Session ID to search for

        Returns
        -------
        Optional[Session]
            Session if found, None otherwise
        """
        for s in self.sessions:
            if s.id == session_id:
                return s
        return None

    def get_session_or_raise(self, session_id: str) -> Session:
        """Get session by ID or raise error if not found.

        Parameters
        ----------
        session_id : str
            Session ID to search for
        Returns
        -------
        Session
            Session if found
        Raises
        ------
        ValueError
            If session with given ID is not found
        """
        session = self.get_session_by_id(session_id)
        if session is None:
            raise ValueError(f"Session with ID '{session_id}' not found in collection '{self.id}'")
        return session


class DatasetConfig(BaseModel):
    """Complete dataset configuration."""

    metadata: Metadata
    collections: List[Collection] = Field(default_factory=list)

    def collection_ids(self) -> List[str]:
        """Get list of collection IDs.

        Returns
        -------
        List[str]
            Collection IDs
        """
        return [c.id for c in self.collections]

    def has_collection(self, collection_id: str) -> bool:
        """Check if collection with given ID exists.

        Parameters
        ----------
        collection_id : str
            Collection ID to check
        Returns
        -------
        bool
            True if collection exists, False otherwise
        """
        return any(c.id == collection_id for c in self.collections)

    def get_collection_by_id(self, collection_id: str) -> Optional[Collection]:
        """Get collection by ID.

        Parameters
        ----------
        collection_id : str
            Collection ID to search for

        Returns
        -------
        Optional[Collection]
            Collection if found, None otherwise
        """
        for c in self.collections:
            if c.id == collection_id:
                return c
        return None

    def get_collection_or_raise(self, collection_id: str) -> Collection:
        """Get collection by ID or raise error if not found.

        Parameters
        ----------
        collection_id : str
            Collection ID to search for
        Returns
        -------
        Collection
            Collection if found
        Raises
        ------
        ValueError
            If collection with given ID is not found
        """
        collection = self.get_collection_by_id(collection_id)
        if collection is None:
            raise ValueError(f"Collection with ID '{collection_id}' not found")
        return collection


class ConfigProvider:
    """
    Provide access to dataset configurations.

    This class loads YAML config files and returns typed DatasetConfig objects.

    Parameters
    ----------
    config_dir : Path, optional
        Directory containing config files.
        Default: src/mobility_datasets/config

    Attributes
    ----------
    config_dir : Path
        Path to configuration directory

    Examples
    --------
    Load KITTI config:

    >>> provider = ConfigProvider()
    >>> kitti_config = provider.get_from_datasource("kitti")
    >>> print(kitti_config.metadata.name)
    The KITTI Vision Benchmark Suite
    """

    def __init__(self, config_dir: Optional[Union[Path, str]] = None):
        """
        Initialize config provider.

        Parameters
        ----------
        config_dir : Path or str, optional
            Directory containing config files.
            Default: src/mobility_datasets/config
        """
        if config_dir is None:
            # Default to config directory relative to this module
            config_dir = Path(__file__).parent
        else:
            config_dir = Path(config_dir)

        if not config_dir.exists():
            raise ValueError(f"Config directory does not exist: {config_dir}")

        self.config_dir = config_dir

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
        ValueError
            If config structure is invalid (Pydantic validation error)

        Examples
        --------
        >>> provider = ConfigProvider()
        >>> kitti_config = provider.get_from_datasource("kitti")
        >>> print(kitti_config.metadata.name)
        The KITTI Vision Benchmark Suite
        """
        config_file = self.config_dir / f"{datasource_name}.yaml"

        try:
            with open(config_file, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Config not found for '{datasource_name}'. " f"Expected: {config_file}"
            ) from None

        try:
            return DatasetConfig(**raw_config)
        except Exception as e:
            raise ValueError(f"Invalid config structure for " f"'{datasource_name}': {e}") from e

    def list_datasources(self) -> List[str]:
        """
        List available datasource configs.

        Returns
        -------
        List[str]
            Names of available datasources (without .yaml extension)

        Examples
        --------
        >>> provider = ConfigProvider()
        >>> provider.list_datasources()
        ['kitti', 'nuscenes', 'waymo']
        """
        yaml_files = self.config_dir.glob("*.yaml")
        return sorted([f.stem for f in yaml_files])
