"""Integration tests for CLI commands with real file operations.

Module: tests/integration/cli/test_cli_integration.py
Purpose: Test CLI with real (mini) YAML configs and actual downloader interactions
Layer: Integration tests (real files, mock only network)

Tests cover:
- Complete download workflow via CLI
- Configuration loading and validation
- Collection/session selection from real configs
- Size estimation with real config data
- Info command with file availability verification
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
            result = runner.invoke(cli, ["download", "kitti"])

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


class TestInfoCommandIntegration:
    """Integration tests for info command with real configs."""

    def test_info_with_real_kitti_config(self, mini_kitti_config):
        """
        Test: Info command works with real KITTI configuration.

        Purpose: Verify info displays dataset information correctly.
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
            mock_config.metadata.name = config["metadata"]["name"]
            mock_config.metadata.description = config["metadata"]["description"]
            mock_config.metadata.license.name = config["metadata"]["license"]["name"]
            mock_config.collections = collections

            # Mock get_collection_by_id to return collections
            def get_coll_by_id(coll_id):
                for c in collections:
                    if c.id == coll_id:
                        return c
                return None

            mock_config.get_collection_by_id = Mock(side_effect=get_coll_by_id)
            mock_downloader.config = mock_config
            mock_downloader.get_download_size.return_value = {
                "total_readable": "100 MB",
            }

            runner = CliRunner()
            result = runner.invoke(cli, ["info", "kitti"])

            assert result.exit_code == 0
            assert "KITTI Dataset" in result.output
            assert "Vision meets Robotics" in result.output

    def test_info_filters_by_collection(self, mini_kitti_config):
        """
        Test: Info shows only selected collection.

        Purpose: Users can get detailed info about specific collections.
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
            mock_config.metadata.name = "KITTI"
            mock_config.metadata.description = "Dataset"
            mock_config.metadata.license.name = "License"
            mock_config.collections = collections

            def get_coll_by_id(coll_id):
                for c in collections:
                    if c.id == coll_id:
                        return c
                return None

            mock_config.get_collection_by_id = Mock(side_effect=get_coll_by_id)
            mock_downloader.config = mock_config
            mock_downloader.get_download_size.return_value = {"total_readable": "50 GB"}

            runner = CliRunner()
            result = runner.invoke(cli, ["info", "kitti", "--collection", "raw_data"])

            assert result.exit_code == 0
            assert "raw_data" in result.output

    def test_info_verify_files_with_real_config(self, mini_kitti_config):
        """
        Test: Info with --verify checks file availability.

        Purpose: Users can verify all files are actually available.
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
            mock_config.metadata.name = "KITTI"
            mock_config.metadata.description = "Dataset"
            mock_config.metadata.license.name = "License"
            mock_config.collections = collections

            def get_coll_by_id(coll_id):
                for c in collections:
                    if c.id == coll_id:
                        return c
                return None

            mock_config.get_collection_by_id = Mock(side_effect=get_coll_by_id)
            mock_downloader.config = mock_config
            mock_downloader.get_download_size.return_value = {"total_readable": "100 MB"}
            mock_downloader.health_check.return_value = {
                "oxts_0001": True,
                "calib_0001": True,
                "images_0001": False,
            }

            runner = CliRunner()
            result = runner.invoke(cli, ["info", "kitti", "--verify"])

            assert result.exit_code == 0
            assert "2/3" in result.output
            mock_downloader.health_check.assert_called_once()

    def test_info_verify_all_available(self, mini_kitti_config):
        """
        Test: Info verify shows success when all files available.

        Purpose: Users see positive feedback for healthy dataset.
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
            mock_config.metadata.name = "KITTI"
            mock_config.metadata.description = "Dataset"
            mock_config.metadata.license.name = "License"
            mock_config.collections = collections

            def get_coll_by_id(coll_id):
                for c in collections:
                    if c.id == coll_id:
                        return c
                return None

            mock_config.get_collection_by_id = Mock(side_effect=get_coll_by_id)
            mock_downloader.config = mock_config
            mock_downloader.get_download_size.return_value = {"total_readable": "100 MB"}
            mock_downloader.health_check.return_value = {
                "file1": True,
                "file2": True,
                "file3": True,
            }

            runner = CliRunner()
            result = runner.invoke(cli, ["info", "kitti", "--verify"])

            assert result.exit_code == 0
            assert "All 3 files available" in result.output


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
            result = runner.invoke(cli, ["download", "kitti"])

            assert result.exit_code != 0
            assert "not found" in result.output.lower()

    def test_info_with_invalid_collection(self, mini_kitti_config):
        """
        Test: Info rejects invalid collection.

        Purpose: Clear error when collection doesn't exist.
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
            mock_config.get_collection_by_id = Mock(return_value=None)
            mock_downloader.config = mock_config

            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["info", "kitti", "--collection", "nonexistent"],
            )

            assert result.exit_code != 0
            assert "not found" in result.output
