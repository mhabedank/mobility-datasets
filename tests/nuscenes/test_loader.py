# tests/nuscenes/test_loader.py
from unittest.mock import MagicMock, patch

import pytest
from mobility_datasets.nuscenes.loader import NuScenesDownloader

from tests.base_downloader_test import BaseDownloaderTestCase


class TestNuScenesDownloaderInit(BaseDownloaderTestCase):
    """Test NuScenesDownloader initialization."""

    @pytest.fixture
    def downloader(self, nuscenes_downloader_mini):
        """Use mini version for init tests."""
        return nuscenes_downloader_mini

    def test_init_default_version(self, tmp_path):
        """Test that default version is 'mini'."""
        downloader = NuScenesDownloader(data_dir=str(tmp_path))
        assert downloader.version == "mini"

    @pytest.mark.parametrize("version", ["mini", "trainval", "test"])
    def test_init_custom_versions(self, tmp_path, version):
        """Test initialization with all supported versions."""
        downloader = NuScenesDownloader(data_dir=str(tmp_path), version=version)
        assert downloader.version == version
        assert len(downloader.AVAILABLE_FILES) > 0

    def test_init_invalid_version(self, tmp_path):
        """Test that invalid version raises ValueError."""
        with pytest.raises(ValueError, match="Invalid version"):
            NuScenesDownloader(data_dir=str(tmp_path), version="invalid")

    def test_available_files_mini(self, nuscenes_downloader_mini):
        """Test that mini version has correct available files."""
        expected_components = [
            "metadata",
            "lidar_keyframes",
            "lidar_sweeps",
            "cam_front",
            "cam_front_left",
            "cam_front_right",
            "cam_back",
            "cam_back_left",
            "cam_back_right",
            "radar_front",
            "radar_front_left",
            "radar_front_right",
            "radar_back_left",
            "radar_back_right",
        ]

        for component in expected_components:
            assert component in nuscenes_downloader_mini.AVAILABLE_FILES

    def test_available_files_trainval(self, nuscenes_downloader_trainval):
        """Test that trainval version has correct available files."""
        expected_components = [
            "metadata",
            "lidar_keyframes",
            "cam_front",
            "cam_front_left",
            "cam_front_right",
            "cam_back",
            "cam_back_left",
            "cam_back_right",
            "radar_front",
            "radar_front_left",
            "radar_front_right",
            "radar_back_left",
            "radar_back_right",
        ]

        for component in expected_components:
            assert component in nuscenes_downloader_trainval.AVAILABLE_FILES

    def test_available_files_test(self, nuscenes_downloader_test):
        """Test that test version only has metadata component."""
        assert "metadata" in nuscenes_downloader_test.AVAILABLE_FILES
        assert len(nuscenes_downloader_test.AVAILABLE_FILES) == 1


class TestNuScenesDownloaderDownload:
    """Test download functionality."""

    @pytest.fixture
    def downloader(self, nuscenes_downloader_mini):
        """Use mini version for download tests."""
        return nuscenes_downloader_mini

    @pytest.mark.parametrize(
        "components,expected_calls",
        [
            (["metadata"], 1),
            (["cam_front"], 1),
            (["metadata", "cam_front"], 2),
            (["metadata", "cam_front", "cam_back"], 3),
        ],
    )
    @patch("mobility_datasets.nuscenes.loader.requests.get")
    @patch("mobility_datasets.nuscenes.loader.tarfile.open")
    def test_download_components(
        self,
        mock_tarfile,
        mock_requests,
        components,
        expected_calls,
        downloader,
        mock_http_response,
    ):
        """Test downloading various component combinations.

        This parametrized test verifies that the correct number of HTTP requests
        are made for different sets of components.
        """
        mock_requests.return_value = mock_http_response
        mock_tar_instance = MagicMock()
        mock_tarfile.return_value.__enter__ = MagicMock(return_value=mock_tar_instance)
        mock_tarfile.return_value.__exit__ = MagicMock(return_value=None)

        downloader.download(components)

        assert mock_requests.call_count == expected_calls, (
            f"Expected {expected_calls} download calls for components {components}, "
            f"got {mock_requests.call_count}"
        )

    @patch("mobility_datasets.nuscenes.loader.requests.get")
    @patch("mobility_datasets.nuscenes.loader.tarfile.open")
    def test_download_all(self, mock_tarfile, mock_requests, downloader, mock_http_response):
        """Test downloading all components for a version."""
        mock_requests.return_value = mock_http_response
        mock_tar_instance = MagicMock()
        mock_tarfile.return_value.__enter__ = MagicMock(return_value=mock_tar_instance)
        mock_tarfile.return_value.__exit__ = MagicMock(return_value=None)

        downloader.download_all()

        # Mini version should download 14 components
        assert mock_requests.call_count == 14


