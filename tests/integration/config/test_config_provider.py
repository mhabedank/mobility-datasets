"""
Integration Tests für ConfigProvider.

Location: tests/integration/test_config_provider.py

Test-Daten befinden sich in:
  tests/integration/data/configs/
  ├── kitti.yaml
  └── nuscenes.yaml

Diese Tests laden echte YAML-Dateien vom Dateisystem - KEINE Patches!
"""

import pytest
import yaml
from mobility_datasets.config import ConfigProvider


class TestConfigProviderIntegrationBasics:
    """
    Integration Tests mit echten YAML Dateien aus tests/integration/data/.

    Keine @patch Decorators - echte Path, echte YAML Operationen.
    """

    def test_init_accepts_real_config_directory(self, config_dir):
        """
        Test: ConfigProvider akzeptiert echtes config_dir.

        Purpose: Initialization mit echtem Dateisystem funktioniert.
        """

        provider = ConfigProvider(config_dir=str(config_dir))

        assert provider.config_dir.exists()
        assert provider.config_dir == config_dir

    def test_init_rejects_nonexistent_directory(self, tmp_path):
        """
        Test: ConfigProvider lehnt nicht-existentes Verzeichnis ab.

        Purpose: Klare Error Messages für falsche config_dir.
        """

        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(ValueError, match="Config directory does not exist:*"):
            ConfigProvider(config_dir=str(nonexistent))

    def test_list_datasources_discovers_yaml_files(self, config_dir):
        """
        Test: list_available_datasources() findet alle YAML Dateien.

        Purpose: Use Case 1 - User sieht alle verfügbaren Datasets.
        Lädt echte Dateien aus tests/integration/data/configs/
        """

        provider = ConfigProvider(config_dir=str(config_dir))
        datasources = provider.list_datasources()

        # Sollte mindestens kitti und nuscenes finden
        assert "kitti" in datasources
        assert "nuscenes" in datasources
        assert isinstance(datasources, list)

    def test_list_datasources_empty_config_dir(self, tmp_path):
        """
        Test: Leeres config_dir gibt leere Liste zurück.

        Purpose: Keine Exception wenn keine Configs vorhanden.
        """

        empty_dir = tmp_path / "empty_config"
        empty_dir.mkdir()

        provider = ConfigProvider(config_dir=str(empty_dir))
        datasources = provider.list_datasources()

        assert datasources == []

    def test_get_from_datasource_loads_yaml(self, config_dir):
        """
        Test: get_from_datasource() lädt und parst echte YAML.

        Purpose: YAML Parsing funktioniert mit echtem Dateisystem.
        Lädt tests/integration/data/configs/kitti.yaml
        """

        provider = ConfigProvider(config_dir=str(config_dir))
        config = provider.get_from_datasource("kitti")

        assert config.metadata.name == "The KITTI Vision Benchmark Suite"
        assert isinstance(config.collections, list)

    def test_get_from_datasource_raises_on_missing_file(self, config_dir):
        """
        Test: FileNotFoundError wenn Datasource nicht existiert.

        Purpose: Klare Error Messages.
        """

        provider = ConfigProvider(config_dir=str(config_dir))

        with pytest.raises(FileNotFoundError, match="unknown.yaml"):
            provider.get_from_datasource("unknown")

    def test_get_from_datasource_handles_malformed_yaml(self, tmp_path):
        """
        Test: Fehler bei ungültiger YAML Syntax.

        Purpose: Konfigurationsfehler werden erkannt.
        """

        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Schreibe ungültige YAML
        bad_yaml_file = config_dir / "bad_config.yaml"
        with open(bad_yaml_file, "w") as f:
            f.write("datasource_id: bad\n")
            f.write("collections: [invalid: syntax: here")  # Ungültige YAML

        provider = ConfigProvider(config_dir=str(config_dir))

        with pytest.raises(yaml.YAMLError):
            provider.get_from_datasource("bad_config")

    def test_list_available_collections_returns_ids(self, config_dir):
        """
        Test: list_available_collections() gibt Collection IDs zurück.

        Purpose: Use Case 1 - User sieht Collections im Dataset.
        Lädt aus echter tests/integration/data/configs/kitti.yaml
        """

        provider = ConfigProvider(config_dir=str(config_dir))
        collections = provider.get_from_datasource("kitti").collection_ids()

        assert "raw_data" in collections
        assert isinstance(collections, list)


