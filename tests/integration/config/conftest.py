from pathlib import Path

import pytest


@pytest.fixture
def config_dir():
    """
    Fixture: Gibt den Pfad zu echten Test-Konfigurationsdateien zurück.

    Purpose: Lädt Configs von Disk statt sie in Fixtures zu erstellen.

    Directory Structure:
    tests/integration/data/configs/
    ├── kitti.yaml
    └── nuscenes.yaml
    """
    data_dir = Path(__file__).parent / "data" / "configs"
    assert data_dir.exists(), f"Test data directory not found: {data_dir}"
    return data_dir
