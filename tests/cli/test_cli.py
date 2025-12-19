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


@patch("mobility_datasets.kitti.loader.KITTIDownloader")
def test_download_with_components(mock_downloader_class):
    """Test downloading specific components."""
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
def test_download_all(mock_downloader_class):
    """Test downloading all components."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "download", "kitti", "--all"])

    assert result.exit_code == 0
    mock_downloader.download_all.assert_called_once_with(keep_zip=False)


@patch("mobility_datasets.kitti.loader.KITTIDownloader")
def test_download_with_custom_dir(mock_downloader_class):
    """Test downloading to custom directory."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "download", "kitti", "--components", "oxts", "--data-dir", "/custom/path"]
    )

    assert result.exit_code == 0
    mock_downloader_class.assert_called_once_with(data_dir="/custom/path/kitti")


@patch("mobility_datasets.kitti.loader.KITTIDownloader")
def test_download_keep_zip(mock_downloader_class):
    """Test keeping zip files."""
    mock_downloader = Mock()
    mock_downloader_class.return_value = mock_downloader

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "download", "kitti", "--components", "oxts", "--keep-zip"]
    )

    assert result.exit_code == 0
    mock_downloader.download.assert_called_once_with(["oxts"], keep_zip=True)


def test_download_without_components_or_all():
    """Test that error is raised when neither components nor all is specified."""
    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "download", "kitti"])

    assert result.exit_code != 0
    assert "Error: Specify --components or --all" in result.output
