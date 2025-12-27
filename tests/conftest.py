"""
Shared pytest fixtures and configuration for all tests.

This module provides:
- Common mock setups (HTTP responses, file archives)
- Temporary directory fixtures
- Custom pytest markers and configuration
- Shared test utilities

Organization
-------------
1. Pytest markers and configuration
2. HTTP response mocks
3. Archive file mocks (ZIP, TAR)
4. Downloader fixtures
5. Test utilities
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

# ============================================================================
# Pytest Markers & Configuration
# ============================================================================


def pytest_configure(config):
    """
    Register custom pytest markers.

    Markers can also be defined in pytest.ini, but we register them here
    for explicit control and better documentation.
    """
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (requires network)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow (may take longer to run)")


# ============================================================================
# HTTP Response Mocks
# ============================================================================


@pytest.fixture
def mock_http_response():
    """
    Create a mock HTTP response for download tests.

    Returns a Mock object that simulates a successful HTTP GET response
    with typical headers and content for dataset downloads.

    Returns
    -------
    Mock
        Mock HTTP response with:
        - headers: {"content-length": "1024"}
        - iter_content: Returns b"data" * 256 (simulated chunks)

    Examples
    --------
    >>> from unittest.mock import patch
    >>> @patch("module.requests.get")
    ... def test_download(mock_get, mock_http_response):
    ...     mock_get.return_value = mock_http_response
    ...     # Test code here
    """
    mock_response = Mock()
    mock_response.headers = {"content-length": "1024"}
    mock_response.iter_content = Mock(return_value=[b"data" * 256])
    return mock_response


@pytest.fixture
def mock_http_response_factory():
    """
    Factory fixture to create customized mock HTTP responses.

    Allows tests to create HTTP response mocks with specific content lengths
    and content patterns.

    Returns
    -------
    callable
        Function that creates mock HTTP responses.
        Signature: create_response(content_length=1024, chunk_pattern=b"data")

    Examples
    --------
    >>> def test_large_download(mock_http_response_factory):
    ...     mock_response = mock_http_response_factory(
    ...         content_length=1024*1024*100  # 100 MB
    ...     )
    ...     # Test code here
    """

    def create_response(content_length=1024, chunk_pattern=b"data"):
        """Create a custom mock HTTP response."""
        mock_response = Mock()
        mock_response.headers = {"content-length": str(content_length)}

        # Generate appropriate chunk data
        chunk_size = len(chunk_pattern) * 256
        num_chunks = max(1, content_length // chunk_size)
        chunks = [chunk_pattern * 256 for _ in range(num_chunks)]

        mock_response.iter_content = Mock(return_value=chunks)
        return mock_response

    return create_response


# ============================================================================
# Archive File Mocks (ZIP, TAR)
# ============================================================================


@pytest.fixture
def mock_zipfile():
    """
    Create a mock zipfile context manager.

    Returns a Mock object that can be used with the ZipFile context manager
    in tests involving ZIP archive extraction.

    Returns
    -------
    Mock
        Mock ZipFile with __enter__ and __exit__ methods configured for
        use as a context manager.

    Examples
    --------
    >>> @patch("module.zipfile.ZipFile")
    ... def test_extract(mock_zip_cls, mock_zipfile):
    ...     mock_zip_cls.return_value = mock_zipfile
    ...     # Test code here
    """
    mock_zip = Mock()
    mock_zip_manager = Mock()
    mock_zip_manager.__enter__ = Mock(return_value=mock_zip)
    mock_zip_manager.__exit__ = Mock(return_value=None)
    return mock_zip_manager


@pytest.fixture
def mock_zipfile_factory():
    """
    Factory fixture to create customized mock zipfile managers.

    Returns
    -------
    callable
        Function that creates mock zipfile context managers.

    Examples
    --------
    >>> def test_archive(mock_zipfile_factory):
    ...     mock_zip = mock_zipfile_factory()
    ...     # Test code here
    """

    def create_zipfile():
        mock_zip = Mock()
        mock_zip_manager = Mock()
        mock_zip_manager.__enter__ = Mock(return_value=mock_zip)
        mock_zip_manager.__exit__ = Mock(return_value=None)
        return mock_zip_manager

    return create_zipfile


@pytest.fixture
def mock_tarfile():
    """
    Create a mock tarfile context manager.

    Returns a Mock object that can be used with tarfile.open() context manager
    in tests involving TAR archive extraction.

    Returns
    -------
    Mock
        Mock tarfile with __enter__ and __exit__ methods configured for
        use as a context manager.

    Examples
    --------
    >>> @patch("module.tarfile.open")
    ... def test_extract(mock_tar_open, mock_tarfile):
    ...     mock_tar_open.return_value = mock_tarfile
    ...     # Test code here
    """
    mock_tar = Mock()
    mock_tar_manager = Mock()
    mock_tar_manager.__enter__ = Mock(return_value=mock_tar)
    mock_tar_manager.__exit__ = Mock(return_value=None)
    return mock_tar_manager


@pytest.fixture
def mock_tarfile_factory():
    """
    Factory fixture to create customized mock tarfile managers.

    Returns
    -------
    callable
        Function that creates mock tarfile context managers.

    Examples
    --------
    >>> def test_archive(mock_tarfile_factory):
    ...     mock_tar = mock_tarfile_factory()
    ...     # Test code here
    """

    def create_tarfile():
        mock_tar = Mock()
        mock_tar_manager = Mock()
        mock_tar_manager.__enter__ = Mock(return_value=mock_tar)
        mock_tar_manager.__exit__ = Mock(return_value=None)
        return mock_tar_manager

    return create_tarfile


# ============================================================================
# Downloader Fixtures (KITTI)
# ============================================================================


@pytest.fixture
def kitti_downloader(tmp_path):
    """
    Create a KITTIDownloader instance with temporary data directory.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest built-in fixture for temporary directory

    Returns
    -------
    KITTIDownloader
        Downloader instance configured for testing

    Examples
    --------
    >>> def test_download(kitti_downloader):
    ...     kitti_downloader.download(["calib"])
    ...     # Test code here
    """
    from mobility_datasets.core.downloader import DatasetDownloader

    return DatasetDownloader(data_dir=str(tmp_path / "kitti_data"))


@pytest.fixture
def kitti_downloader_no_cleanup(tmp_path):
    """
    Create a KITTIDownloader that persists between test methods in a class.

    Useful for testing state that persists across multiple operations.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest built-in fixture for temporary directory

    Returns
    -------
    KITTIDownloader
        Downloader instance with persistent state

    Examples
    --------
    >>> class TestKITTIState:
    ...     def test_first_operation(self, kitti_downloader_no_cleanup):
    ...         # Operation 1
    ...     def test_second_operation(self, kitti_downloader_no_cleanup):
    ...         # Operation 2 (state from op 1 is available)
    """
    from mobility_datasets.core.downloader import DatasetDownloader

    return DatasetDownloader(data_dir=str(tmp_path / "kitti_persistent"))


# ============================================================================
# Downloader Fixtures (nuScenes)
# ============================================================================


@pytest.fixture
def nuscenes_downloader_mini(tmp_path):
    """
    Create a NuScenesDownloader instance with mini version.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest built-in fixture for temporary directory

    Returns
    -------
    NuScenesDownloader
        Downloader instance configured for mini version

    Examples
    --------
    >>> def test_download(nuscenes_downloader_mini):
    ...     nuscenes_downloader_mini.download(["metadata"])
    ...     # Test code here
    """
    from mobility_datasets.nuscenes.loader import NuScenesDownloader

    return NuScenesDownloader(data_dir=str(tmp_path / "nuscenes_data"), version="mini")


@pytest.fixture
def nuscenes_downloader_trainval(tmp_path):
    """
    Create a NuScenesDownloader instance with trainval version.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest built-in fixture for temporary directory

    Returns
    -------
    NuScenesDownloader
        Downloader instance configured for trainval version
    """
    from mobility_datasets.nuscenes.loader import NuScenesDownloader

    return NuScenesDownloader(data_dir=str(tmp_path / "nuscenes_data"), version="trainval")


@pytest.fixture
def nuscenes_downloader_test(tmp_path):
    """
    Create a NuScenesDownloader instance with test version.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest built-in fixture for temporary directory

    Returns
    -------
    NuScenesDownloader
        Downloader instance configured for test version
    """
    from mobility_datasets.nuscenes.loader import NuScenesDownloader

    return NuScenesDownloader(data_dir=str(tmp_path / "nuscenes_data"), version="test")


@pytest.fixture(params=["mini", "trainval", "test"])
def nuscenes_downloader_all_versions(tmp_path, request):
    """
    Create NuScenesDownloader instances for all versions (parametrized).

    This is a parametrized fixture that runs the test for each nuScenes version.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest built-in fixture for temporary directory
    request : pytest.FixtureRequest
        Pytest fixture request object containing the version parameter

    Returns
    -------
    NuScenesDownloader
        Downloader instance for the current version in the parametrized run

    Examples
    --------
    >>> def test_all_versions(nuscenes_downloader_all_versions):
    ...     # This test will run 3 times, once for each version
    ...     downloader = nuscenes_downloader_all_versions
    ...     # Test code here
    """
    from mobility_datasets.nuscenes.loader import NuScenesDownloader

    return NuScenesDownloader(
        data_dir=str(tmp_path / f"nuscenes_{request.param}"),
        version=request.param,
    )


# ============================================================================
# File Creation Utilities
# ============================================================================


@pytest.fixture
def create_archive_files():
    """
    Factory fixture to create fake archive files for testing.

    Allows tests to create ZIP/TAR files without downloading actual data.

    Returns
    -------
    callable
        Function to create archive files.
        Signature: create_archive_files(base_path, filenames, format="zip")

    Examples
    --------
    >>> def test_with_archives(create_archive_files, tmp_path):
    ...     archives = create_archive_files(
    ...         tmp_path,
    ...         ["data_tracking_calib.zip", "data_tracking_oxts.zip"]
    ...     )
    ...     assert len(archives) == 2
    """

    def create_files(base_path: Path, filenames: list, format: str = "zip"):
        """Create fake archive files."""
        archives = []
        for filename in filenames:
            file_path = Path(base_path) / filename
            file_path.write_text(f"fake {format} content")
            archives.append(file_path)
        return archives

    return create_files


@pytest.fixture
def create_data_directory_structure():
    """
    Factory fixture to create realistic dataset directory structures.

    Useful for testing file discovery and path handling.

    Returns
    -------
    callable
        Function to create directory structures.

    Examples
    --------
    >>> def test_structure(create_data_directory_structure, tmp_path):
    ...     structure = create_data_directory_structure(
    ...         tmp_path,
    ...         {
    ...             "raw_data/2011_10_03/drive_0027/oxts/data": [
    ...                 "0000000000.txt",
    ...                 "0000000001.txt",
    ...             ]
    ...         }
    ...     )
    """

    def create_structure(base_path: Path, structure: dict):
        """Create directory structure with files."""
        created_dirs = []
        created_files = []

        for dir_path, files in structure.items():
            full_path = Path(base_path) / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)

            for filename in files:
                file_path = full_path / filename
                file_path.write_text(f"content of {filename}")
                created_files.append(file_path)

        return {"directories": created_dirs, "files": created_files}

    return create_structure


# ============================================================================
# Test Output Utilities
# ============================================================================


@pytest.fixture
def captured_output(capsys):
    """
    Convenience wrapper for capsys to get combined stdout/stderr.

    Parameters
    ----------
    capsys : pytest.CaptureFixture
        Built-in pytest fixture for capturing output

    Returns
    -------
    callable
        Function that returns captured output.
        Returns: (stdout, stderr, combined)

    Examples
    --------
    >>> def test_output(captured_output):
    ...     print("Hello")
    ...     stdout, stderr, combined = captured_output()
    ...     assert "Hello" in combined
    """

    def get_output():
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        return captured.out, captured.err, combined

    return get_output
