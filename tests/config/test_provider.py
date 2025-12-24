"""
Test suite for ConfigProvider.

Module: tests/config/test_provider.py
Purpose: Load YAML configs and return typed dataclass objects

Test organization follows the test pyramid:
- Unit tests (25%): Fast, mock-heavy, individual methods
- Integration tests (35%): Real files, no network, component interaction
- E2E tests (40%): Complete workflows, no mocks
"""

import pytest
import yaml
from mobility_datasets.config.provider import (
    ConfigLoader,
    ConfigProvider,
    DatasetConfig,
    DownloadInfo,
)

# =============================================================================
# Fixtures (shared across all test layers)
# =============================================================================


@pytest.fixture
def config_dir(tmp_path):
    """
    Create temporary config directory for testing.

    Scope: function
    Purpose: Isolated test environment for each test
    """
    config_path = tmp_path / "config"
    config_path.mkdir()
    return config_path


@pytest.fixture
def minimal_kitti_config_dict():
    """
    Minimal valid KITTI config (required fields only).

    Used across unit, integration, and E2E tests.
    """
    return {
        "metadata": {
            "name": "KITTI Vision Benchmark",
            "description": "A dataset for autonomous driving research",
            "license": {
                "name": "CC BY-NC-SA 3.0",
                "url": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
            },
        },
        "collections": [],
    }