class TestNuScenesDownloaderArchiveHandling:
    """Test archive file handling."""

    @pytest.mark.parametrize(
        "keep_archive,should_exist",
        [
            (True, True),
            (False, False),
        ],
    )
    @patch("mobility_datasets.nuscenes.loader.requests.get")
    @patch("mobility_datasets.nuscenes.loader.tarfile.open")
    def test_archive_handling(
        self, mock_tarfile, mock_requests, keep_archive, should_exist, tmp_path, mock_http_response
    ):
        """Test archive file handling with different configurations.

        Parametrized test that verifies both keep_archive=True and False
        behaviors work correctly.
        """
        mock_requests.return_value = mock_http_response
        mock_tar_instance = MagicMock()
        mock_tarfile.return_value.__enter__ = MagicMock(return_value=mock_tar_instance)
        mock_tarfile.return_value.__exit__ = MagicMock(return_value=None)

        # Create a fake archive file
        archive_path = tmp_path / "v1.0-mini.tgz"
        archive_path.write_text("fake archive")

        # Create downloader with tmp_path
        downloader = NuScenesDownloader(data_dir=str(tmp_path), version="mini")
        downloader.download(["metadata"], keep_archive=keep_archive)

        assert archive_path.exists() == should_exist, (
            f"Archive should {'exist' if should_exist else 'not exist'} "
            f"when keep_archive={keep_archive}"
        )


class TestNuScenesDownloaderSkipExisting(BaseDownloaderTestCase):
    """Test handling of existing files."""

    @pytest.fixture
    def downloader(self, nuscenes_downloader_mini):
        """Use mini version for skip tests."""
        return nuscenes_downloader_mini

    @patch("mobility_datasets.nuscenes.loader.requests.get")
    @patch("mobility_datasets.nuscenes.loader.tarfile.open")
    def test_skip_existing_archive(self, mock_tarfile, mock_requests, tmp_path, capsys):
        """Test that existing archive files are skipped for download.

        When a tarball already exists, the downloader should skip the
        download step (requests.get should not be called).
        The extraction will still occur, but no new download happens.
        """
        # Mock tarfile context manager
        mock_tar_instance = MagicMock()
        mock_tarfile.return_value.__enter__ = MagicMock(return_value=mock_tar_instance)
        mock_tarfile.return_value.__exit__ = MagicMock(return_value=None)

        # Create existing archive file
        archive_path = tmp_path / "v1.0-mini.tgz"
        archive_path.write_text("fake archive")

        # Test
        downloader = NuScenesDownloader(data_dir=str(tmp_path), version="mini")
        downloader.download(["metadata"])

        # Verify no download was attempted (file already exists)
        mock_requests.assert_not_called()

        # Verify message was printed
        captured = capsys.readouterr()
        assert "already exists" in captured.out


