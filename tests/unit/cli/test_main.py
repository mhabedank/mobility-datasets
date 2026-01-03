"""Unit tests for CLI commands.

Module: tests/unit/cli/test_cli_main.py
Purpose: Test CLI input validation, error handling, and output formatting
Layer: Unit tests (no real downloads, extensive mocking)

Tests cover:
- Command structure and option parsing
- Input validation and error messages
- Help text and documentation
- Output formatting and user messaging
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner
from mobility_datasets.cli.main import (
    cli,
    get_available_datasets,
)


class TestGetAvailableDatasets:
    """Test suite for get_available_datasets() helper function."""

    def test_returns_list_of_dataset_names(self):
        """
        Test: Returns available dataset names from config provider.

        Purpose: Verify dataset discovery works before CLI is initialized.
        """
        with patch("mobility_datasets.cli.main.ConfigProvider") as mock_provider_cls:
            mock_provider = Mock()
            mock_provider_cls.return_value = mock_provider
            mock_provider.list_datasources.return_value = ["kitti", "nuscenes", "waymo"]

            datasets = get_available_datasets()

            assert datasets == ["kitti", "nuscenes", "waymo"]
            mock_provider.list_datasources.assert_called_once()

    def test_returns_empty_list_when_no_datasets(self):
        """
        Test: Returns empty list if no datasets are configured.

        Purpose: Graceful handling of misconfigured systems.
        """
        with patch("mobility_datasets.cli.main.ConfigProvider") as mock_provider_cls:
            mock_provider = Mock()
            mock_provider_cls.return_value = mock_provider
            mock_provider.list_datasources.return_value = []

            datasets = get_available_datasets()

            assert datasets == []

    def test_handles_config_provider_error(self):
        """
        Test: Gracefully handles ConfigProvider errors.

        Purpose: CLI doesn't crash if config provider fails.
        """
        with patch("mobility_datasets.cli.main.ConfigProvider") as mock_provider_cls:
            mock_instance = Mock()
            mock_instance.list_datasources.side_effect = FileNotFoundError("Config error")
            mock_provider_cls.return_value = mock_instance

            with pytest.raises(FileNotFoundError):
                get_available_datasets()


class TestCliRootCommand:
    """Test suite for root 'cli' command."""

    def test_cli_displays_help(self):
        """
        Test: Root CLI command displays help text.

        Purpose: Verify basic CLI structure is valid.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Mobility Datasets" in result.output
        assert "autonomous driving datasets" in result.output

    def test_cli_shows_available_subcommands(self):
        """
        Test: Help shows available subcommands.

        Purpose: Users can discover available commands.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "download" in result.output
        assert "info" in result.output


class TestDownloadCommand:
    """Test suite for 'download' command."""

    def test_download_requires_dataset_name(self):
        """
        Test: Download command requires a dataset name argument.

        Purpose: Clear error if user forgets dataset name.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ["download"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "DATASET_NAME" in result.output

    def test_download_validates_dataset_choice(self):
        """
        Test: Download rejects invalid dataset names.

        Purpose: Fail fast with helpful error for typos.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti", "nuscenes"]

            runner = CliRunner()
            result = runner.invoke(cli, ["download", "invalid_dataset"])

            assert result.exit_code != 0
            assert "Invalid value" in result.output or "choice" in result.output

    def test_download_accepts_valid_dataset(self):
        """
        Test: Download accepts valid dataset name.

        Purpose: Valid input is processed without rejection.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader

                # Mock config with collections
                mock_config = Mock()
                mock_config.collections = [Mock(id="raw_data")]
                mock_downloader.config = mock_config

                # Mock download method
                mock_downloader.download = Mock()
                mock_downloader.data_dir = Path("/data/kitti")

                runner = CliRunner()
                result = runner.invoke(cli, ["download", "kitti"])

                assert result.exit_code == 0

    def test_download_handles_case_insensitive_dataset(self):
        """
        Test: Dataset name is case-insensitive.

        Purpose: User can type 'KITTI' or 'kitti' interchangeably.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader
                mock_config = Mock()
                mock_config.collections = [Mock(id="raw_data")]
                mock_downloader.config = mock_config
                mock_downloader.download = Mock()
                mock_downloader.data_dir = Path("/data/kitti")

                runner = CliRunner()
                result = runner.invoke(cli, ["download", "KITTI"])

                # Should be converted to lowercase and work
                assert result.exit_code == 0

    def test_download_with_collection_option(self):
        """
        Test: Collection option filters which collections to download.

        Purpose: Users can specify specific collections.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader

                # Mock config with multiple collections
                mock_config = Mock()
                mock_config.collections = [
                    Mock(id="raw_data"),
                    Mock(id="synced_data"),
                ]
                mock_downloader.config = mock_config
                mock_downloader.download = Mock()
                mock_downloader.data_dir = Path("/data/kitti")

                runner = CliRunner()
                result = runner.invoke(
                    cli,
                    [
                        "download",
                        "kitti",
                        "--collection",
                        "raw_data",
                    ],
                )

                assert result.exit_code == 0
                # Verify only specified collection was downloaded
                mock_downloader.download.assert_called_once()
                call_kwargs = mock_downloader.download.call_args[1]
                assert call_kwargs["collection_id"] == "raw_data"

    def test_download_with_invalid_collection(self):
        """
        Test: Invalid collection name is rejected.

        Purpose: Clear error for non-existent collections.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader
                mock_config = Mock()
                mock_config.collections = [Mock(id="raw_data")]
                mock_downloader.config = mock_config

                runner = CliRunner()
                result = runner.invoke(
                    cli,
                    [
                        "download",
                        "kitti",
                        "--collection",
                        "nonexistent",
                    ],
                )

                assert result.exit_code != 0
                assert "not found" in result.output

    def test_download_with_sessions_option(self):
        """
        Test: Sessions option allows filtering by session IDs.

        Purpose: Users can download specific sessions.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader
                mock_config = Mock()
                mock_config.collections = [Mock(id="raw_data")]
                mock_downloader.config = mock_config
                mock_downloader.download = Mock()
                mock_downloader.data_dir = Path("/data/kitti")

                runner = CliRunner()
                result = runner.invoke(
                    cli,
                    [
                        "download",
                        "kitti",
                        "--sessions",
                        "session_1,session_2",
                    ],
                )

                assert result.exit_code == 0
                call_kwargs = mock_downloader.download.call_args[1]
                assert call_kwargs["sessions"] == ["session_1", "session_2"]

    def test_download_with_keep_zip_flag(self):
        """
        Test: Keep-zip flag is passed to downloader.

        Purpose: Users can preserve ZIP archives after extraction.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader
                mock_config = Mock()
                mock_config.collections = [Mock(id="raw_data")]
                mock_downloader.config = mock_config
                mock_downloader.download = Mock()
                mock_downloader.data_dir = Path("/data/kitti")

                runner = CliRunner()
                result = runner.invoke(
                    cli,
                    [
                        "download",
                        "kitti",
                        "--keep-zip",
                    ],
                )

                assert result.exit_code == 0
                call_kwargs = mock_downloader.download.call_args[1]
                assert call_kwargs["keep_zip"] is True

    def test_download_with_data_dir_option(self):
        """
        Test: Custom data directory is accepted.

        Purpose: Users can specify custom download location.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader
                mock_config = Mock()
                mock_config.collections = [Mock(id="raw_data")]
                mock_downloader.config = mock_config
                mock_downloader.download = Mock()
                mock_downloader.data_dir = Path("/custom/path/data/kitti")

                runner = CliRunner()
                custom_dir = "/custom/path/data"
                result = runner.invoke(
                    cli,
                    [
                        "download",
                        "kitti",
                        "--data-dir",
                        custom_dir,
                    ],
                )

                assert result.exit_code == 0
                # Verify DatasetDownloader was created with custom directory
                call_kwargs = mock_downloader_cls.call_args[1]
                assert call_kwargs["data_dir"] == custom_dir

    def test_download_with_estimate_only(self):
        """
        Test: Estimate-only flag shows size without downloading.

        Purpose: Users can preview download size before committing.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader
                mock_config = Mock()
                mock_config.collections = [Mock(id="raw_data")]
                mock_downloader.config = mock_config

                # Mock get_download_size
                mock_downloader.get_download_size.return_value = {
                    "total_readable": "50 GB",
                    "sessions_count": 5,
                    "parts": {"oxts": 10_000_000_000},
                }

                runner = CliRunner()
                result = runner.invoke(
                    cli,
                    [
                        "download",
                        "kitti",
                        "--estimate-only",
                    ],
                )

                assert result.exit_code == 0
                assert "50 GB" in result.output
                # Should NOT call download when estimating
                mock_downloader.download.assert_not_called()

    def test_download_handles_file_not_found(self):
        """
        Test: FileNotFoundError is caught and reported.

        Purpose: Clear error if config file is missing.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader_cls.side_effect = FileNotFoundError("Config not found")

                runner = CliRunner()
                result = runner.invoke(cli, ["download", "kitti"])

                assert result.exit_code != 0
                assert "not found" in result.output.lower()

    def test_download_handles_value_error(self):
        """
        Test: ValueError is caught and reported.

        Purpose: Invalid configuration is caught early.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader_cls.side_effect = ValueError("Invalid config")

                runner = CliRunner()
                result = runner.invoke(cli, ["download", "kitti"])

                assert result.exit_code != 0
                assert "Invalid" in result.output

    def test_download_handles_generic_exception(self):
        """
        Test: Generic exceptions are caught and reported.

        Purpose: No uncaught exceptions reach user.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader_cls.side_effect = RuntimeError("Unexpected error")

                runner = CliRunner()
                result = runner.invoke(cli, ["download", "kitti"])

                assert result.exit_code != 0
                assert "Download failed" in result.output or "error" in result.output.lower()

    def test_download_shows_success_message(self):
        """
        Test: Successful download shows completion message.

        Purpose: Users know when download is done.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader
                mock_config = Mock()
                mock_config.collections = [Mock(id="raw_data")]
                mock_downloader.config = mock_config
                mock_downloader.download = Mock()
                mock_downloader.data_dir = Path("/data/kitti")

                runner = CliRunner()
                result = runner.invoke(cli, ["download", "kitti"])

                assert result.exit_code == 0
                assert "complete" in result.output.lower()


class TestInfoCommand:
    """Test suite for 'info' command."""

    def test_info_requires_dataset_name(self):
        """
        Test: Info command requires dataset name argument.

        Purpose: Clear error if dataset is missing.
        """
        runner = CliRunner()
        result = runner.invoke(cli, ["info"])

        assert result.exit_code != 0

    def test_info_validates_dataset_choice(self):
        """
        Test: Invalid dataset is rejected.

        Purpose: Fail fast for typos.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            runner = CliRunner()
            result = runner.invoke(cli, ["info", "invalid"])

            assert result.exit_code != 0

    def test_info_accepts_valid_dataset(self):
        """
        Test: Valid dataset is accepted.

        Purpose: Info command runs for valid datasets.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader

                # Mock config
                mock_collection = Mock(id="raw_data", sessions=[])
                mock_config = Mock()
                mock_config.metadata.name = "KITTI"
                mock_config.metadata.description = "Vision meets Robotics"
                mock_config.metadata.license.name = "CC BY-NC-SA 3.0"
                mock_config.collections = [mock_collection]
                mock_config.get_collection_by_id = Mock(return_value=mock_collection)
                mock_downloader.config = mock_config

                # Mock get_download_size
                mock_downloader.get_download_size.return_value = {
                    "total_readable": "50 GB",
                }

                runner = CliRunner()
                result = runner.invoke(cli, ["info", "kitti"])

                assert result.exit_code == 0

    def test_info_shows_dataset_metadata(self):
        """
        Test: Info displays dataset name and description.

        Purpose: Users see basic dataset information.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader

                mock_collection = Mock(id="raw_data", sessions=[])
                mock_config = Mock()
                mock_config.metadata.name = "KITTI Vision Benchmark"
                mock_config.metadata.description = "Vision meets Robotics"
                mock_config.metadata.license.name = "CC BY-NC-SA 3.0"
                mock_config.collections = [mock_collection]
                mock_config.get_collection_by_id = Mock(return_value=mock_collection)
                mock_downloader.config = mock_config
                mock_downloader.get_download_size.return_value = {"total_readable": "50 GB"}

                runner = CliRunner()
                result = runner.invoke(cli, ["info", "kitti"])

                assert result.exit_code == 0
                assert "KITTI Vision Benchmark" in result.output
                assert "Vision meets Robotics" in result.output

    def test_info_shows_collections(self):
        """
        Test: Info lists available collections.

        Purpose: Users see what collections are available.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader

                mock_raw_data = Mock()
                mock_raw_data.id = "raw_data"
                mock_raw_data.sessions = [Mock(id="2011_09_26_drive_0001")]

                mock_synced = Mock()
                mock_synced.id = "synced_data"
                mock_synced.sessions = []

                mock_config = Mock()
                mock_config.metadata.name = "KITTI"
                mock_config.metadata.description = "Dataset"
                mock_config.metadata.license.name = "License"
                mock_config.collections = [mock_raw_data, mock_synced]

                def get_coll_by_id(coll_id):
                    for c in [mock_raw_data, mock_synced]:
                        if c.id == coll_id:
                            return c
                    return None

                mock_config.get_collection_by_id = Mock(side_effect=get_coll_by_id)
                mock_downloader.config = mock_config
                mock_downloader.get_download_size.return_value = {"total_readable": "50 GB"}

                runner = CliRunner()
                result = runner.invoke(cli, ["info", "kitti"])

                assert result.exit_code == 0
                assert "raw_data" in result.output
                assert "synced_data" in result.output

    def test_info_with_collection_option(self):
        """
        Test: Collection option filters which collection to show.

        Purpose: Users can get info about specific collections.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader

                mock_raw_data = Mock()
                mock_raw_data.id = "raw_data"
                mock_raw_data.sessions = []

                mock_config = Mock()
                mock_config.metadata.name = "KITTI"
                mock_config.metadata.description = "Dataset"
                mock_config.metadata.license.name = "License"
                mock_config.collections = [mock_raw_data]
                mock_config.get_collection_by_id = Mock(return_value=mock_raw_data)
                mock_downloader.config = mock_config
                mock_downloader.get_download_size.return_value = {"total_readable": "50 GB"}

                runner = CliRunner()
                result = runner.invoke(cli, ["info", "kitti", "--collection", "raw_data"])

                assert result.exit_code == 0
                assert "raw_data" in result.output

    def test_info_with_invalid_collection(self):
        """
        Test: Invalid collection name is rejected.

        Purpose: Clear error for non-existent collections.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader

                mock_config = Mock()
                mock_config.metadata.name = "KITTI"
                mock_config.metadata.description = "Dataset"
                mock_config.metadata.license.name = "License"
                mock_config.collections = [Mock(id="raw_data")]
                mock_config.collection_by_id = Mock(return_value=None)
                mock_downloader.config = mock_config

                runner = CliRunner()
                result = runner.invoke(cli, ["info", "kitti", "--collection", "nonexistent"])

                assert result.exit_code != 0
                assert "not found" in result.output

    def test_info_with_verify_flag(self):
        """
        Test: Verify flag checks file availability.

        Purpose: Users can verify files are actually available.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader

                mock_collection = Mock(id="raw_data", sessions=[])
                mock_config = Mock()
                mock_config.metadata.name = "KITTI"
                mock_config.metadata.description = "Dataset"
                mock_config.metadata.license.name = "License"
                mock_config.collections = [mock_collection]
                mock_config.get_collection_by_id = Mock(return_value=mock_collection)
                mock_downloader.config = mock_config
                mock_downloader.get_download_size.return_value = {"total_readable": "50 GB"}
                mock_downloader.health_check.return_value = {
                    "file1": True,
                    "file2": True,
                }

                runner = CliRunner()
                result = runner.invoke(cli, ["info", "kitti", "--verify"])

                assert result.exit_code == 0
                mock_downloader.health_check.assert_called_once()

    def test_info_verify_shows_availability_summary(self):
        """
        Test: Verify shows how many files are available.

        Purpose: Users see availability status.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader = Mock()
                mock_downloader_cls.return_value = mock_downloader

                mock_collection = Mock(id="raw_data", sessions=[])
                mock_config = Mock()
                mock_config.metadata.name = "KITTI"
                mock_config.metadata.description = "Dataset"
                mock_config.metadata.license.name = "License"
                mock_config.collections = [mock_collection]
                mock_config.get_collection_by_id = Mock(return_value=mock_collection)
                mock_downloader.config = mock_config
                mock_downloader.get_download_size.return_value = {"total_readable": "50 GB"}
                mock_downloader.health_check.return_value = {
                    "file1": True,
                    "file2": True,
                    "file3": False,
                }

                runner = CliRunner()
                result = runner.invoke(cli, ["info", "kitti", "--verify"])

                assert result.exit_code == 0
                assert "2/3" in result.output

    def test_info_handles_exception(self):
        """
        Test: Exceptions are caught and reported.

        Purpose: No crashes, helpful error messages.
        """
        with patch("mobility_datasets.cli.main.get_available_datasets") as mock_get:
            mock_get.return_value = ["kitti"]

            with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
                mock_downloader_cls.side_effect = Exception("Info failed")

                runner = CliRunner()
                result = runner.invoke(cli, ["info", "kitti"])

                assert result.exit_code != 0
                assert "failed" in result.output.lower()
