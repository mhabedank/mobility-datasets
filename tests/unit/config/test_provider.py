"""
Unit Tests für ConfigProvider - überarbeitete Version.

Anpassungen:
1. API-Methoden renamed: *_by_id() statt get_*_by_id()
2. Neue *_ids() Methoden testen (List aller IDs)
3. Konsistent mit neuem Pattern: _by_id(), has_*(), get_*_or_raise()
4. ConfigProvider.list_available_collections() -> DatasetConfig.collection_ids()
5. Bessere Test-Struktur nach Test Strategy Guideline
"""

from pathlib import Path

import pytest
import yaml
from mobility_datasets.config.provider import ConfigProvider, DatasetConfig

# =============================================================================
# UNIT TESTS: ConfigProvider Initialization
# =============================================================================


class TestConfigProviderInitUnit:
    """Test: ConfigProvider Initialisierung."""

    def test_init_accepts_custom_config_dir(self, tmp_path):
        """
        Test: __init__ akzeptiert custom config_dir Parameter.

        Purpose: ConfigProvider kann auf custom Directories zeigen.
        """
        # Setup: Echtes temp directory
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Execution
        provider = ConfigProvider(config_dir=config_dir)

        # Verifizierung
        assert provider.config_dir == config_dir

    def test_init_uses_default_config_dir(self):
        """
        Test: Falls kein config_dir gegeben, wird default verwendet.

        Purpose: Default Directory existiert und ist korrekt.
        If fails: Default config directory is misconfigured.
        """
        # Execution (ohne Parameter)
        provider = ConfigProvider()

        # Verifizierung: Default sollte auf src/mobility_datasets/config zeigen
        assert provider.config_dir.exists()
        assert provider.config_dir.name == "config"

    def test_init_rejects_nonexistent_directory(self, tmp_path):
        """
        Test: __init__ schlägt fehl wenn config_dir nicht existiert.

        Purpose: Früher Error wenn Konfiguration fehlerhaft ist.
        If fails: ConfigProvider doesn't validate directory existence.
        """
        # Setup: Verzeichnis existiert nicht
        nonexistent_dir = tmp_path / "nonexistent" / "path"

        # Execution & Verifizierung
        with pytest.raises(ValueError, match="Config directory does not exist"):
            ConfigProvider(config_dir=nonexistent_dir)

    def test_init_converts_string_to_path(self, tmp_path):
        """
        Test: __init__ konvertiert string zu Path.

        Purpose: Benutzer kann strings oder Paths übergeben.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_dir_str = str(config_dir)

        # Execution
        provider = ConfigProvider(config_dir=config_dir_str)

        # Verifizierung: sollte Path sein
        assert isinstance(provider.config_dir, Path)
        assert provider.config_dir == config_dir


# =============================================================================
# UNIT TESTS: list_datasources
# =============================================================================


class TestListDatasourcesUnit:
    """Test: list_datasources() Methode."""

    def test_list_datasources_finds_yaml_files(self, tmp_path):
        """
        Test: Findet alle *.yaml Dateien im config_dir.

        Purpose: Automatische Erkennung neuer Datasources.
        If fails: YAML discovery is broken.
        """
        # Setup: Erstelle fake YAML Dateien
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "kitti.yaml").touch()
        (config_dir / "nuscenes.yaml").touch()
        (config_dir / "waymo.yaml").touch()

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        result = provider.list_datasources()

        # Verifizierung
        assert set(result) == {"kitti", "nuscenes", "waymo"}

    def test_list_datasources_ignores_non_yaml_files(self, tmp_path):
        """
        Test: Ignoriert Dateien die nicht *.yaml sind.

        Purpose: Keine Fehler wenn andere Dateien im config_dir sind.
        """
        # Setup: Mix aus YAML und anderen Dateien
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "kitti.yaml").touch()
        (config_dir / "README.md").touch()
        (config_dir / "nuscenes.yaml").touch()
        (config_dir / ".gitkeep").touch()

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        result = provider.list_datasources()

        # Verifizierung
        assert set(result) == {"kitti", "nuscenes"}
        assert "README" not in result

    def test_list_datasources_empty_if_none(self, tmp_path):
        """
        Test: Gibt leere List zurück wenn keine YAML Dateien.

        Purpose: Keine Exception, sondern sauberes Handling.
        """
        # Setup: Leeres Verzeichnis
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        result = provider.list_datasources()

        # Verifizierung
        assert result == []

    @pytest.mark.parametrize("datasource_count", [1, 5, 10])
    def test_list_datasources_scales(self, tmp_path, datasource_count):
        """
        Test: Funktioniert auch mit vielen Datasources.

        Purpose: Keine Performance-Probleme später.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        for i in range(datasource_count):
            (config_dir / f"dataset_{i:02d}.yaml").touch()

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        result = provider.list_datasources()

        # Verifizierung
        assert len(result) == datasource_count


