"""Integration tests for CLI commands with real file operations.

Module: tests/integration/cli/test_cli_integration.py
Purpose: Test CLI with real (mini) YAML configs and actual downloader interactions
Layer: Integration tests (real files, mock only network)

Tests cover:
- Complete download workflow via CLI
- Configuration loading and validation
- Collection/session selection from real configs
- Size estimation with real config data
- Health check with mocked network
- Error handling with real file structures
"""

from unittest.mock import Mock, patch

import pytest
import yaml
from click.testing import CliRunner
from mobility_datasets.cli.main import cli


@pytest.fixture
def mini_kitti_config(tmp_path):
    """Create a minimal KITTI configuration for testing.

    Returns a valid YAML config with realistic structure but minimal data.
    """
    config = {
        "metadata": {
            "name": "KITTI Dataset",
            "description": "Vision meets Robotics",
            "license": {
                "name": "CC BY-NC-SA 3.0",
                "url": "https://example.com/license",
            },
        },
        "collections": [
            {
                "id": "raw_data",
                "name": "Raw Data",
                "description": "Raw camera images and sensor data",
                "sessions": [
                    {
                        "id": "2011_09_26_drive_0001",
                        "name": "Urban drive 1",
                        "date": "2011-09-26",
                        "location_type": "urban",
                        "parts": [
                            {
                                "id": "oxts",
                                "name": "GPS/IMU Data",
                                "download": {
                                    "url": "https://s3.example.com/oxts_0001.zip",
                                    "filename": "oxts_0001.zip",
                                    "size_bytes": 100000000,
                                    "md5": "abc123",
                                    "format": "zip",
                                },
                                "optional": False,
                            }
                        ],
                    }
                ],
            },
            {
                "id": "synced_data",
                "name": "Synced Data",
                "description": "Synchronized and rectified data",
                "sessions": [],
            },
        ],
    }

    # Save to temp file
    config_file = tmp_path / "kitti.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)

    return config_file, config


@pytest.fixture
def mini_nuscenes_config(tmp_path):
    """Create a minimal nuScenes configuration for testing."""
    config = {
        "metadata": {
            "name": "nuScenes",
            "description": "Large-scale 3D object detection dataset",
            "license": {
                "name": "CC BY-NC-SA 4.0",
                "url": "https://example.com/license",
            },
        },
        "collections": [
            {
                "id": "v1.0-mini",
                "name": "Mini Version",
                "description": "Small version for quick testing",
                "sessions": [
                    {
                        "id": "scene-0001",
                        "name": "Scene 1",
                        "date": "2018-08-01",
                        "location_type": "boston",
                        "parts": [
                            {
                                "id": "metadata",
                                "name": "Metadata",
                                "download": {
                                    "url": "https://www.nuscenes.org/public/v1.0-mini/metadata.tgz",
                                    "filename": "metadata.tgz",
                                    "size_bytes": 50000000,
                                    "md5": "def456",
                                    "format": "tar",
                                },
                                "optional": False,
                            }
                        ],
                    }
                ],
            }
        ],
    }

    config_file = tmp_path / "nuscenes.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)

    return config_file, config


