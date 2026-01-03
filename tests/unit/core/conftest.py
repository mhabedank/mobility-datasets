"""Fixtures for core downloader tests."""

import io
import tarfile
import zipfile
from unittest.mock import Mock, patch

import pytest
from mobility_datasets.config.provider import (
    Collection,
    DatasetConfig,
    DownloadInfo,
    License,
    Metadata,
    Part,
    Session,
)
from mobility_datasets.core.downloader import DatasetDownloader


@pytest.fixture
def mock_config():
    """Minimal valid DatasetConfig for testing.

    Returns
    -------
    DatasetConfig
        Test config with one collection, one session, one part.
    """
    return DatasetConfig(
        metadata=Metadata(
            name="Test Dataset",
            description="For testing",
            license=License(name="CC0"),
        ),
        collections=[
            Collection(
                id="test_collection",
                name="Test Collection",
                description="Test",
                sessions=[
                    Session(
                        id="test_session_001",
                        name="Test Session 001",
                        date="2024-01-01",
                        location_type="Test",
                        parts=[
                            Part(
                                id="test_part",
                                name="Test Part",
                                optional=False,
                                download=DownloadInfo(
                                    url="https://example.com/test.zip",
                                    filename="test.zip",
                                    size_bytes=1000,
                                    md5="abc123def456",
                                    format="zip",
                                ),
                            )
                        ],
                    )
                ],
            )
        ],
    )


@pytest.fixture
def mock_config_with_optional():
    """DatasetConfig with optional parts for testing.

    Returns
    -------
    DatasetConfig
        Test config with optional part.
    """
    return DatasetConfig(
        metadata=Metadata(
            name="Test Dataset",
            description="For testing",
            license=License(name="CC0"),
        ),
        collections=[
            Collection(
                id="test_collection",
                name="Test Collection",
                description="Test",
                sessions=[
                    Session(
                        id="test_session_001",
                        name="Test Session 001",
                        date="2024-01-01",
                        location_type="Test",
                        parts=[
                            Part(
                                id="required_part",
                                name="Required Part",
                                optional=False,
                                download=DownloadInfo(
                                    url="https://example.com/required.zip",
                                    filename="required.zip",
                                    size_bytes=500,
                                    md5="aaa111",
                                    format="zip",
                                ),
                            ),
                            Part(
                                id="optional_part",
                                name="Optional Part",
                                optional=True,
                                download=DownloadInfo(
                                    url="https://example.com/optional.zip",
                                    filename="optional.zip",
                                    size_bytes=500,
                                    md5="bbb222",
                                    format="zip",
                                ),
                            ),
                        ],
                    )
                ],
            )
        ],
    )


@pytest.fixture
def mock_config_multiple_collections():
    """DatasetConfig with multiple collections.

    Returns
    -------
    DatasetConfig
        Test config with 2 collections.
    """
    return DatasetConfig(
        metadata=Metadata(
            name="Test Dataset",
            description="For testing",
            license=License(name="CC0"),
        ),
        collections=[
            Collection(
                id="collection_001",
                name="Collection 001",
                description="Test",
                sessions=[
                    Session(
                        id="session_001",
                        name="Session 001",
                        date="2024-01-01",
                        location_type="Test",
                        parts=[
                            Part(
                                id="part_001",
                                name="Part 001",
                                optional=False,
                                download=DownloadInfo(
                                    url="https://example.com/001.zip",
                                    filename="001.zip",
                                    size_bytes=100,
                                    md5="111",
                                    format="zip",
                                ),
                            )
                        ],
                    )
                ],
            ),
            Collection(
                id="collection_002",
                name="Collection 002",
                description="Test",
                sessions=[
                    Session(
                        id="session_002",
                        name="Session 002",
                        date="2024-01-02",
                        location_type="Test",
                        parts=[
                            Part(
                                id="part_002",
                                name="Part 002",
                                optional=False,
                                download=DownloadInfo(
                                    url="https://example.com/002.zip",
                                    filename="002.zip",
                                    size_bytes=100,
                                    md5="222",
                                    format="zip",
                                ),
                            )
                        ],
                    )
                ],
            ),
        ],
    )


@pytest.fixture
def downloader(tmp_path, mock_config):
    """DatasetDownloader with mocked ConfigProvider.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory.
    mock_config : DatasetConfig
        Mocked configuration.

    Returns
    -------
    DatasetDownloader
        Ready-to-use downloader instance.
    """
    with patch("mobility_datasets.core.downloader.ConfigProvider") as mock_provider_class:
        mock_provider = Mock()
        mock_provider.get_from_datasource.return_value = mock_config
        mock_provider_class.return_value = mock_provider

        return DatasetDownloader(dataset="test", data_dir=str(tmp_path))


@pytest.fixture
def test_zip_file(tmp_path):
    """Create a minimal valid ZIP file for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory.

    Returns
    -------
    Path
        Path to created ZIP file.
    """
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("test.txt", "test content")

    return zip_path


@pytest.fixture
def test_tar_gz_file(tmp_path):
    """Create a minimal valid TAR.GZ file for testing.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory.

    Returns
    -------
    Path
        Path to created TAR.GZ file.
    """
    tar_path = tmp_path / "test.tar.gz"
    with tarfile.open(tar_path, "w:gz") as t:
        info = tarfile.TarInfo(name="test.txt")
        info.size = 12
        t.addfile(info, io.BytesIO(b"test content"))

    return tar_path
