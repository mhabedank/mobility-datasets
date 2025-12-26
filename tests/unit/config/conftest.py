"""
Fixtures for unit tests of config.provider.

Location: tests/unit/config/conftest.py

These fixtures provide dict representations for testing ConfigLoader
methods (dict_to_X functions). No dataclass instances needed.
"""

import pytest


@pytest.fixture
def dict_license_minimal():
    """Minimal License dict."""
    return {"name": "MIT"}


@pytest.fixture
def dict_license_full():
    """Full License dict with all fields."""
    return {
        "name": "CC BY-NC-SA 3.0",
        "url": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
        "details": "Non-commercial use only",
    }


@pytest.fixture
def dict_citation():
    """Citation dict."""
    return {"bibtex": "@article{Geiger2013IJRR,author={Andreas Geiger}}"}


@pytest.fixture
def dict_download_info():
    """DownloadInfo dict."""
    return {
        "url": "https://s3.eu-central-1.amazonaws.com/avg-kitti/file.zip",
        "filename": "file.zip",
        "size_bytes": 1_000_000,
        "md5": "5d41402abc4b2a76b9719d911017c592",
        "format": "zip",
    }


@pytest.fixture
def dict_part(dict_download_info):
    """Part dict."""
    return {"id": "synced_rectified", "name": "Synced + Rectified", "download": dict_download_info}


@pytest.fixture
def dict_session(dict_part):
    """Session dict with one part."""
    return {
        "id": "2011_09_26_drive_0001",
        "name": "2011_09_26_drive_0001",
        "date": "2011-09-26",
        "location_type": "City",
        "parts": [dict_part],
    }


@pytest.fixture
def dict_collection(dict_session):
    """Collection dict with one session."""
    return {
        "id": "raw_data",
        "name": "Raw Data",
        "description": "Raw sensor data",
        "sessions": [dict_session],
    }


@pytest.fixture
def dict_metadata_minimal(dict_license_minimal):
    """Minimal Metadata dict (no citation)."""
    return {
        "name": "KITTI",
        "description": "KITTI Vision Benchmark Suite",
        "license": dict_license_minimal,
    }


@pytest.fixture
def dict_metadata_full(dict_license_full, dict_citation):
    """Full Metadata dict with citation."""
    return {
        "name": "KITTI",
        "description": "KITTI Vision Benchmark Suite",
        "license": dict_license_full,
        "citation": dict_citation,
    }


@pytest.fixture
def dict_config_minimal(dict_metadata_minimal):
    """Minimal DatasetConfig dict (no collections)."""
    return {"metadata": dict_metadata_minimal, "collections": []}


@pytest.fixture
def dict_config_full(dict_metadata_full, dict_collection):
    """Full DatasetConfig dict with collection."""
    return {"metadata": dict_metadata_full, "collections": [dict_collection]}


@pytest.fixture
def dict_invalid_missing_license():
    """Invalid dict - missing required 'license' field."""
    return {
        "metadata": {
            "name": "KITTI",
            "description": "Test Dataset",
            # Missing 'license'
        },
        "collections": [],
    }


@pytest.fixture
def dict_invalid_missing_name():
    """Invalid dict - missing required 'name' field in metadata."""
    return {
        "metadata": {
            "description": "Test Dataset",
            "license": {"name": "MIT"},
            # Missing 'name'
        },
        "collections": [],
    }


@pytest.fixture
def dict_invalid_empty_collections():
    """Valid dict with empty collections list."""
    return {
        "metadata": {"name": "KITTI", "description": "Test Dataset", "license": {"name": "MIT"}},
        "collections": [],
    }