# =============================================================================
# UNIT TESTS: get_from_datasource
# =============================================================================


class TestGetFromDatasourceUnit:
    """Test: get_from_datasource() Methode."""

    def test_get_loads_yaml_file(self, tmp_path):
        """
        Test: Lädt und parst YAML Datei korrekt.

        Purpose: ConfigProvider kann echte YAML lesen.
        If fails: YAML loading is broken.
        """
        # Setup: Echte YAML Datei
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_yaml = {
            "metadata": {
                "name": "Test Dataset",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_yaml, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")

        # Verifizierung
        assert isinstance(config, DatasetConfig)
        assert config.metadata.name == "Test Dataset"

    def test_get_raises_if_datasource_not_found(self, tmp_path):
        """
        Test: Fehler wenn Datasource nicht existiert.

        Purpose: Klare Error Messages für User.
        If fails: Missing datasources don't raise proper error.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Execution & Verifizierung
        provider = ConfigProvider(config_dir=config_dir)
        with pytest.raises(FileNotFoundError, match="unknown"):
            provider.get_from_datasource("unknown")

    def test_get_handles_malformed_yaml(self, tmp_path):
        """
        Test: Fehler bei ungültiger YAML Syntax.

        Purpose: Aussagekräftige Error Messages.
        """
        # Setup: Ungültige YAML
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        with open(config_dir / "bad.yaml", "w") as f:
            f.write("invalid: [yaml: {syntax")

        # Execution & Verifizierung
        provider = ConfigProvider(config_dir=config_dir)
        with pytest.raises((yaml.YAMLError, ValueError)):
            provider.get_from_datasource("bad")

    def test_get_validates_config_structure(self, tmp_path):
        """
        Test: Validiert dass YAML die richtige Struktur hat.

        Purpose: Ungültige Configs werden erkannt.
        If fails: Invalid configs are not caught.
        """
        # Setup: YAML mit falscher Struktur (fehlt description und license)
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        bad_structure = {"metadata": {"name": "test"}, "collections": []}

        with open(config_dir / "bad_structure.yaml", "w") as f:
            yaml.dump(bad_structure, f)

        # Execution & Verifizierung
        provider = ConfigProvider(config_dir=config_dir)
        with pytest.raises(ValueError, match="Invalid config structure"):
            provider.get_from_datasource("bad_structure")


# =============================================================================
# UNIT TESTS: DatasetConfig.collection_ids()
# =============================================================================


class TestDatasetConfigCollectionIdsUnit:
    """Test: DatasetConfig.collection_ids() Methode."""

    def test_collection_ids_returns_all_ids(self, tmp_path):
        """
        Test: Gibt alle Collection IDs für ein Dataset.

        Purpose: Use Case 1 - User entdeckt verfügbare Collections.
        If fails: Collection discovery is broken.
        """
        # Setup: YAML mit Collections
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [],
                },
                {
                    "id": "synced",
                    "name": "Synced",
                    "description": "Synced",
                    "sessions": [],
                },
                {
                    "id": "tracking",
                    "name": "Tracking",
                    "description": "Tracking",
                    "sessions": [],
                },
            ],
        }

        with open(config_dir / "kitti.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("kitti")
        result = config.collection_ids()

        # Verifizierung
        assert result == ["raw_data", "synced", "tracking"]

    def test_collection_ids_empty_if_none(self, tmp_path):
        """
        Test: Gibt leere List wenn keine Collections.

        Purpose: Graceful Handling.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Empty",
                "description": "Empty",
                "license": {"name": "MIT"},
            },
            "collections": [],
        }

        with open(config_dir / "empty.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("empty")
        result = config.collection_ids()

        # Verifizierung
        assert result == []

    @pytest.mark.parametrize("collection_count", [1, 5, 10])
    def test_collection_ids_scales(self, tmp_path, collection_count):
        """
        Test: Funktioniert auch mit vielen Collections.

        Purpose: Keine Performance-Probleme später.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        collections = [
            {
                "id": f"collection_{i:02d}",
                "name": f"Collection {i}",
                "description": f"Desc {i}",
                "sessions": [],
            }
            for i in range(collection_count)
        ]

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": collections,
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        result = config.collection_ids()

        # Verifizierung
        assert len(result) == collection_count


# =============================================================================
# UNIT TESTS: DatasetConfig.collection_by_id()
# =============================================================================


class TestDatasetConfigCollectionByIdUnit:
    """Test: DatasetConfig.collection_by_id() Methode."""

    def test_collection_by_id_finds_collection(self, tmp_path):
        """
        Test: Findet Collection nach ID.

        Purpose: Validierung von User Input.
        If fails: Collection lookup fails.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [],
                },
                {
                    "id": "synced",
                    "name": "Synced",
                    "description": "Synced",
                    "sessions": [],
                },
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        collection = config.get_collection_by_id("raw_data")

        # Verifizierung
        assert collection is not None
        assert collection.id == "raw_data"

    def test_collection_by_id_returns_none_if_not_found(self, tmp_path):
        """
        Test: Gibt None zurück wenn Collection nicht existiert.

        Purpose: Graceful Error Handling.
        If fails: Missing collections don't return None.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [],
                },
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        result = config.get_collection_by_id("unknown")

        # Verifizierung
        assert result is None


# =============================================================================
# UNIT TESTS: DatasetConfig.has_collection()
# =============================================================================


class TestDatasetConfigHasCollectionUnit:
    """Test: DatasetConfig.has_collection() Methode."""

    def test_has_collection_returns_true_if_exists(self, tmp_path):
        """
        Test: Gibt True zurück wenn Collection existiert.

        Purpose: Validation before operations.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [],
                },
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        result = config.has_collection("raw_data")

        # Verifizierung
        assert result is True

    def test_has_collection_returns_false_if_not_exists(self, tmp_path):
        """
        Test: Gibt False zurück wenn Collection nicht existiert.

        Purpose: Graceful validation.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [],
                },
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        result = config.has_collection("unknown")

        # Verifizierung
        assert result is False


# =============================================================================
# UNIT TESTS: DatasetConfig.get_collection_or_raise()
# =============================================================================


class TestDatasetConfigGetCollectionOrRaiseUnit:
    """Test: DatasetConfig.get_collection_or_raise() Methode."""

    def test_get_collection_or_raise_returns_collection(self, tmp_path):
        """
        Test: Gibt Collection zurück wenn existiert.

        Purpose: Fail-fast for user input.
        If fails: Collection retrieval broken.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [],
                },
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        collection = config.get_collection_or_raise("raw_data")

        # Verifizierung
        assert collection.id == "raw_data"

    def test_get_collection_or_raise_raises_if_not_found(self, tmp_path):
        """
        Test: Raises ValueError wenn Collection nicht existiert.

        Purpose: Clear error messages for user input.
        If fails: Missing collections don't raise.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [],
                },
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution & Verifizierung
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        with pytest.raises(ValueError, match="Collection with ID 'unknown' not found"):
            config.get_collection_or_raise("unknown")


# =============================================================================
# UNIT TESTS: Collection.session_ids()
# =============================================================================


class TestCollectionSessionIdsUnit:
    """Test: Collection.session_ids() Methode."""

    def test_session_ids_returns_all_ids(self, tmp_path):
        """
        Test: Gibt alle Session IDs für eine Collection.

        Purpose: User entdeckt verfügbare Sessions.
        If fails: Session discovery is broken.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [
                        {
                            "id": "session_001",
                            "name": "Session 1",
                            "date": "2011-09-26",
                            "location_type": "urban",
                            "parts": [],
                        },
                        {
                            "id": "session_002",
                            "name": "Session 2",
                            "date": "2011-09-26",
                            "location_type": "highway",
                            "parts": [],
                        },
                    ],
                }
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        collection = config.get_collection_by_id("raw_data")
        result = collection.session_ids()

        # Verifizierung
        assert result == ["session_001", "session_002"]


