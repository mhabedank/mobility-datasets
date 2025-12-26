"""
Unit tests for config.provider - Dataclasses and ConfigLoader.

Location: tests/unit/config/test_provider.py

Focus:
- Dataclass instantiation and basic functionality
- ConfigLoader static methods (dict conversion)
- ConfigLoader YAML parsing
- Error cases and validation
"""

import pytest
import yaml
from mobility_datasets.config.provider import (
    Citation,
    Collection,
    ConfigLoader,
    DatasetConfig,
    DownloadInfo,
    License,
    Metadata,
    Part,
    Session,
)

# ============================================================================
# Dataclass Tests: License
# ============================================================================


class TestLicense:
    """Test License dataclass."""

    def test_license_creation_minimal(self):
        """Create License with required fields only."""
        license_obj = License(name="MIT")
        assert license_obj.name == "MIT"
        assert license_obj.url is None
        assert license_obj.details is None

    def test_license_creation_full(self):
        """Create License with all fields."""
        license_obj = License(
            name="CC BY-NC-SA 3.0",
            url="https://creativecommons.org/licenses/by-nc-sa/3.0/",
            details="Non-commercial use only",
        )
        assert license_obj.name == "CC BY-NC-SA 3.0"
        assert license_obj.url == "https://creativecommons.org/licenses/by-nc-sa/3.0/"
        assert license_obj.details == "Non-commercial use only"


# ============================================================================
# Dataclass Tests: Citation
# ============================================================================


class TestCitation:
    """Test Citation dataclass."""

    def test_citation_creation_empty(self):
        """Create Citation with no BibTeX."""
        citation = Citation()
        assert citation.bibtex is None

    def test_citation_creation_with_bibtex(self):
        """Create Citation with BibTeX."""
        bibtex = "@article{Geiger2013IJRR,author={...}}"
        citation = Citation(bibtex=bibtex)
        assert citation.bibtex == bibtex


# ============================================================================
# Dataclass Tests: Metadata
# ============================================================================


class TestMetadata:
    """Test Metadata dataclass."""

    def test_metadata_creation_without_citation(self):
        """Create Metadata without citation."""
        license_obj = License(name="MIT")
        metadata = Metadata(name="KITTI", description="A dataset", license=license_obj)
        assert metadata.name == "KITTI"
        assert metadata.citation is None

    def test_metadata_creation_with_citation(self):
        """Create Metadata with citation."""
        license_obj = License(name="MIT")
        citation = Citation(bibtex="@article{...}")
        metadata = Metadata(
            name="KITTI", description="A dataset", license=license_obj, citation=citation
        )
        assert metadata.citation.bibtex == "@article{...}"


# ============================================================================
# Dataclass Tests: DownloadInfo
# ============================================================================


class TestDownloadInfo:
    """Test DownloadInfo dataclass."""

    def test_download_info_creation(self):
        """Create DownloadInfo with all fields."""
        info = DownloadInfo(
            url="https://example.com/file.zip",
            filename="file.zip",
            size_bytes=1000000,
            md5="abc123",
            format="zip",
        )
        assert info.url == "https://example.com/file.zip"
        assert info.filename == "file.zip"
        assert info.size_bytes == 1000000
        assert info.md5 == "abc123"
        assert info.format == "zip"


# ============================================================================
# Dataclass Tests: Part
# ============================================================================


class TestPart:
    """Test Part dataclass."""

    def test_part_creation(self):
        """Create Part."""
        download_info = DownloadInfo(
            url="https://example.com/file.zip",
            filename="file.zip",
            size_bytes=1000000,
            md5="abc123",
            format="zip",
        )
        part = Part(id="synced_rectified", name="Synced + Rectified", download=download_info)
        assert part.id == "synced_rectified"
        assert part.name == "Synced + Rectified"
        assert part.download.filename == "file.zip"


# ============================================================================
# Dataclass Tests: Session
# ============================================================================


class TestSession:
    """Test Session dataclass and methods."""

    def test_session_creation_empty_parts(self):
        """Create Session with no parts."""
        session = Session(
            id="2011_09_26_drive_0001",
            name="2011_09_26_drive_0001",
            date="2011-09-26",
            location_type="City",
            parts=[],
        )
        assert session.id == "2011_09_26_drive_0001"
        assert len(session.parts) == 0

    def test_session_creation_with_parts(self):
        """Create Session with multiple parts."""
        download_info = DownloadInfo(
            url="https://example.com/file.zip",
            filename="file.zip",
            size_bytes=1000,
            md5="abc123",
            format="zip",
        )
        part1 = Part(id="part1", name="Part 1", download=download_info)
        part2 = Part(id="part2", name="Part 2", download=download_info)

        session = Session(
            id="session1",
            name="Session 1",
            date="2011-09-26",
            location_type="City",
            parts=[part1, part2],
        )
        assert len(session.parts) == 2

    def test_get_part_by_id_found(self):
        """Get part by ID when it exists."""
        download_info = DownloadInfo(
            url="https://example.com/file.zip",
            filename="file.zip",
            size_bytes=1000,
            md5="abc123",
            format="zip",
        )
        part = Part(id="synced", name="Synced", download=download_info)
        session = Session(
            id="session1", name="Session 1", date="2011-09-26", location_type="City", parts=[part]
        )

        found = session.get_part_by_id("synced")
        assert found is not None
        assert found.id == "synced"

    def test_get_part_by_id_not_found(self):
        """Get part by ID when it doesn't exist."""
        session = Session(
            id="session1", name="Session 1", date="2011-09-26", location_type="City", parts=[]
        )

        found = session.get_part_by_id("nonexistent")
        assert found is None