class TestConfigProviderUseCase1:
    """
    Integration Tests für Use Case 1: User entdeckt verfügbare Daten.

    Scenario: Neuer User möchte wissen welche Datasets/Collections/Sessions
    verfügbar sind.
    Lädt echte Dateien aus tests/integration/data/configs/
    """

    def test_discover_all_datasets(self, config_dir):
        """
        Test: "Welche Datasets gibt es?"

        Purpose: User sieht auf einen Blick alle verfügbaren Datasets.
        """

        provider = ConfigProvider(config_dir=str(config_dir))

        datasets = provider.list_datasources()

        assert len(datasets) >= 2
        assert "kitti" in datasets
        assert "nuscenes" in datasets

    def test_discover_collections_in_dataset(self, config_dir):
        """
        Test: "Was sind die Collections in KITTI?"

        Purpose: User sieht welche Collections in KITTI verfügbar sind.
        """

        provider = ConfigProvider(config_dir=str(config_dir))

        collections = provider.get_from_datasource("kitti").collection_ids()

        assert len(collections) >= 1
        assert "raw_data" in collections

    def test_discover_sessions_in_collection(self, config_dir):
        """
        Test: "Welche Sessions gibt es in raw_data?"

        Purpose: User sieht welche Sessions zum Download verfügbar sind.
        """

        provider = ConfigProvider(config_dir=str(config_dir))

        kitti_config = provider.get_from_datasource("kitti")
        collection = kitti_config.get_collection_by_id("raw_data")
        sessions = collection.session_ids()

        assert len(sessions) >= 1
        assert "2011_09_26_drive_0001" in sessions

    def test_workflow_discover_then_access(self, config_dir):
        """
        Test: Kompletter Workflow - entdecken und dann abrufen.

        Purpose: User kann iterativ navigieren durch Struktur.
        """
        provider = ConfigProvider(config_dir=str(config_dir))

        # 1. Alle Datasets
        datasets = provider.list_datasources()
        assert "kitti" in datasets

        # 2. Collections in KITTI
        collections = provider.get_from_datasource("kitti").collection_ids()
        assert "raw_data" in collections

        # 3. Sessions in raw_data
        kitti_config = provider.get_from_datasource("kitti")
        collection = kitti_config.get_collection_by_id("raw_data")
        sessions = collection.session_ids()
        assert "2011_09_26_drive_0001" in sessions

        # 4. Actual Session object
        session = collection.get_session_by_id("2011_09_26_drive_0001")
        assert session.id == "2011_09_26_drive_0001"


class TestConfigProviderUseCase3:
    """
    Integration Tests für Use Case 3: Validierung von User Input.

    Scenario: User gibt Collection/Session ID an, wir validieren dass sie existiert.
    Lädt echte Dateien aus tests/integration/data/configs/
    """

    def test_validate_valid_collection(self, config_dir):
        """
        Test: Valid collection_id wird akzeptiert.

        Purpose: Keine Exception bei gültiger Eingabe.
        """
        provider = ConfigProvider(config_dir=str(config_dir))

        # Sollte nicht werfen
        collection = provider.get_from_datasource("kitti").get_collection_by_id("raw_data")
        assert collection is not None

    def test_validate_invalid_collection(self, config_dir):
        """
        Test: Invalid collection_id wird abgelehnt.

        Purpose: Klare Error Message für falsche Collection.
        """
        provider = ConfigProvider(config_dir=str(config_dir))

        collection = provider.get_from_datasource("kitti").get_collection_by_id(
            "unknown_collection"
        )
        assert collection is None

    def test_validate_valid_session(self, config_dir):
        """
        Test: Valid session_id wird akzeptiert.

        Purpose: Keine Exception bei gültiger Session.
        """
        provider = ConfigProvider(config_dir=str(config_dir))

        kitti_config = provider.get_from_datasource("kitti")
        collection = kitti_config.get_collection_by_id("raw_data")
        session = collection.get_session_by_id("2011_09_26_drive_0001")
        assert session.id == "2011_09_26_drive_0001"

    def test_validate_invalid_session(self, config_dir):
        """
        Test: Invalid session_id wird abgelehnt.

        Purpose: Klare Error Message für falsche Session.
        """
        provider = ConfigProvider(config_dir=str(config_dir))

        kitti_config = provider.get_from_datasource("kitti")
        collection = kitti_config.get_collection_by_id("raw_data")
        session = collection.get_session_by_id("unknown_session")
        assert session is None

    def test_validate_session_wrong_collection(self, config_dir):
        """
        Test: Session gibt Error wenn Collection falsch ist.

        Purpose: Zuerst Collection validieren, dann Session.
        """
        provider = ConfigProvider(config_dir=str(config_dir))

        kitti_config = provider.get_from_datasource("kitti")
        collection = kitti_config.get_collection_by_id("wrong_collection")
        assert collection is None


class TestConfigProviderUseCase4:
    """
    Integration Tests für Use Case 4: Health Check.

    Scenario: Health Check iteriert über Config um alle URLs zu prüfen.
    Lädt echte Dateien aus tests/integration/data/configs/
    """

    def test_get_all_urls_from_collection(self, config_dir):
        """
        Test: get_all_download_urls() gibt alle Download URLs einer Collection.

        Purpose: Health Check kann über alle URLs iterieren.
        """
        provider = ConfigProvider(config_dir=str(config_dir))

        collection = provider.get_from_datasource("kitti").get_collection_by_id("raw_data")

        urls = [part.download.url for session in collection.sessions for part in session.parts]

        # 2 Sessions * 1-2 Parts = mindestens 3 URLs
        assert len(urls) >= 3
        assert all("s3.eu-central-1.amazonaws.com" in url or "avg-kitti" in url for url in urls)

    def test_urls_include_metadata(self, config_dir):
        """
        Test: URLs haben Metadaten wie size_bytes.

        Purpose: Health Check kann Details abrufen.
        """
        provider = ConfigProvider(config_dir=str(config_dir))

        # Sollte auch Metadaten abrufen können
        session = (
            provider.get_from_datasource("kitti")
            .get_collection_by_id("raw_data")
            .get_session_by_id("2011_09_26_drive_0001")
        )

        unsynced_part = session.parts[0]
        assert "size_bytes" in unsynced_part.download.__dict__
        assert unsynced_part.download.size_bytes == 696833348
