# tests/kitti/test_loader.py
from unittest.mock import patch

import pytest
from mobility_datasets.kitti.loader import KITTIDownloader

from tests.base_downloader_test import BaseDownloaderTestCase


class TestKITTIDownloaderInit(BaseDownloaderTestCase):
    """Test KITTIDownloader initialization."""

    @pytest.fixture
    def downloader(self, tmp_path):
        """Create a KITTIDownloader instance for testing."""
        return KITTIDownloader(data_dir=str(tmp_path))

    def test_available_files_count(self, downloader):
        """Test that all 6 KITTI components are available."""
        assert len(downloader.AVAILABLE_FILES) == 6

    def test_available_files_names(self, downloader):
        """Test that all expected components are available."""
        expected = ["oxts", "calib", "label", "image_left", "image_right", "velodyne"]

        for component in expected:
            assert component in downloader.AVAILABLE_FILES


class TestKITTIDownloaderDownload:
    """Test download functionality."""

    @pytest.fixture
    def downloader(self, tmp_path):
        """Create a KITTIDownloader instance for testing."""
        return KITTIDownloader(data_dir=str(tmp_path))

    @pytest.mark.parametrize(
        "components,expected_calls",
        [
            (["calib"], 1),
            (["oxts"], 1),
            (["calib", "oxts"], 2),
            (["calib", "oxts", "label"], 3),
            (["calib", "oxts", "label", "image_left"], 4),
            (["calib", "oxts", "label", "image_left", "image_right", "velodyne"], 6),
        ],
    )
    @patch("mobility_datasets.kitti.loader.requests.get")
    @patch("mobility_datasets.kitti.loader.zipfile.ZipFile")
    def test_download_components(
        self,
        mock_zipfile,
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
        mock_zipfile.return_value = mock_zipfile

        downloader.download(components)

        assert mock_requests.call_count == expected_calls, (
            f"Expected {expected_calls} download calls for components {components}, "
            f"got {mock_requests.call_count}"
        )

    @patch("mobility_datasets.kitti.loader.requests.get")
    @patch("mobility_datasets.kitti.loader.zipfile.ZipFile")
    def test_download_all(self, mock_zipfile, mock_requests, downloader, mock_http_response):
        """Test downloading all components."""
        mock_requests.return_value = mock_http_response
        mock_zipfile.return_value = mock_zipfile

        downloader.download_all()

        # KITTI has 6 components
        assert mock_requests.call_count == 6


class TestKITTIDownloaderSkipExisting(BaseDownloaderTestCase):
    """Test handling of existing files."""

    @pytest.fixture
    def downloader(self, tmp_path):
        """Create a KITTIDownloader instance for testing."""
        return KITTIDownloader(data_dir=str(tmp_path))

    @pytest.mark.parametrize(
        "components",
        [
            ["calib"],
            ["oxts"],
            ["calib", "oxts"],
        ],
    )
    @patch("mobility_datasets.kitti.loader.requests.get")
    @patch("mobility_datasets.kitti.loader.zipfile.ZipFile")
    def test_skip_existing_files(self, mock_zipfile, mock_requests, components, tmp_path, capsys):
        """Test that existing files are skipped for various component sets.

        This parametrized test verifies that the downloader correctly skips
        downloading files that already exist.
        """
        # Create existing zip files
        for component in components:
            zip_path = tmp_path / f"data_tracking_{component}.zip"
            zip_path.touch()

        # Create new downloader with this tmp_path
        downloader = KITTIDownloader(data_dir=str(tmp_path))
        downloader.download(components)

        # Verify no download was attempted
        mock_requests.assert_not_called()

        # Verify message was printed
        captured = capsys.readouterr()
        assert "already exists" in captured.out


class TestKITTIDownloaderIntegration:
    """Integration tests for KITTI downloader."""

    @pytest.mark.integration
    def test_kitti_base_url_accessible(self):
        """
        Integration test: Verify KITTI base URL is accessible.

        This test checks if the AWS S3 base URL responds successfully.
        It performs a simple HEAD request to verify connectivity without
        downloading any data.

        The test will fail if:
        - AWS S3 is unreachable
        - Network connectivity is broken
        - The base URL has changed

        Notes
        -----
        This is a real integration test that requires internet connectivity.
        Run with: pytest -m integration
        """
        import requests

        downloader = KITTIDownloader()
        base_url = downloader.BASE_URL

        try:
            # Simple HEAD request to base URL (should return 403 or 200, not 404)
            response = requests.head(base_url, timeout=10)

            # S3 bucket root may return 403 (forbidden) but should not be 404
            assert response.status_code != 404, (
                f"KITTI base URL returned 404: {base_url}. "
                f"The S3 bucket may have been deleted or moved."
            )
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Cannot reach KITTI base URL {base_url}: {e}")

    @pytest.mark.integration
    def test_kitti_all_files_available(self):
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

            pytest -m integration -v

        Run with detailed output:

            pytest -m integration -v -s

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
    def test_kitti_essential_files_available(self):
        """
        Integration test: Verify essential KITTI files are available.

        Tests only the minimal files needed for sensor fusion:
        - oxts (GPS/IMU data)
        - calib (calibration)

        This is a lighter test than test_kitti_all_files_available and can be
        run more frequently in CI/CD pipelines.

        The test will fail if:
        - oxts component is not available
        - calib component is not available
        - S3 connectivity is broken

        Notes
        -----
        This test is suitable for:
        - Quick sanity checks in CI/CD
        - Rapid feedback on S3 availability
        - Smoke testing before full integration suite
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
    def test_kitti_large_files_available(self):
        """
        Integration test: Verify large KITTI files are available on S3.

        Tests the large files (images, velodyne) separately as they may be
        slower to check and more prone to S3 issues.

        The large components tested:
        - image_left (camera left)
        - image_right (camera right)
        - velodyne (LiDAR point clouds)

        These files are typically 100+ GB and may have different availability
        or network performance characteristics.

        Notes
        -----
        Marked as 'slow' because checking large files may take longer.
        Run with: pytest -m "integration and slow" -v

        In CI/CD, you may want to skip this test or run it separately from
        quick sanity checks to maintain fast feedback loops.
        """
        downloader = KITTIDownloader()
        status = downloader.health_check()

        large_files = ["image_left", "image_right", "velodyne"]

        for component in large_files:
            assert status[component], (
                f"Large KITTI component '{component}' is not available on S3. "
                f"Users will not be able to download complete dataset."
            )