class TestDownloadCommandIntegration:
    """Integration tests for download command with real configs."""

    def test_download_with_real_kitti_config(self, mini_kitti_config, tmp_path):
        """
        Test: Download command works with real KITTI configuration.

        Purpose: Verify complete download pipeline with actual config file.
        """
        config_file, config = mini_kitti_config

        # Mock only the downloader's download method
        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader = Mock()
            mock_downloader_cls.return_value = mock_downloader

            # Set up config from the file
            from mobility_datasets.config.provider import Collection, DownloadInfo, Part, Session

            collections = []
            for coll_data in config["collections"]:
                sessions = []
                for sess_data in coll_data.get("sessions", []):
                    parts = []
                    for part_data in sess_data.get("parts", []):
                        download = DownloadInfo(**part_data["download"])
                        part = Part(**{**part_data, "download": download})
                        parts.append(part)
                    session = Session(**{**sess_data, "parts": parts})
                    sessions.append(session)
                collection = Collection(**{**coll_data, "sessions": sessions})
                collections.append(collection)

            mock_config = Mock()
            mock_config.collections = collections
            mock_downloader.config = mock_config
            mock_downloader.download = Mock()
            mock_downloader.data_dir = tmp_path / "kitti"

            runner = CliRunner()
            result = runner.invoke(cli, ["dataset", "download", "kitti"])

            assert result.exit_code == 0
            assert "complete" in result.output.lower()

    def test_download_filters_by_collection(self, mini_kitti_config, tmp_path):
        """
        Test: Download only selected collection.

        Purpose: Users can specify which collection to download.
        """
        config_file, config = mini_kitti_config

        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader = Mock()
            mock_downloader_cls.return_value = mock_downloader

            # Set up config
            from mobility_datasets.config.provider import Collection, DownloadInfo, Part, Session

            collections = []
            for coll_data in config["collections"]:
                sessions = []
                for sess_data in coll_data.get("sessions", []):
                    parts = []
                    for part_data in sess_data.get("parts", []):
                        download = DownloadInfo(**part_data["download"])
                        part = Part(**{**part_data, "download": download})
                        parts.append(part)
                    session = Session(**{**sess_data, "parts": parts})
                    sessions.append(session)
                collection = Collection(**{**coll_data, "sessions": sessions})
                collections.append(collection)

            mock_config = Mock()
            mock_config.collections = collections
            mock_downloader.config = mock_config
            mock_downloader.download = Mock()
            mock_downloader.data_dir = tmp_path / "kitti"

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "dataset",
                    "download",
                    "kitti",
                    "--collection",
                    "raw_data",
                ],
            )

            assert result.exit_code == 0
            # Verify correct collection was passed
            mock_downloader.download.assert_called_once()
            call_args = mock_downloader.download.call_args[1]
            assert call_args["collection_id"] == "raw_data"

    def test_download_filters_by_sessions(self, mini_kitti_config, tmp_path):
        """
        Test: Download specific sessions.

        Purpose: Users can filter by session IDs.
        """
        config_file, config = mini_kitti_config

        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader = Mock()
            mock_downloader_cls.return_value = mock_downloader

            from mobility_datasets.config.provider import Collection, DownloadInfo, Part, Session

            collections = []
            for coll_data in config["collections"]:
                sessions = []
                for sess_data in coll_data.get("sessions", []):
                    parts = []
                    for part_data in sess_data.get("parts", []):
                        download = DownloadInfo(**part_data["download"])
                        part = Part(**{**part_data, "download": download})
                        parts.append(part)
                    session = Session(**{**sess_data, "parts": parts})
                    sessions.append(session)
                collection = Collection(**{**coll_data, "sessions": sessions})
                collections.append(collection)

            mock_config = Mock()
            mock_config.collections = collections
            mock_downloader.config = mock_config
            mock_downloader.download = Mock()
            mock_downloader.data_dir = tmp_path / "kitti"

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "dataset",
                    "download",
                    "kitti",
                    "--sessions",
                    "2011_09_26_drive_0001",
                ],
            )

            assert result.exit_code == 0
            call_args = mock_downloader.download.call_args[1]
            assert call_args["sessions"] == ["2011_09_26_drive_0001"]

    def test_download_estimate_shows_realistic_sizes(self, mini_kitti_config, tmp_path):
        """
        Test: Size estimation shows realistic sizes from config.

        Purpose: Users get accurate download size previews.
        """
        config_file, config = mini_kitti_config

        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader = Mock()
            mock_downloader_cls.return_value = mock_downloader

            from mobility_datasets.config.provider import Collection, DownloadInfo, Part, Session

            collections = []
            for coll_data in config["collections"]:
                sessions = []
                for sess_data in coll_data.get("sessions", []):
                    parts = []
                    for part_data in sess_data.get("parts", []):
                        download = DownloadInfo(**part_data["download"])
                        part = Part(**{**part_data, "download": download})
                        parts.append(part)
                    session = Session(**{**sess_data, "parts": parts})
                    sessions.append(session)
                collection = Collection(**{**coll_data, "sessions": sessions})
                collections.append(collection)

            mock_config = Mock()
            mock_config.collections = collections
            mock_downloader.config = mock_config
            mock_downloader.get_download_size.return_value = {
                "total_readable": "100 MB",
                "sessions_count": 1,
                "parts": {"oxts": 100_000_000},
            }

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "dataset",
                    "download",
                    "kitti",
                    "--estimate-only",
                ],
            )

            assert result.exit_code == 0
            assert "100 MB" in result.output
            # Should not call download
            mock_downloader.download.assert_not_called()

    def test_download_with_all_options_together(self, mini_kitti_config, tmp_path):
        """
        Test: All download options work together.

        Purpose: Complex real-world usage patterns work correctly.
        """
        config_file, config = mini_kitti_config
        custom_dir = tmp_path / "custom_download"

        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader = Mock()
            mock_downloader_cls.return_value = mock_downloader

            from mobility_datasets.config.provider import Collection, DownloadInfo, Part, Session

            collections = []
            for coll_data in config["collections"]:
                sessions = []
                for sess_data in coll_data.get("sessions", []):
                    parts = []
                    for part_data in sess_data.get("parts", []):
                        download = DownloadInfo(**part_data["download"])
                        part = Part(**{**part_data, "download": download})
                        parts.append(part)
                    session = Session(**{**sess_data, "parts": parts})
                    sessions.append(session)
                collection = Collection(**{**coll_data, "sessions": sessions})
                collections.append(collection)

            mock_config = Mock()
            mock_config.collections = collections
            mock_downloader.config = mock_config
            mock_downloader.download = Mock()
            mock_downloader.data_dir = custom_dir

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "dataset",
                    "download",
                    "kitti",
                    "--collection",
                    "raw_data",
                    "--sessions",
                    "2011_09_26_drive_0001",
                    "--keep-zip",
                    "--data-dir",
                    str(custom_dir),
                ],
            )

            assert result.exit_code == 0
            # Verify all options were passed
            mock_downloader_cls.assert_called_once()
            init_args = mock_downloader_cls.call_args[1]
            assert init_args["data_dir"] == str(custom_dir)

            download_args = mock_downloader.download.call_args[1]
            assert download_args["collection_id"] == "raw_data"
            assert download_args["sessions"] == ["2011_09_26_drive_0001"]
            assert download_args["keep_zip"] is True


