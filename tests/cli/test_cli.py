# tests/cli/test_cli.py

from unittest.mock import Mock, patch

from click.testing import CliRunner
from mobility_datasets.cli.main import cli


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Mobility Datasets CLI" in result.output


def test_dataset_download_help():
    """Test dataset download help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "download", "--help"])

    assert result.exit_code == 0
    assert "Download dataset files" in result.output


# --- KITTI Tests ---


@patch("mobility_datasets.kitti.loader.KITTIDownloader")
def test_kitti_download_with_components(mock_downloader_class):
    """Test downloading specific KITTI components."""
    # Mock the downloader
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "download", "kitti", "--components", "oxts,calib"])

    assert result.exit_code == 0
    mock_downloader_class.assert_called_once_with(data_dir="./data/kitti")
    mock_downloader.download.assert_called_once_with(["oxts", "calib"], keep_zip=False)
    assert "Download complete!" in result.output


@patch("mobility_datasets.kitti.loader.KITTIDownloader")
def test_kitti_download_all(mock_downloader_class):
    """Test downloading all KITTI components."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "download", "kitti", "--all"])

    assert result.exit_code == 0
    mock_downloader.download_all.assert_called_once_with(keep_zip=False)


@patch("mobility_datasets.kitti.loader.KITTIDownloader")
def test_kitti_download_with_custom_dir(mock_downloader_class):
    """Test downloading KITTI to custom directory."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "download", "kitti", "--components", "oxts", "--data-dir", "/custom/path"]
    )

    assert result.exit_code == 0
    mock_downloader_class.assert_called_once_with(data_dir="/custom/path/kitti")


@patch("mobility_datasets.kitti.loader.KITTIDownloader")
def test_kitti_download_keep_archive(mock_downloader_class):
    """Test keeping archive files for KITTI."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "download", "kitti", "--components", "oxts", "--keep-archive"]
    )

    assert result.exit_code == 0
    mock_downloader.download.assert_called_once_with(["oxts"], keep_zip=True)


# --- nuScenes Tests ---


@patch("mobility_datasets.nuscenes.loader.NuScenesDownloader")
def test_nuscenes_download_with_components(mock_downloader_class):
    """Test downloading specific nuScenes components."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "download", "nuscenes", "--components", "metadata,lidar_keyframes"]
    )

    assert result.exit_code == 0
    mock_downloader_class.assert_called_once_with(data_dir="./data/nuscenes", version="mini")
    mock_downloader.download.assert_called_once_with(
        ["metadata", "lidar_keyframes"], keep_archive=False
    )
    assert "Download complete!" in result.output


@patch("mobility_datasets.nuscenes.loader.NuScenesDownloader")
def test_nuscenes_download_all(mock_downloader_class):
    """Test downloading all nuScenes components."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "download", "nuscenes", "--all"])

    assert result.exit_code == 0
    mock_downloader.download_all.assert_called_once_with(keep_archive=False)


@patch("mobility_datasets.nuscenes.loader.NuScenesDownloader")
def test_nuscenes_download_trainval_version(mock_downloader_class):
    """Test downloading nuScenes with trainval version."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "download", "nuscenes", "--all", "--version", "trainval"]
    )

    assert result.exit_code == 0
    mock_downloader_class.assert_called_once_with(data_dir="./data/nuscenes", version="trainval")
    mock_downloader.download_all.assert_called_once_with(keep_archive=False)


@patch("mobility_datasets.nuscenes.loader.NuScenesDownloader")
def test_nuscenes_download_test_version(mock_downloader_class):
    """Test downloading nuScenes with test version."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "download", "nuscenes", "--components", "metadata", "--version", "test"]
    )

    assert result.exit_code == 0
    mock_downloader_class.assert_called_once_with(data_dir="./data/nuscenes", version="test")
    mock_downloader.download.assert_called_once_with(["metadata"], keep_archive=False)


@patch("mobility_datasets.nuscenes.loader.NuScenesDownloader")
def test_nuscenes_download_with_custom_dir(mock_downloader_class):
    """Test downloading nuScenes to custom directory."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "dataset",
            "download",
            "nuscenes",
            "--components",
            "metadata",
            "--data-dir",
            "/custom/path",
        ],
    )

    assert result.exit_code == 0
    mock_downloader_class.assert_called_once_with(data_dir="/custom/path/nuscenes", version="mini")


@patch("mobility_datasets.nuscenes.loader.NuScenesDownloader")
def test_nuscenes_download_keep_archive(mock_downloader_class):
    """Test keeping archive files for nuScenes."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "dataset",
            "download",
            "nuscenes",
            "--components",
            "metadata",
            "--keep-archive",
        ],
    )

    assert result.exit_code == 0
    mock_downloader.download.assert_called_once_with(["metadata"], keep_archive=True)


# --- Error Handling Tests ---


def test_download_without_components_or_all():
    """Test that error is raised when neither components nor all is specified."""
    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "download", "kitti"])

    assert result.exit_code != 0
    assert "Error: Specify --components or --all" in result.output


def test_nuscenes_download_without_components_or_all():
    """Test that error is raised for nuScenes when neither components nor all is specified."""
    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "download", "nuscenes"])

    assert result.exit_code != 0
    assert "Error: Specify --components or --all" in result.output
