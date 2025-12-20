"""
Base test classes for downloader tests.

Provides shared test functionality for all downloader implementations
(KITTI, nuScenes, Waymo, etc.) to avoid code duplication while maintaining
consistency across dataset downloaders.
"""


class BaseDownloaderTestCase:
    """
    Base class for downloader tests.

    Provides shared test methods that all downloader implementations should pass.
    Subclasses must implement the `downloader` fixture that returns a configured
    downloader instance.

    This follows the DRY principle - common test patterns are defined once and
    inherited by all downloader test classes.

    Important: All test methods must accept the `downloader` fixture as a parameter.

    Examples
    --------
    Subclass for KITTI:

    >>> class TestKITTIDownloaderInit(BaseDownloaderTestCase):
    ...     @pytest.fixture
    ...     def downloader(self, tmp_path):
    ...         from mobility_datasets.kitti.loader import KITTIDownloader
    ...         return KITTIDownloader(data_dir=str(tmp_path))
    ...
    ...     def test_init_creates_directory(self, downloader):
    ...         assert downloader.data_dir.exists()

    Subclass for nuScenes:

    >>> class TestNuScenesDownloaderInit(BaseDownloaderTestCase):
    ...     @pytest.fixture
    ...     def downloader(self, nuscenes_downloader_mini):
    ...         return nuscenes_downloader_mini
    ...
    ...     def test_init_creates_directory(self, downloader):
    ...         assert downloader.data_dir.exists()
    """

    def test_init_creates_directory(self, downloader):
        """Test that downloader creates data directory."""
        assert downloader.data_dir.exists(), "Data directory should be created"

    def test_available_files_dict_exists(self, downloader):
        """Test that AVAILABLE_FILES dictionary is defined."""
        assert hasattr(downloader, "AVAILABLE_FILES"), "Must have AVAILABLE_FILES"
        assert isinstance(downloader.AVAILABLE_FILES, dict), "AVAILABLE_FILES must be a dictionary"
        assert len(downloader.AVAILABLE_FILES) > 0, "AVAILABLE_FILES must not be empty"

    def test_unknown_component_handling(self, downloader, capsys):
        """Test handling of unknown/invalid components.

        All downloaders should gracefully handle unknown component names
        with some form of error message (implementation may vary).
        """
        downloader.download(["invalid_nonexistent_component"])

        captured = capsys.readouterr()
        output = captured.out + captured.err

        # Check that unknown component is reported (exact message may vary)
        assert (
            "Unknown component" in output
            or "invalid" in output.lower()
            or "not found" in output.lower()
        ), f"Should report unknown component. Output: {output}"