class TestHealthCheckIntegration:
    """Integration tests for health-check command."""

    def test_health_check_with_real_config(self, mini_kitti_config):
        """
        Test: Health check works with real config.

        Purpose: Verify health check integration with actual configuration.
        """
        config_file, config = mini_kitti_config

        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader = Mock()
            mock_downloader_cls.return_value = mock_downloader

            # Mock health check with realistic results
            mock_downloader.health_check.return_value = {
                "oxts_0001": True,
                "calib_0001": True,
                "images_0001": False,  # One unavailable
            }

            runner = CliRunner()
            result = runner.invoke(cli, ["dataset", "health-check", "kitti"])

            assert result.exit_code == 0
            assert "2/3" in result.output
            assert "images_0001" in result.output

    def test_health_check_with_timeout_option(self, mini_kitti_config):
        """
        Test: Health check accepts timeout option.

        Purpose: Users can customize timeout for slow connections.
        """
        config_file, config = mini_kitti_config

        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader = Mock()
            mock_downloader_cls.return_value = mock_downloader
            mock_downloader.health_check.return_value = {}

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "dataset",
                    "health-check",
                    "kitti",
                    "--timeout",
                    "30",
                ],
            )

            assert result.exit_code == 0

    def test_health_check_all_available(self, mini_kitti_config):
        """
        Test: Health check shows success when all files available.

        Purpose: Users see positive feedback for healthy dataset.
        """
        config_file, config = mini_kitti_config

        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader = Mock()
            mock_downloader_cls.return_value = mock_downloader
            mock_downloader.health_check.return_value = {
                "file1": True,
                "file2": True,
                "file3": True,
            }

            runner = CliRunner()
            result = runner.invoke(cli, ["dataset", "health-check", "kitti"])

            assert result.exit_code == 0
            assert "3/3" in result.output
            assert "All files available" in result.output