class TestNuScenesDownloaderVersionSpecific(BaseDownloaderTestCase):
    """Test version-specific behavior."""

    @pytest.fixture
    def downloader(self, nuscenes_downloader_mini):
        """Use mini version (override in specific tests if needed)."""
        return nuscenes_downloader_mini

    @patch("mobility_datasets.nuscenes.loader.requests.get")
    @patch("mobility_datasets.nuscenes.loader.tarfile.open")
    def test_trainval_lidar_keyframes_multiple_files(
        self, mock_tarfile, mock_requests, nuscenes_downloader_trainval, mock_http_response
    ):
        """Test that trainval version downloads multiple lidar_keyframes files."""
        mock_requests.return_value = mock_http_response
        mock_tar_instance = MagicMock()
        mock_tarfile.return_value.__enter__ = MagicMock(return_value=mock_tar_instance)
        mock_tarfile.return_value.__exit__ = MagicMock(return_value=None)

        # Test
        nuscenes_downloader_trainval.download(["lidar_keyframes"])

        # trainval has 10 lidar_keyframes files
        assert mock_requests.call_count == 10

    def test_test_version_only_metadata(self, nuscenes_downloader_test):
        """Test that test version only has metadata component."""
        assert "metadata" in nuscenes_downloader_test.AVAILABLE_FILES
        assert len(nuscenes_downloader_test.AVAILABLE_FILES) == 1

    def test_all_versions_consistency(self, nuscenes_downloader_all_versions):
        """
        Parametrized test: Verify all versions are valid and accessible.

        This test runs once for each version (mini, trainval, test).
        """
        assert nuscenes_downloader_all_versions.version in ["mini", "trainval", "test"]
        assert "metadata" in nuscenes_downloader_all_versions.AVAILABLE_FILES


class TestNuScenesDownloaderIntegration:
    """Integration tests for nuScenes downloader."""

    @pytest.mark.integration
    def test_nuscenes_base_url_accessible(self):
        """
        Integration test: Verify nuScenes base URL is accessible.

        This test checks if the CloudFront base URL responds successfully.
        It performs a simple HEAD request to verify connectivity without
        downloading any data.

        The test will fail if:
        - CloudFront CDN is unreachable
        - Network connectivity is broken
        - The base URL has changed

        Notes
        -----
        This is a real integration test that requires internet connectivity.
        Run with: pytest -m integration
        """
        import requests

        downloader = NuScenesDownloader()
        base_url = downloader.BASE_URL

        try:
            # Simple HEAD request to base URL
            response = requests.head(base_url, timeout=10)

            # Base URL should be accessible
            assert response.status_code in [
                200,
                403,
            ], f"nuScenes base URL returned unexpected status: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Cannot reach nuScenes base URL {base_url}: {e}")

    @pytest.mark.integration
    def test_nuscenes_metadata_available_mini(self):
        """
        Integration test: Verify nuScenes mini metadata is available.

        Checks if the essential metadata file for the mini version exists
        on the CloudFront CDN.

        The test will fail if:
        - Metadata file returns HTTP 404
        - CDN is temporarily unavailable
        - File has been moved or deleted

        Notes
        -----
        This test focuses on essential files needed for minimal setup.
        Use this for quick sanity checks in CI/CD.
        """
        import requests

        downloader = NuScenesDownloader(version="mini")
        metadata_file = downloader.AVAILABLE_FILES["metadata"]
        url = downloader.BASE_URL + metadata_file

        try:
            response = requests.head(url, timeout=10)
            assert response.status_code == 200, (
                f"nuScenes mini metadata not available. " f"HTTP {response.status_code} at {url}"
            )
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Cannot reach nuScenes metadata: {e}")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_nuscenes_version_consistency(self):
        """
        Integration test: Verify all versions have required components.

        Ensures each version has the metadata component at minimum.
        This is a comprehensive check across all dataset versions.

        The test will fail if:
        - Any version is missing metadata component
        - Version structure has changed
        - Data inconsistency is detected

        Notes
        -----
        Marked as 'slow' because it tests all versions.
        Run with: pytest -m "integration and slow" -v

        In CI/CD, you may want to skip this or run it separately.
        """
        for version in ["mini", "trainval", "test"]:
            downloader = NuScenesDownloader(version=version)
            assert (
                "metadata" in downloader.AVAILABLE_FILES
            ), f"Version '{version}' missing 'metadata' component"
