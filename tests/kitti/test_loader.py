# tests/kitti/test_downloader.py
from unittest.mock import Mock, patch

import pytest
from mobility_datasets.kitti.loader import KITTIDownloader


def test_download_creates_directory(tmp_path):
    """Test that data directory is created."""
    data_dir = tmp_path / "kitti_data"
    _ = KITTIDownloader(data_dir=str(data_dir))

    assert data_dir.exists()


@patch("mobility_datasets.kitti.loader.requests.get")
@patch("mobility_datasets.kitti.loader.zipfile.ZipFile")
def test_download_component(mock_zipfile, mock_requests, tmp_path):
    """Test downloading a single component."""
    # Mock HTTP response
    mock_response = Mock()
    mock_response.headers = {"content-length": "1024"}
    mock_response.iter_content = Mock(return_value=[b"data" * 256])
    mock_requests.return_value = mock_response

    # Mock zipfile
    mock_zip = Mock()
    mock_zipfile.return_value.__enter__ = Mock(return_value=mock_zip)
    mock_zipfile.return_value.__exit__ = Mock(return_value=None)

    # Test
    downloader = KITTIDownloader(data_dir=str(tmp_path))
    downloader.download(["calib"])

    # Verify requests was called
    mock_requests.assert_called_once()
    assert "data_tracking_calib.zip" in mock_requests.call_args[0][0]


@patch("mobility_datasets.kitti.loader.requests.get")
@patch("mobility_datasets.kitti.loader.zipfile.ZipFile")
def test_download_all(mock_zipfile, mock_requests, tmp_path):
    """Test downloading all components."""
    # Mock HTTP response
    mock_response = Mock()
    mock_response.headers = {"content-length": "1024"}
    mock_response.iter_content = Mock(return_value=[b"data" * 256])
    mock_requests.return_value = mock_response

    # Mock zipfile
    mock_zip = Mock()
    mock_zipfile.return_value.__enter__ = Mock(return_value=mock_zip)
    mock_zipfile.return_value.__exit__ = Mock(return_value=None)

    # Test
    downloader = KITTIDownloader(data_dir=str(tmp_path))
    downloader.download_all()

    # Verify all 6 components were downloaded
    assert mock_requests.call_count == 6


@patch("mobility_datasets.kitti.loader.requests.get")
@patch("mobility_datasets.kitti.loader.zipfile.ZipFile")
def test_skip_existing_file(mock_zipfile, mock_requests, tmp_path, capsys):
    """Test that existing files are skipped."""
    # Create existing zip file
    zip_path = tmp_path / "data_tracking_calib.zip"
    zip_path.touch()

    # Test
    downloader = KITTIDownloader(data_dir=str(tmp_path))
    downloader.download(["calib"])

    # Verify no download was attempted
    mock_requests.assert_not_called()

    # Verify message was printed
    captured = capsys.readouterr()
    assert "already exists" in captured.out


def test_unknown_component(tmp_path, capsys):
    """Test handling of unknown component."""
    downloader = KITTIDownloader(data_dir=str(tmp_path))
    downloader.download(["invalid_component"])

    captured = capsys.readouterr()
    assert "Unknown component" in captured.out


def test_available_files():
    """Test that all expected components are available."""
    expected = ["oxts", "calib", "label", "image_left", "image_right", "velodyne"]

    for component in expected:
        assert component in KITTIDownloader.AVAILABLE_FILES


@pytest.mark.integration
def test_kitti_all_files_available():
    """
    Integration test: Verify all KITTI files are available on S3.

    This test performs actual HTTP HEAD requests to AWS S3 to verify that
    all dataset files exist and are accessible. It does not download files.

    The test will fail if:
    - Any file returns HTTP 404 (not found)
    - Any file is inaccessible due to network errors
    - AWS S3 bucket structure has changed
    - Files have been moved or deleted

    Notes
    -----
    This is a real integration test that requires internet connectivity.
    It should be run:
    - Before releases to verify download functionality
    - Periodically (e.g., monthly) to catch broken URLs
    - When adding new components to AVAILABLE_FILES

    Examples
    --------
    Run only integration tests:

        pytest tests/integration/ -v

    Run with detailed output:

        pytest tests/integration/test_kitti_availability.py -v -s

    Skip integration tests in CI:

        pytest -m "not integration"
    """
    # Initialize downloader (no download, just check)
    downloader = KITTIDownloader()

    # Perform health check
    status = downloader.health_check()

    # Collect failed components
    failed_components = [component for component, available in status.items() if not available]

    # Assert all files are available
    assert all(status.values()), (
        f"Some KITTI files are not available on S3. "
        f"Failed components: {failed_components}. "
        f"This may indicate:\n"
        f"  - Files were moved or deleted on S3\n"
        f"  - AWS S3 bucket structure changed\n"
        f"  - Network connectivity issues\n"
        f"  - Temporary S3 outage\n"
        f"Status: {status}"
    )

    # Verify we checked all expected components
    expected_components = ["oxts", "calib", "label", "image_left", "image_right", "velodyne"]
    assert set(status.keys()) == set(
        expected_components
    ), f"Component mismatch. Expected {expected_components}, got {list(status.keys())}"


@pytest.mark.integration
def test_kitti_base_url_accessible():
    """
    Integration test: Verify KITTI base URL is accessible.

    This test checks if the AWS S3 base URL responds successfully.
    """
    import requests

    downloader = KITTIDownloader()
    base_url = downloader.BASE_URL

    try:
        # Simple GET request to base URL (should return 403 or 200, not 404)
        response = requests.head(base_url, timeout=10)

        # S3 bucket root may return 403 (forbidden) but should not be 404
        assert response.status_code != 404, (
            f"KITTI base URL returned 404: {base_url}. "
            f"The S3 bucket may have been deleted or moved."
        )
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Cannot reach KITTI base URL {base_url}: {e}")


@pytest.mark.integration
def test_kitti_essential_files_available():
    """
    Integration test: Verify essential KITTI files are available.

    Tests only the minimal files needed for sensor fusion:
    - oxts (GPS/IMU data)
    - calib (calibration)

    This is a lighter test than test_kitti_all_files_available and can be
    run more frequently.
    """
    downloader = KITTIDownloader()

    # Check only essential components
    essential_components = ["oxts", "calib"]
    status = downloader.health_check()

    for component in essential_components:
        assert status[component], (
            f"Essential KITTI component '{component}' is not available. "
            f"This will break basic sensor fusion workflows."
        )


@pytest.mark.integration
@pytest.mark.slow
def test_kitti_large_files_available():
    """
    Integration test: Verify large KITTI files are available.

    Tests the large files (images, velodyne) separately as they may be
    slower to check and more prone to S3 issues.

    Marked as 'slow' because checking large files may take longer.
    """
    downloader = KITTIDownloader()
    status = downloader.health_check()

    large_files = ["image_left", "image_right", "velodyne"]

    for component in large_files:
        assert status[component], (
            f"Large KITTI component '{component}' is not available on S3. "
            f"Users will not be able to download complete dataset."
        )