class TestListDatasetsIntegration:
    """Integration tests for list-datasets command."""

    def test_list_datasets_shows_all_configs(self, mini_kitti_config, mini_nuscenes_config):
        """
        Test: List-datasets shows all configured datasets.

        Purpose: Users see all available datasets with metadata.
        """
        with patch("mobility_datasets.cli.main.ConfigProvider") as mock_provider_cls:
            mock_provider = Mock()
            mock_provider_cls.return_value = mock_provider
            mock_provider.list_datasources.return_value = ["kitti", "nuscenes"]

            # Create realistic config mocks
            from mobility_datasets.config.provider import (
                DatasetConfig,
            )

            kitti_config = {
                "metadata": {
                    "name": "KITTI Dataset",
                    "description": "Vision meets Robotics",
                    "license": {"name": "CC BY-NC-SA 3.0"},
                },
                "collections": [],
            }

            nuscenes_config = {
                "metadata": {
                    "name": "nuScenes",
                    "description": "Large-scale 3D object detection",
                    "license": {"name": "CC BY-NC-SA 4.0"},
                },
                "collections": [],
            }

            kitti_obj = DatasetConfig(**kitti_config)
            nuscenes_obj = DatasetConfig(**nuscenes_config)

            mock_provider.get_from_datasource.side_effect = lambda ds: (
                kitti_obj if ds == "kitti" else nuscenes_obj
            )

            runner = CliRunner()
            result = runner.invoke(cli, ["dataset", "list-datasets"])

            assert result.exit_code == 0
            assert "KITTI" in result.output
            assert "nuScenes" in result.output
            assert "CC BY-NC-SA" in result.output


class TestCliErrorHandling:
    """Integration tests for CLI error handling."""

    def test_invalid_collection_with_real_config(self, mini_kitti_config):
        """
        Test: Invalid collection is rejected with real config.

        Purpose: Clear error messages when user specifies wrong collection.
        """
        config_file, config = mini_kitti_config

        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader = Mock()
            mock_downloader_cls.return_value = mock_downloader

            from mobility_datasets.config.provider import Collection, DownloadInfo, Part, Session

            collections = []
            for coll_data in config["collections"]:
                sessions = []
                for sess_data in coll_data.get("sessions", []):
                    parts = []
                    for part_data in sess_data.get("parts", []):
                        download = DownloadInfo(**part_data["download"])
                        part = Part(**{**part_data, "download": download})
                        parts.append(part)
                    session = Session(**{**sess_data, "parts": parts})
                    sessions.append(session)
                collection = Collection(**{**coll_data, "sessions": sessions})
                collections.append(collection)

            mock_config = Mock()
            mock_config.collections = collections
            mock_downloader.config = mock_config

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "dataset",
                    "download",
                    "kitti",
                    "--collection",
                    "nonexistent_collection",
                ],
            )

            assert result.exit_code != 0
            assert "not found" in result.output

    def test_cli_with_missing_config_file(self):
        """
        Test: Clear error when dataset config is missing.

        Purpose: User gets helpful message about missing configuration.
        """
        with patch("mobility_datasets.cli.main.DatasetDownloader") as mock_downloader_cls:
            mock_downloader_cls.side_effect = FileNotFoundError("Config file not found: kitti.yaml")

            runner = CliRunner()
            result = runner.invoke(cli, ["dataset", "download", "kitti"])

            assert result.exit_code != 0
            assert "not found" in result.output.lower()