# =============================================================================
# UNIT TESTS: Collection.session_by_id()
# =============================================================================


class TestCollectionSessionByIdUnit:
    """Test: Collection.session_by_id() Methode."""

    def test_session_by_id_finds_session(self, tmp_path):
        """
        Test: Findet Session nach ID in Collection.

        Purpose: Validierung von Session IDs.
        If fails: Session lookup fails.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [
                        {
                            "id": "session_001",
                            "name": "Session 1",
                            "date": "2011-09-26",
                            "location_type": "urban",
                            "parts": [],
                        },
                        {
                            "id": "session_002",
                            "name": "Session 2",
                            "date": "2011-09-26",
                            "location_type": "highway",
                            "parts": [],
                        },
                    ],
                }
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        collection = config.get_collection_by_id("raw_data")
        session = collection.get_session_by_id("session_001")

        # Verifizierung
        assert session is not None
        assert session.id == "session_001"

    def test_session_by_id_returns_none_if_not_found(self, tmp_path):
        """
        Test: Gibt None zurück wenn Session nicht existiert.

        Purpose: Graceful Error Handling.
        If fails: Missing sessions don't return None.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [
                        {
                            "id": "session_001",
                            "name": "Session 1",
                            "date": "2011-09-26",
                            "location_type": "urban",
                            "parts": [],
                        },
                    ],
                }
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        collection = config.get_collection_by_id("raw_data")
        result = collection.get_session_by_id("unknown_session")

        # Verifizierung
        assert result is None