# ============================================================================
# Dataclass Tests: Collection
# ============================================================================


class TestCollection:
    """Test Collection dataclass and methods."""

    def test_collection_creation_empty_sessions(self):
        """Create Collection with no sessions."""
        collection = Collection(
            id="raw_data", name="Raw Data", description="Raw sensor data", sessions=[]
        )
        assert collection.id == "raw_data"
        assert len(collection.sessions) == 0

    def test_get_session_by_id_found(self):
        """Get session by ID when it exists."""
        session = Session(
            id="2011_09_26_drive_0001",
            name="2011_09_26_drive_0001",
            date="2011-09-26",
            location_type="City",
            parts=[],
        )
        collection = Collection(
            id="raw_data", name="Raw Data", description="Raw sensor data", sessions=[session]
        )

        found = collection.get_session_by_id("2011_09_26_drive_0001")
        assert found is not None
        assert found.id == "2011_09_26_drive_0001"

    def test_get_session_by_id_not_found(self):
        """Get session by ID when it doesn't exist."""
        collection = Collection(
            id="raw_data", name="Raw Data", description="Raw sensor data", sessions=[]
        )

        found = collection.get_session_by_id("nonexistent")
        assert found is None


# ============================================================================
# Dataclass Tests: DatasetConfig
# ============================================================================


class TestDatasetConfig:
    """Test DatasetConfig dataclass and methods."""

    def test_dataset_config_creation(self):
        """Create DatasetConfig."""
        license_obj = License(name="MIT")
        metadata = Metadata(name="KITTI", description="A dataset", license=license_obj)
        config = DatasetConfig(metadata=metadata, collections=[])

        assert config.metadata.name == "KITTI"
        assert len(config.collections) == 0

    def test_collection_by_id_found(self):
        """Get collection by ID when it exists."""
        license_obj = License(name="MIT")
        metadata = Metadata(name="KITTI", description="A dataset", license=license_obj)
        collection = Collection(
            id="raw_data", name="Raw Data", description="Raw sensor data", sessions=[]
        )
        config = DatasetConfig(metadata=metadata, collections=[collection])

        found = config.collection_by_id("raw_data")
        assert found is not None
        assert found.id == "raw_data"

    def test_collection_by_id_not_found(self):
        """Get collection by ID when it doesn't exist."""
        license_obj = License(name="MIT")
        metadata = Metadata(name="KITTI", description="A dataset", license=license_obj)
        config = DatasetConfig(metadata=metadata, collections=[])

        found = config.collection_by_id("nonexistent")
        assert found is None

    def test_id_in_collections_exists(self):
        """Check if collection ID exists."""
        license_obj = License(name="MIT")
        metadata = Metadata(name="KITTI", description="A dataset", license=license_obj)
        collection = Collection(
            id="raw_data", name="Raw Data", description="Raw sensor data", sessions=[]
        )
        config = DatasetConfig(metadata=metadata, collections=[collection])

        assert config.id_in_collections("raw_data") is True

    def test_id_in_collections_not_exists(self):
        """Check if collection ID doesn't exist."""
        license_obj = License(name="MIT")
        metadata = Metadata(name="KITTI", description="A dataset", license=license_obj)
        config = DatasetConfig(metadata=metadata, collections=[])

        assert config.id_in_collections("nonexistent") is False


# ============================================================================
# ConfigLoader Tests: Dict Conversion
# ============================================================================


