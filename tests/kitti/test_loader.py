# tests/kitti/test_downloader.py
from unittest.mock import Mock, patch

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