# =============================================================================
# UNIT TESTS: Session.part_ids()
# =============================================================================


class TestSessionPartIdsUnit:
    """Test: Session.part_ids() Methode."""

    def test_part_ids_returns_all_ids(self, tmp_path):
        """
        Test: Gibt alle Part IDs für eine Session.

        Purpose: User entdeckt verfügbare Parts.
        If fails: Part discovery is broken.
        """
        # Setup
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        fake_config = {
            "metadata": {
                "name": "Test",
                "description": "Test",
                "license": {"name": "MIT"},
            },
            "collections": [
                {
                    "id": "raw_data",
                    "name": "Raw",
                    "description": "Raw",
                    "sessions": [
                        {
                            "id": "session_001",
                            "name": "Session 1",
                            "date": "2011-09-26",
                            "location_type": "urban",
                            "parts": [
                                {
                                    "id": "oxts",
                                    "name": "OXTS",
                                    "download": {
                                        "url": "http://example.com/oxts.zip",
                                        "filename": "oxts.zip",
                                        "size_bytes": 100000,
                                        "md5": "abc123",
                                    },
                                },
                                {
                                    "id": "calib",
                                    "name": "Calibration",
                                    "download": {
                                        "url": "http://example.com/calib.zip",
                                        "filename": "calib.zip",
                                        "size_bytes": 50000,
                                        "md5": "def456",
                                    },
                                },
                            ],
                        },
                    ],
                }
            ],
        }

        with open(config_dir / "test.yaml", "w") as f:
            yaml.dump(fake_config, f)

        # Execution
        provider = ConfigProvider(config_dir=config_dir)
        config = provider.get_from_datasource("test")
        collection = config.get_collection_by_id("raw_data")
        session = collection.get_session_by_id("session_001")
        result = session.part_ids()

        # Verifizierung
        assert result == ["oxts", "calib"]