@pytest.fixture
def full_kitti_config_dict():
    """
    Complete KITTI config with all optional fields.

    Used for testing nested structure handling.
    """
    return {
        "metadata": {
            "name": "KITTI Vision Benchmark Suite",
            "description": "A dataset for autonomous driving research",
            "license": {
                "name": "CC BY-NC-SA 3.0",
                "url": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
                "details": "Non-commercial use only",
            },
            "citation": {"bibtex": "@article{Geiger2013IJRR,...}"},
        },
        "collections": [
            {
                "id": "raw_data",
                "name": "Raw Data",
                "description": "Raw sensor data from vehicles",
                "sessions": [
                    {
                        "id": "2011_09_26_drive_0001",
                        "name": "2011_09_26_drive_0001",
                        "date": "2011-09-26",
                        "location_type": "City",
                        "parts": [
                            {
                                "id": "unsynced",
                                "name": "Unsynced + Unrectified",
                                "download": {
                                    "url": "https://s3.example.com/kitti.zip",
                                    "filename": "kitti.zip",
                                    "size_bytes": 1000000,
                                    "md5": "abc123def456",
                                    "format": "zip",
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }


@pytest.fixture
def kitti_yaml_file(config_dir, full_kitti_config_dict):
    """
    Create kitti.yaml file in config directory.

    Scope: function
    Purpose: Real file I/O for integration tests
    """
    yaml_file = config_dir / "kitti.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(full_kitti_config_dict, f)
    return yaml_file


# =============================================================================
# UNIT TESTS: License (Layer 1 - Base)
# =============================================================================


class TestConfigLoaderLicenseUnit:
    """
    Unit tests for License dataclass conversion.

    Purpose: Verify individual field handling in isolation
    Speed: < 100ms per test
    Mocking: All external dependencies mocked
    """

    def test_license_required_fields_only(self):
        """
        Test: License with only required 'name' field.

        Purpose: Verify minimal valid config doesn't fail
        If fails: Required fields handling is broken
        """
        data = {"name": "MIT"}
        license_obj = ConfigLoader._dict_to_license(data)

        assert license_obj.name == "MIT"
        assert license_obj.url is None
        assert license_obj.details is None

    def test_license_all_fields_populated(self):
        """
        Test: License with all optional fields.

        Purpose: Verify all fields are correctly assigned
        If fails: Optional field handling broken
        """
        data = {
            "name": "CC BY-NC-SA 3.0",
            "url": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
            "details": "Non-commercial use only",
        }
        license_obj = ConfigLoader._dict_to_license(data)

        assert license_obj.name == "CC BY-NC-SA 3.0"
        assert license_obj.url == "https://creativecommons.org/licenses/by-nc-sa/3.0/"
        assert license_obj.details == "Non-commercial use only"

    def test_license_missing_required_name_raises_keyerror(self):
        """
        Test: Missing required 'name' field raises KeyError.

        Purpose: Prevent silent failures from incomplete data
        If fails: Validation is not catching invalid configs
        """
        data = {"url": "https://example.com"}

        with pytest.raises(KeyError, match="name"):
            ConfigLoader._dict_to_license(data)


# =============================================================================
# UNIT TESTS: Citation (Layer 1 - Base)
# =============================================================================


class TestConfigLoaderCitationUnit:
    """Unit tests for Citation dataclass conversion."""

    def test_citation_with_bibtex_content(self):
        """Test Citation is correctly populated with BibTeX."""
        bibtex = "@article{Example2020,...}"
        data = {"bibtex": bibtex}
        citation = ConfigLoader._dict_to_citation(data)

        assert citation.bibtex == bibtex

    def test_citation_missing_bibtex_defaults_to_none(self):
        """Test Citation with missing BibTeX defaults to None."""
        citation = ConfigLoader._dict_to_citation({})

        assert citation.bibtex is None


# =============================================================================
# UNIT TESTS: Metadata (Layer 1 - Base)
# =============================================================================


class TestConfigLoaderMetadataUnit:
    """Unit tests for Metadata dataclass conversion."""

    def test_metadata_required_fields_only(self):
        """Test Metadata with only required fields."""
        data = {"name": "KITTI", "description": "A dataset", "license": {"name": "CC BY-NC-SA 3.0"}}
        metadata = ConfigLoader._dict_to_metadata(data)

        assert metadata.name == "KITTI"
        assert metadata.description == "A dataset"
        assert metadata.license.name == "CC BY-NC-SA 3.0"
        assert metadata.citation is None

    def test_metadata_with_optional_citation(self):
        """Test Metadata correctly includes optional citation."""
        data = {
            "name": "KITTI",
            "description": "A dataset",
            "license": {"name": "CC BY-NC-SA 3.0"},
            "citation": {"bibtex": "@article{...}"},
        }
        metadata = ConfigLoader._dict_to_metadata(data)

        assert metadata.citation is not None
        assert metadata.citation.bibtex == "@article{...}"

    def test_metadata_missing_name_raises_keyerror(self):
        """Test that missing name raises KeyError."""
        data = {"description": "A dataset", "license": {"name": "CC BY-NC-SA 3.0"}}

        with pytest.raises(KeyError):
            ConfigLoader._dict_to_metadata(data)


# =============================================================================
# UNIT TESTS: DownloadInfo (Layer 1 - Base)
# =============================================================================


class TestConfigLoaderDownloadInfoUnit:
    """Unit tests for DownloadInfo dataclass conversion."""

    def test_download_all_fields_present(self):
        """Test DownloadInfo with all fields specified."""
        data = {
            "url": "https://example.com/file.zip",
            "filename": "file.zip",
            "size_bytes": 1000000,
            "md5": "abc123",
            "format": "zip",
        }
        download = ConfigLoader._dict_to_download_info(data)

        assert download.url == "https://example.com/file.zip"
        assert download.size_bytes == 1000000
        assert download.md5 == "abc123"

    def test_download_optional_fields_use_defaults(self):
        """Test DownloadInfo uses sensible defaults for optional fields."""
        data = {"url": "https://example.com/file.zip", "filename": "file.zip"}
        download = ConfigLoader._dict_to_download_info(data)

        assert download.size_bytes == 0
        assert download.md5 == "unknown"
        assert download.format == "zip"

    def test_download_missing_url_raises_keyerror(self):
        """Test that missing URL raises KeyError."""
        data = {"filename": "file.zip"}

        with pytest.raises(KeyError):
            ConfigLoader._dict_to_download_info(data)


# =============================================================================
# UNIT TESTS: Variant (Layer 1 - Base)
# =============================================================================


class TestConfigLoaderVariantUnit:
    """Unit tests for Variant dataclass conversion."""

    def test_variant_creates_nested_download_info(self):
        """Test Variant correctly creates nested DownloadInfo."""
        data = {
            "id": "synced",
            "name": "Synced Data",
            "download": {"url": "https://example.com/file.zip", "filename": "file.zip"},
        }
        variant = ConfigLoader._dict_to_part(data)

        assert variant.id == "synced"
        assert isinstance(variant.download, DownloadInfo)
        assert variant.download.url == "https://example.com/file.zip"


# =============================================================================
# UNIT TESTS: Session (Layer 1 - Base)
# =============================================================================


class TestConfigLoaderSessionUnit:
    """Unit tests for Session dataclass conversion."""

    def test_session_without_variants_creates_empty_list(self):
        """Test Session without variants defaults to empty list."""
        data = {
            "id": "2011_09_26_drive_0001",
            "name": "Drive 0001",
            "date": "2011-09-26",
            "location_type": "City",
        }
        session = ConfigLoader._dict_to_session(data)

        assert session.parts == []

    def test_session_with_multiple_parts(self):
        """Test Session correctly handles multiple parts."""
        data = {
            "id": "session1",
            "name": "Session 1",
            "date": "2011-09-26",
            "location_type": "City",
            "parts": [
                {"id": "v1", "name": "Variant 1", "download": {"url": "url1", "filename": "f1"}},
                {"id": "v2", "name": "Variant 2", "download": {"url": "url2", "filename": "f2"}},
            ],
        }
        session = ConfigLoader._dict_to_session(data)

        assert len(session.parts) == 2
        assert session.parts[0].id == "v1"
        assert session.parts[1].id == "v2"


# =============================================================================
# UNIT TESTS: Collection (Layer 1 - Base)
# =============================================================================


class TestConfigLoaderCollectionUnit:
    """Unit tests for Collection dataclass conversion."""

    def test_collection_without_sessions_creates_empty_list(self):
        """Test Collection without sessions defaults to empty list."""
        data = {"id": "raw_data", "name": "Raw Data", "description": "Raw sensor data"}
        collection = ConfigLoader._dict_to_collection(data)

        assert collection.sessions == []


# =============================================================================
# UNIT TESTS: Full Config (Layer 1 - Base)
# =============================================================================


class TestConfigLoaderFullConfigUnit:
    """Unit tests for complete config dict conversion."""

    def test_dict_to_config_rejects_non_dict_input(self):
        """Test that non-dict input raises ValueError."""
        with pytest.raises(ValueError, match="Expected dict"):
            ConfigLoader.dict_to_config("not a dict")

    def test_dict_to_config_missing_metadata_raises_keyerror(self):
        """Test that missing metadata raises KeyError."""
        data = {"collections": []}

        with pytest.raises(KeyError):
            ConfigLoader.dict_to_config(data)

    def test_dict_to_config_minimal_structure(self, minimal_kitti_config_dict):
        """Test config conversion with minimal required fields."""
        config = ConfigLoader.dict_to_config(minimal_kitti_config_dict)

        assert isinstance(config, DatasetConfig)
        assert config.metadata.name == "KITTI Vision Benchmark"
        assert config.collections == []


# =============================================================================
# INTEGRATION TESTS: YAML File Loading (Layer 2 - Middle)
# =============================================================================


class TestConfigLoaderYAMLIntegration:
    """
    Integration tests for YAML file loading.

    Purpose: Test file I/O and YAML parsing with real files
    Speed: < 5s per test
    Mocking: No mocking (real files)
    """

    def test_load_valid_yaml_file(self, kitti_yaml_file):
        """
        Test: Load valid YAML file and parse to dict.

        Purpose: Verify YAML parsing works end-to-end
        If fails: YAML parsing or file I/O broken
        """
        data = ConfigLoader.load_yaml(kitti_yaml_file)

        assert isinstance(data, dict)
        assert "metadata" in data
        assert data["metadata"]["name"] == "KITTI Vision Benchmark Suite"

    def test_load_nonexistent_file_raises_filenotfounderror(self, config_dir):
        """
        Test: Non-existent file raises FileNotFoundError.

        Purpose: Catch missing config files early with clear error
        If fails: Silent failures on missing configs
        """
        nonexistent = config_dir / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError, match="Config file not found"):
            ConfigLoader.load_yaml(nonexistent)

    def test_load_invalid_yaml_raises_yamlerror(self, config_dir):
        """
        Test: Invalid YAML syntax raises YAMLError.

        Purpose: Catch malformed YAML early
        If fails: Silent parsing failures
        """
        bad_yaml = config_dir / "bad.yaml"
        bad_yaml.write_text("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            ConfigLoader.load_yaml(bad_yaml)

    def test_load_empty_file_returns_empty_dict(self, config_dir):
        """Test: Empty YAML file returns empty dict."""
        empty_file = config_dir / "empty.yaml"
        empty_file.write_text("")

        data = ConfigLoader.load_yaml(empty_file)
        assert data == {}


# =============================================================================
# INTEGRATION TESTS: ConfigProvider Initialization (Layer 2 - Middle)
# =============================================================================


class TestConfigProviderInitIntegration:
    """Integration tests for ConfigProvider initialization."""

    def test_init_with_valid_directory(self, config_dir):
        """Test ConfigProvider initializes with valid config directory."""
        provider = ConfigProvider(config_dir=config_dir)

        assert provider.config_dir == config_dir
        assert provider._cache == {}

    def test_init_with_nonexistent_directory_raises_error(self, tmp_path):
        """Test that non-existent config directory raises ValueError."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(ValueError, match="Config directory does not exist"):
            ConfigProvider(config_dir=nonexistent)


# =============================================================================
# INTEGRATION TESTS: Loading Configs (Layer 2 - Middle)
# =============================================================================


class TestConfigProviderGetFromDatasourceIntegration:
    """
    Integration tests for loading configs from files.

    Purpose: Test complete load → parse → cache workflow
    Speed: < 5s per test
    Mocking: No mocking (real files)
    """

    def test_load_valid_datasource_config(self, config_dir, kitti_yaml_file):
        """
        Test: Load valid datasource config file.

        Purpose: Verify end-to-end load from file → typed object
        If fails: File loading or parsing broken
        """
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("kitti")

        assert isinstance(config, DatasetConfig)
        assert config.metadata.name == "KITTI Vision Benchmark Suite"

    def test_load_caches_result_for_reuse(self, config_dir, kitti_yaml_file):
        """
        Test: Config is cached after first load.

        Purpose: Avoid redundant file I/O on repeated requests
        If fails: Performance regression (unnecessary file reads)
        """
        provider = ConfigProvider(config_dir=config_dir)

        config1 = provider.get_from_datasource("kitti")
        config2 = provider.get_from_datasource("kitti")

        assert config1 is config2  # Same cached object
        assert "kitti" in provider._cache

    def test_load_nonexistent_datasource_raises_error(self, config_dir):
        """
        Test: Non-existent datasource raises FileNotFoundError.

        Purpose: Catch missing configs early
        If fails: Silent failures on missing datasources
        """
        provider = ConfigProvider(config_dir=config_dir)

        with pytest.raises(FileNotFoundError, match="Config not found for 'nonexistent'"):
            provider.get_from_datasource("nonexistent")

    def test_load_invalid_config_raises_error(self, config_dir):
        """
        Test: Invalid config structure raises KeyError.

        Purpose: Catch malformed configs with clear error message
        If fails: Silent failures on incomplete configs
        """
        invalid_file = config_dir / "invalid.yaml"
        invalid_file.write_text("some: data\nwithout: metadata")

        provider = ConfigProvider(config_dir=config_dir)

        with pytest.raises(KeyError, match="Invalid config structure"):
            provider.get_from_datasource("invalid")


# =============================================================================
# INTEGRATION TESTS: Listing Datasources (Layer 2 - Middle)
# =============================================================================


class TestConfigProviderListAvailableIntegration:
    """Integration tests for discovering available datasources."""

    def test_list_multiple_available_datasources(self, config_dir):
        """
        Test: List multiple available datasource configs.

        Purpose: Verify discovery of multiple datasources
        If fails: File enumeration broken
        """
        # Create multiple config files
        (config_dir / "kitti.yaml").write_text(
            "metadata:\n  name: KITTI\n  description: test\n  license:\n    name: test"
        )
        (config_dir / "nuscenes.yaml").write_text(
            "metadata:\n  name: nuScenes\n  description: test\n  license:\n    name: test"
        )
        (config_dir / "waymo.yaml").write_text(
            "metadata:\n  name: Waymo\n  description: test\n  license:\n    name: test"
        )

        provider = ConfigProvider(config_dir=config_dir)
        available = provider.list_available_datasources()

        assert available == ["kitti", "nuscenes", "waymo"]

    def test_list_empty_directory_returns_empty_list(self, config_dir):
        """Test listing from empty directory returns empty list."""
        provider = ConfigProvider(config_dir=config_dir)
        available = provider.list_available_datasources()

        assert available == []

    def test_list_ignores_non_yaml_files(self, config_dir):
        """
        Test: Non-YAML files are ignored in discovery.

        Purpose: Avoid errors from non-config files in config dir
        If fails: Invalid files cause discovery errors
        """
        (config_dir / "kitti.yaml").write_text(
            "metadata:\n  name: KITTI\n  description: test\n  license:\n    name: test"
        )
        (config_dir / "readme.txt").write_text("This is not a config")

        provider = ConfigProvider(config_dir=config_dir)
        available = provider.list_available_datasources()

        assert available == ["kitti"]
        assert "readme" not in available


# =============================================================================
# INTEGRATION TESTS: Cache Management (Layer 2 - Middle)
# =============================================================================


class TestConfigProviderCacheManagementIntegration:
    """Integration tests for cache behavior."""

    def test_clear_cache_removes_cached_configs(self, config_dir, kitti_yaml_file):
        """Test that clear_cache removes all cached configs."""
        provider = ConfigProvider(config_dir=config_dir)

        provider.get_from_datasource("kitti")
        assert len(provider._cache) == 1

        provider.clear_cache()
        assert len(provider._cache) == 0

    def test_cache_allows_reloading_after_clear(self, config_dir, kitti_yaml_file):
        """Test that cache can be repopulated after clear."""
        provider = ConfigProvider(config_dir=config_dir)

        config1 = provider.get_from_datasource("kitti")
        provider.clear_cache()
        config2 = provider.get_from_datasource("kitti")

        assert config1 is not config2  # Different objects after cache clear


# =============================================================================
# E2E TESTS: Complete Workflows (Layer 3 - Top)
# =============================================================================


class TestConfigProviderE2EWorkflows:
    """
    End-to-end tests for complete user workflows.

    Purpose: Test realistic user scenarios without mocking
    Speed: < 30s per test
    Mocking: None
    """

    def test_user_loads_config_and_accesses_nested_data(self, config_dir, full_kitti_config_dict):
        """
        Test: User loads config file and accesses deeply nested data.

        Scenario: User wants to access download URL for a specific variant
        Steps:
            1. Load kitti config via provider
            2. Navigate to specific collection
            3. Navigate to specific session
            4. Navigate to specific variant
            5. Access download info
        """
        # Setup: Create config file
        yaml_file = config_dir / "kitti.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(full_kitti_config_dict, f)

        # Workflow: Load and access
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("kitti")

        # Verify complete navigation path
        assert config.metadata.name == "KITTI Vision Benchmark Suite"
        assert config.metadata.license.name == "CC BY-NC-SA 3.0"
        assert config.metadata.citation.bibtex == "@article{Geiger2013IJRR,...}"

        # Navigate to variant and access download info
        part = config.collections[0].sessions[0].parts[0]
        assert part.download.md5 == "abc123def456"
        assert part.download.url == "https://s3.example.com/kitti.zip"

    def test_user_loads_multiple_datasources(self, config_dir, full_kitti_config_dict):
        """
        Test: User loads and compares multiple datasources.

        Scenario: User wants to work with both KITTI and nuScenes
        """
        # Setup: Create multiple config files
        (config_dir / "kitti.yaml").write_text(yaml.dump(full_kitti_config_dict))

        nuscenes_config = {
            "metadata": {
                "name": "nuScenes",
                "description": "Multimodal dataset",
                "license": {"name": "CC BY-NC 4.0"},
            },
            "collections": [],
        }
        (config_dir / "nuscenes.yaml").write_text(yaml.dump(nuscenes_config))

        # Workflow: Load both
        provider = ConfigProvider(config_dir=config_dir)
        kitti = provider.get_from_datasource("kitti")
        nuscenes = provider.get_from_datasource("nuscenes")

        # Verify both loaded correctly
        assert kitti.metadata.name == "KITTI Vision Benchmark Suite"
        assert nuscenes.metadata.name == "nuScenes"
        assert kitti.metadata.license.name != nuscenes.metadata.license.name

    def test_user_discovers_and_loads_all_available_datasets(
        self, config_dir, full_kitti_config_dict
    ):
        """
        Test: User discovers available datasets and loads all of them.

        Scenario: User wants to see all available datasets and load each one
        """
        # Setup: Create multiple configs
        (config_dir / "kitti.yaml").write_text(yaml.dump(full_kitti_config_dict))

        minimal_config = {
            "metadata": {
                "name": "Minimal Dataset",
                "description": "Test dataset",
                "license": {"name": "MIT"},
            },
            "collections": [],
        }
        (config_dir / "test.yaml").write_text(yaml.dump(minimal_config))

        # Workflow: Discover and load
        provider = ConfigProvider(config_dir=config_dir)
        available = provider.list_available_datasources()

        # Load each one
        configs = {}
        for name in available:
            configs[name] = provider.get_from_datasource(name)

        # Verify
        assert len(configs) == 2
        assert "kitti" in configs
        assert "test" in configs
        assert all(isinstance(c, DatasetConfig) for c in configs.values())
