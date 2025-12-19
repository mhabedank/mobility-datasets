"""Tests for CLI functionality."""

from pathlib import Path

from click.testing import CliRunner

from mobility_datasets.cli.main import cli


class TestCLI:
    """Test CLI commands."""

    def test_cli_help(self) -> None:
        """Test CLI help message."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Mobility Datasets CLI" in result.output

    def test_dataset_list(self) -> None:
        """Test dataset list command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["dataset", "list"])
        assert result.exit_code == 0
        assert "Available Datasets" in result.output
        assert "kitti" in result.output.lower()
        assert "nuscenes" in result.output.lower()
        assert "waymo" in result.output.lower()

    def test_dataset_list_json(self) -> None:
        """Test dataset list command with JSON output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["dataset", "list", "--format", "json"])
        assert result.exit_code == 0
        assert "kitti" in result.output.lower()

    def test_dataset_info(self, tmp_path: Path) -> None:
        """Test dataset info command."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["dataset", "info", "kitti", "--root-dir", str(tmp_path), "--split", "training"]
        )
        assert result.exit_code == 0
        assert "Dataset Information" in result.output

    def test_dataset_info_json(self, tmp_path: Path) -> None:
        """Test dataset info command with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "dataset",
                "info",
                "kitti",
                "--root-dir",
                str(tmp_path),
                "--split",
                "training",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        assert "num_samples" in result.output

    def test_dataset_download(self, tmp_path: Path) -> None:
        """Test dataset download command."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["dataset", "download", "kitti", "--root-dir", str(tmp_path), "--split", "training"],
        )
        assert result.exit_code == 0
        assert "Download instructions" in result.output