class TestConfigLoaderDictConversion:
    """Test ConfigLoader static methods for dict → dataclass conversion."""

    def test_dict_to_download_info_minimal(self):
        """Convert minimal dict to DownloadInfo."""
        data = {"url": "https://example.com/file.zip", "filename": "file.zip"}
        info = ConfigLoader._dict_to_download_info(data)

        assert info.url == "https://example.com/file.zip"
        assert info.filename == "file.zip"
        assert info.size_bytes == 0
        assert info.md5 == "unknown"
        assert info.format == "zip"

    def test_dict_to_download_info_full(self):
        """Convert full dict to DownloadInfo."""
        data = {
            "url": "https://example.com/file.zip",
            "filename": "file.zip",
            "size_bytes": 1000000,
            "md5": "abc123def456",
            "format": "zip",
        }
        info = ConfigLoader._dict_to_download_info(data)

        assert info.size_bytes == 1000000
        assert info.md5 == "abc123def456"

    def test_dict_to_license(self):
        """Convert dict to License."""
        data = {
            "name": "CC BY-NC-SA 3.0",
            "url": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
        }
        license_obj = ConfigLoader._dict_to_license(data)

        assert license_obj.name == "CC BY-NC-SA 3.0"
        assert license_obj.url == "https://creativecommons.org/licenses/by-nc-sa/3.0/"

    def test_dict_to_citation(self):
        """Convert dict to Citation."""
        data = {"bibtex": "@article{...}"}
        citation = ConfigLoader._dict_to_citation(data)

        assert citation.bibtex == "@article{...}"

    def test_dict_to_metadata(self):
        """Convert dict to Metadata."""
        data = {
            "name": "KITTI",
            "description": "A dataset",
            "license": {
                "name": "CC BY-NC-SA 3.0",
                "url": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
            },
            "citation": {"bibtex": "@article{Geiger2013IJRR,...}"},
        }
        metadata = ConfigLoader._dict_to_metadata(data)

        assert metadata.name == "KITTI"
        assert metadata.license.name == "CC BY-NC-SA 3.0"
        assert metadata.citation.bibtex == "@article{Geiger2013IJRR,...}"

    def test_dict_to_part(self):
        """Convert dict to Part."""
        data = {
            "id": "synced_rectified",
            "name": "Synced + Rectified",
            "download": {
                "url": "https://example.com/file.zip",
                "filename": "file.zip",
                "size_bytes": 1000000,
                "md5": "abc123",
                "format": "zip",
            },
        }
        part = ConfigLoader._dict_to_part(data)

        assert part.id == "synced_rectified"
        assert part.download.filename == "file.zip"

    def test_dict_to_session(self):
        """Convert dict to Session."""
        data = {
            "id": "2011_09_26_drive_0001",
            "name": "2011_09_26_drive_0001",
            "date": "2011-09-26",
            "location_type": "City",
            "parts": [
                {
                    "id": "synced",
                    "name": "Synced",
                    "download": {
                        "url": "https://example.com/file.zip",
                        "filename": "file.zip",
                        "size_bytes": 1000,
                        "md5": "abc123",
                        "format": "zip",
                    },
                }
            ],
        }
        session = ConfigLoader._dict_to_session(data)

        assert session.id == "2011_09_26_drive_0001"
        assert len(session.parts) == 1
        assert session.parts[0].id == "synced"

    def test_dict_to_collection(self):
        """Convert dict to Collection."""
        data = {
            "id": "raw_data",
            "name": "Raw Data",
            "description": "Raw sensor data",
            "sessions": [
                {
                    "id": "2011_09_26_drive_0001",
                    "name": "2011_09_26_drive_0001",
                    "date": "2011-09-26",
                    "location_type": "City",
                    "parts": [],
                }
            ],
        }
        collection = ConfigLoader._dict_to_collection(data)

        assert collection.id == "raw_data"
        assert len(collection.sessions) == 1

    def test_dict_to_config(self):
        """Convert dict to DatasetConfig."""
        data = {
            "metadata": {"name": "KITTI", "description": "A dataset", "license": {"name": "MIT"}},
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw Data",
                    "description": "Raw sensor data",
                    "sessions": [],
                }
            ],
        }
        config = ConfigLoader.dict_to_config(data)

        assert config.metadata.name == "KITTI"
        assert len(config.collections) == 1

    def test_dict_to_config_not_dict(self):
        """dict_to_config raises ValueError for non-dict input."""
        with pytest.raises(ValueError, match="Expected dict"):
            ConfigLoader.dict_to_config("not a dict")


# ============================================================================
# ConfigLoader Tests: YAML Loading
# ============================================================================


class TestConfigLoaderYaml:
    """Test ConfigLoader.load_yaml() method."""

    def test_load_yaml_success(self, tmp_path):
        """Load valid YAML file successfully."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nnested:\n  item: 123")

        result = ConfigLoader.load_yaml(yaml_file)

        assert result["key"] == "value"
        assert result["nested"]["item"] == 123

    def test_load_yaml_file_not_found(self, tmp_path):
        """load_yaml raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            ConfigLoader.load_yaml(tmp_path / "nonexistent.yaml")

    def test_load_yaml_invalid_yaml(self, tmp_path):
        """load_yaml raises YAMLError for invalid YAML syntax."""
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text("invalid: : yaml: : syntax:")

        with pytest.raises(yaml.YAMLError, match="Invalid YAML"):
            ConfigLoader.load_yaml(yaml_file)

    def test_load_yaml_empty_file(self, tmp_path):
        """load_yaml returns empty dict for empty YAML file."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        result = ConfigLoader.load_yaml(yaml_file)

        assert result == {}
