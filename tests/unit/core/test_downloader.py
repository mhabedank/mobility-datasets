"""Unit tests for DatasetDownloader.

Tests focus on individual methods with mocked dependencies.
No real network or file system operations (except tmp_path).
"""

import hashlib
from unittest.mock import Mock, patch

import pytest
import requests
from mobility_datasets.core.downloader import DatasetDownloader, FileStatus


class TestDatasetDownloaderInit:
    """Test suite for DatasetDownloader.__init__()"""

    def test_init_creates_data_directory(self, tmp_path, mock_config):
        """Directory is created if it doesn't exist.

        Purpose: Verify data directory is created during initialization.
        """
        data_dir = tmp_path / "new_dataset_dir"
        assert not data_dir.exists()

        with patch("mobility_datasets.core.downloader.ConfigProvider") as mock_provider_class:
            mock_provider = Mock()
            mock_provider.get_from_datasource.return_value = mock_config
            mock_provider_class.return_value = mock_provider

            downloader = DatasetDownloader(dataset="test", data_dir=str(data_dir))

        assert downloader.data_dir.exists()
        assert downloader.data_dir == data_dir / "test"

    def test_init_loads_config_from_provider(self, tmp_path, mock_config):
        """Config is loaded from ConfigProvider.

        Purpose: Verify ConfigProvider is called with correct dataset name.
        """
        with patch("mobility_datasets.core.downloader.ConfigProvider") as mock_provider_class:
            mock_provider = Mock()
            mock_provider.get_from_datasource.return_value = mock_config
            mock_provider_class.return_value = mock_provider

            downloader = DatasetDownloader(dataset="kitti", data_dir=str(tmp_path))

            mock_provider.get_from_datasource.assert_called_once_with("kitti")

        assert downloader.config == mock_config

    def test_init_raises_on_invalid_dataset(self, tmp_path):
        """FileNotFoundError raised for non-existent dataset YAML.

        Purpose: Provide clear error when dataset config doesn't exist.
        """
        with patch("mobility_datasets.core.downloader.ConfigProvider") as mock_provider_class:
            mock_provider = Mock()
            mock_provider.get_from_datasource.side_effect = FileNotFoundError(
                "Config not found for 'invalid'"
            )
            mock_provider_class.return_value = mock_provider

            with pytest.raises(FileNotFoundError):
                DatasetDownloader(dataset="invalid", data_dir=str(tmp_path))


class TestValidateFile:
    """Test suite for _validate_file() method"""

    def test_validate_missing_file(self, downloader, mock_config):
        """Returns MISSING if file doesn't exist.

        Purpose: Detect when file hasn't been downloaded yet.
        """
        part = mock_config.collections[0].sessions[0].parts[0]
        status = downloader._validate_file(part)

        assert status == FileStatus.MISSING

    def test_validate_partial_file(self, downloader, mock_config):
        """Returns PARTIAL if file size < expected.

        Purpose: Detect interrupted downloads to enable resume.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Create file with wrong size
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(b"short")

        status = downloader._validate_file(part)

        assert status == FileStatus.PARTIAL

    def test_validate_wrong_md5(self, downloader, mock_config):
        """Returns WRONG_MD5 if checksum differs.

        Purpose: Detect corrupted or incomplete downloads.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Create file with correct size but different content
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(b"a" * part.download.size_bytes)

        status = downloader._validate_file(part)

        assert status == FileStatus.WRONG_MD5

    def test_validate_valid_file(self, downloader, mock_config):
        """Returns VALID if size and MD5 match.

        Purpose: Confirm file is ready for extraction.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Create file with correct size and content matching MD5
        content = b"a" * part.download.size_bytes
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(content)

        # Update part MD5 to match our content
        actual_md5 = hashlib.md5(content).hexdigest()
        part.download.md5 = actual_md5

        status = downloader._validate_file(part)

        assert status == FileStatus.VALID


class TestCalculateMd5:
    """Test suite for _calculate_md5() method"""

    def test_calculate_md5_small_file(self, downloader, tmp_path):
        """MD5 calculated correctly for small files.

        Purpose: Verify hash calculation works for small downloads.
        """
        content = b"test content"
        file_path = tmp_path / "test.bin"
        file_path.write_bytes(content)

        expected_hash = hashlib.md5(content).hexdigest()
        actual_hash = downloader._calculate_md5(file_path)

        assert actual_hash == expected_hash

    def test_calculate_md5_large_file(self, downloader, tmp_path):
        """MD5 calculated correctly for large files (chunked).

        Purpose: Verify chunked reading works for large files.
        """
        # Create 1MB file
        content = b"x" * (1024 * 1024)
        file_path = tmp_path / "large.bin"
        file_path.write_bytes(content)

        expected_hash = hashlib.md5(content).hexdigest()
        actual_hash = downloader._calculate_md5(file_path)

        assert actual_hash == expected_hash


class TestDownloadFromStart:
    """Test suite for _download_from_start() method"""

    def test_download_removes_existing_file(self, downloader, mock_config):
        """Existing partial file is removed before download.

        Purpose: Ensure clean downloads from scratch.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Create existing file
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(b"old content")
        assert file_path.exists()

        # Mock requests.get
        mock_response = Mock()
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"new content"]
        mock_response.raise_for_status = Mock()

        with patch("requests.get", return_value=mock_response):
            downloader._download_from_start(part)

        # Verify new file has new content
        assert file_path.read_bytes() == b"new content"

    def test_download_creates_file_with_content(self, downloader, mock_config):
        """File is created with streamed content.

        Purpose: Verify streaming download works correctly.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        mock_response = Mock()
        mock_response.headers = {"content-length": "20"}
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_response.raise_for_status = Mock()

        with patch("requests.get", return_value=mock_response):
            downloader._download_from_start(part)

        file_path = downloader.data_dir / part.download.filename
        assert file_path.exists()
        assert file_path.read_bytes() == b"chunk1chunk2"

    def test_download_handles_http_error(self, downloader, mock_config):
        """HTTPError from requests is re-raised.

        Purpose: Propagate network errors to caller.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(requests.HTTPError):
                downloader._download_from_start(part)


class TestDownloadResume:
    """Test suite for _download_resume() method"""

    def test_resume_checks_range_support(self, downloader, mock_config):
        """HEAD request checks Accept-Ranges header.

        Purpose: Verify server support for partial requests.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Create partial file
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(b"partial")

        mock_head = Mock()
        mock_head.headers = {"accept-ranges": "bytes"}

        with patch("requests.head", return_value=mock_head) as mock_head_call:
            with patch.object(downloader, "_download_from_start"):
                downloader._download_resume(part)

                # Verify HEAD was called to check ranges
                mock_head_call.assert_called_once_with(part.download.url, timeout=10)

    def test_resume_fallback_no_range_support(self, downloader, mock_config):
        """Falls back to fresh download if server doesn't support ranges.

        Purpose: Handle servers that don't support partial requests.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Create partial file
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(b"partial")

        mock_head = Mock()
        mock_head.headers = {"accept-ranges": "none"}

        with patch("requests.head", return_value=mock_head):
            with patch.object(downloader, "_download_from_start") as mock_fresh:
                downloader._download_resume(part)
                mock_fresh.assert_called_once_with(part)

    def test_resume_sends_range_request(self, downloader, mock_config):
        """Range request is made when server supports ranges.

        Purpose: Verify correct Range header is sent.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Create partial file (7 bytes)
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(b"partial")

        mock_head = Mock()
        mock_head.headers = {"accept-ranges": "bytes"}

        mock_response = Mock()
        mock_response.status_code = 206  # Partial Content
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = []

        with patch("requests.head", return_value=mock_head):
            with patch("requests.get", return_value=mock_response) as mock_get:
                # Patch _validate_file to succeed immediately
                with patch.object(downloader, "_validate_file", return_value=FileStatus.VALID):
                    downloader._download_resume(part)

                    # Verify GET was called
                    mock_get.assert_called()

                    # Check that Range header was sent
                    call_kwargs = mock_get.call_args[1]
                    assert "headers" in call_kwargs
                    assert "Range" in call_kwargs["headers"]
                    assert call_kwargs["headers"]["Range"].startswith("bytes=")

    def test_resume_fallback_server_returns_full_file(self, downloader, mock_config):
        """Falls back if server returns 200 instead of 206.

        Purpose: Handle servers that ignore Range header.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Create partial file
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(b"partial")

        mock_head = Mock()
        mock_head.headers = {"accept-ranges": "bytes"}

        mock_response = Mock()
        mock_response.status_code = 200  # Full file, not partial

        with patch("requests.head", return_value=mock_head):
            with patch("requests.get", return_value=mock_response):
                with patch.object(downloader, "_download_from_start") as mock_fresh:
                    downloader._download_resume(part)
                    mock_fresh.assert_called_once()


class TestDownloadPart:
    """Test suite for _download_part() orchestration"""

    def test_download_skips_valid_file(self, downloader, mock_config):
        """Valid files are skipped without download.

        Purpose: Avoid re-downloading valid files.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Create valid file
        content = b"a" * part.download.size_bytes
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(content)
        part.download.md5 = hashlib.md5(content).hexdigest()

        with patch("requests.get") as mock_get:
            downloader._download_part(part)
            mock_get.assert_not_called()

    def test_download_missing_file(self, downloader, mock_config):
        """MISSING file triggers fresh download.

        Purpose: Download files that don't exist.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        with patch.object(downloader, "_download_from_start") as mock_fresh:
            with patch.object(
                downloader,
                "_validate_file",
                side_effect=[
                    FileStatus.MISSING,
                    FileStatus.VALID,
                ],
            ):
                downloader._download_part(part)
                mock_fresh.assert_called()

    def test_download_partial_file(self, downloader, mock_config):
        """PARTIAL file triggers resume.

        Purpose: Resume interrupted downloads.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        with patch.object(downloader, "_download_resume") as mock_resume:
            with patch.object(
                downloader,
                "_validate_file",
                side_effect=[
                    FileStatus.PARTIAL,
                    FileStatus.VALID,
                ],
            ):
                downloader._download_part(part)
                mock_resume.assert_called()

    def test_download_retries_on_failure(self, downloader, mock_config):
        """Failed downloads are retried up to 3 times.

        Purpose: Retry transient errors.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # Validation always returns MISSING (simulating failed download)
        with patch.object(downloader, "_download_from_start"):
            with patch.object(downloader, "_validate_file", return_value=FileStatus.MISSING):
                downloader._download_part(part, retries=3)

                # Should have called _validate_file 4 times:
                # 1 initial + 3 retries
                assert downloader._validate_file.call_count == 4

    def test_download_wrong_md5_redownloads(self, downloader, mock_config):
        """WRONG_MD5 triggers full re-download.

        Purpose: Re-download corrupted files from scratch.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        with patch.object(downloader, "_download_from_start") as mock_fresh:
            with patch.object(
                downloader,
                "_validate_file",
                side_effect=[
                    FileStatus.WRONG_MD5,
                    FileStatus.VALID,
                ],
            ):
                downloader._download_part(part)
                mock_fresh.assert_called()


class TestExtractFile:
    """Test suite for _extract_file() format-agnostic extraction"""

    def test_extract_skips_missing_file(self, downloader, mock_config):
        """Missing file is skipped without error.

        Purpose: Handle missing archives gracefully.
        """
        part = mock_config.collections[0].sessions[0].parts[0]

        # File doesn't exist
        downloader._extract_file(part, keep_zip=False)

        # Should not raise, just print warning

    def test_extract_zip_format(self, downloader, test_zip_file, mock_config):
        """ZIP files are extracted correctly.

        Purpose: Support ZIP format (KITTI, nuScenes).
        """
        part = mock_config.collections[0].sessions[0].parts[0]
        part.download.format = "zip"
        part.download.filename = test_zip_file.name

        # Copy test ZIP to data_dir
        import shutil

        zip_in_data_dir = downloader.data_dir / test_zip_file.name
        shutil.copy(test_zip_file, zip_in_data_dir)

        downloader._extract_file(part, keep_zip=True)

        # Verify file was extracted
        extracted_file = downloader.data_dir / "test.txt"
        assert extracted_file.exists()

    def test_extract_tar_gz_format(self, downloader, test_tar_gz_file, mock_config):
        """TAR.GZ files are extracted correctly.

        Purpose: Support TAR.GZ format (Waymo, etc.).
        """
        part = mock_config.collections[0].sessions[0].parts[0]
        part.download.format = "tar.gz"
        part.download.filename = test_tar_gz_file.name

        # Copy test TAR.GZ to data_dir
        import shutil

        tar_in_data_dir = downloader.data_dir / test_tar_gz_file.name
        shutil.copy(test_tar_gz_file, tar_in_data_dir)

        downloader._extract_file(part, keep_zip=True)

        # Verify file was extracted
        extracted_file = downloader.data_dir / "test.txt"
        assert extracted_file.exists()

    def test_extract_tfrecord_no_extraction(self, downloader, mock_config, tmp_path):
        """TFRecords are not extracted (used directly).

        Purpose: TFRecords don't need extraction.
        """
        part = mock_config.collections[0].sessions[0].parts[0]
        part.download.format = "tfrecord"
        part.download.filename = "test.tfrecord"

        # Create dummy TFRecord
        tfrecord_path = downloader.data_dir / "test.tfrecord"
        tfrecord_path.write_bytes(b"tfrecord content")

        downloader._extract_file(part, keep_zip=False)

        # File should NOT be deleted (no extraction)
        assert tfrecord_path.exists()

    def test_extract_unknown_format_skipped(self, downloader, mock_config):
        """Unknown formats are skipped with warning.

        Purpose: Handle unknown formats gracefully.
        """
        part = mock_config.collections[0].sessions[0].parts[0]
        part.download.format = "unknown_format"

        # Create dummy file
        file_path = downloader.data_dir / part.download.filename
        file_path.write_bytes(b"content")

        downloader._extract_file(part, keep_zip=False)

        # File should not be deleted
        assert file_path.exists()

    def test_extract_removes_archive_if_not_keep_zip(self, downloader, test_zip_file, mock_config):
        """Archive is deleted after extraction if keep_zip=False.

        Purpose: Save disk space by removing archives.
        """
        part = mock_config.collections[0].sessions[0].parts[0]
        part.download.format = "zip"
        part.download.filename = test_zip_file.name

        # Copy test ZIP to data_dir
        import shutil

        zip_in_data_dir = downloader.data_dir / test_zip_file.name
        shutil.copy(test_zip_file, zip_in_data_dir)

        downloader._extract_file(part, keep_zip=False)

        # Archive should be deleted
        assert not zip_in_data_dir.exists()


class TestDownload:
    """Test suite for public download() method"""

    def test_download_skips_nonexistent_sessions(self, downloader, mock_config):
        """Non-existent sessions are skipped with warning.

        Purpose: Handle user input gracefully.
        """
        with patch.object(downloader, "_download_part"):
            with patch.object(downloader, "_extract_file"):
                # Request session that doesn't exist
                downloader.download("test_collection", sessions=["nonexistent"])

                # Should not raise, just skip

    def test_download_skips_optional_parts(self, downloader, mock_config_with_optional):
        """Optional parts skipped unless with_optional=True.

        Purpose: Allow users to skip optional data.
        """
        with patch("mobility_datasets.core.downloader.ConfigProvider") as mock_provider_class:
            mock_provider = Mock()
            mock_provider.get_from_datasource.return_value = mock_config_with_optional
            mock_provider_class.return_value = mock_provider

            downloader = DatasetDownloader(dataset="test", data_dir="/tmp")

            with patch.object(downloader, "_download_part") as mock_download:
                with patch.object(downloader, "_extract_file"):
                    downloader.download(
                        "test_collection",
                        sessions=["test_session_001"],
                        with_optional=False,
                    )

                    # Should only call _download_part for required part
                    assert mock_download.call_count == 1
                    call_args = mock_download.call_args[0][0]
                    assert call_args.id == "required_part"


class TestDownloadAll:
    """Test suite for download_all() method"""

    def test_download_all_calls_download_per_collection(
        self, downloader, mock_config_multiple_collections
    ):
        """download() called for each collection.

        Purpose: Verify download_all() iterates all collections.
        """
        with patch("mobility_datasets.core.downloader.ConfigProvider") as mock_provider_class:
            mock_provider = Mock()
            mock_provider.get_from_datasource.return_value = mock_config_multiple_collections
            mock_provider_class.return_value = mock_provider

            downloader = DatasetDownloader(dataset="test", data_dir="/tmp")

            with patch.object(downloader, "download") as mock_download:
                downloader.download_all()

                # Should call download() for each collection
                assert mock_download.call_count == 2

                # Verify correct collections were passed
                calls = [call[1]["collection_id"] for call in mock_download.call_args_list]
                assert "collection_001" in calls
                assert "collection_002" in calls


class TestHealthCheck:
    """Test suite for health_check() method"""

    def test_health_check_returns_dict(self, downloader, mock_config):
        """Returns dict with file IDs as keys.

        Purpose: Verify return type and structure.
        """
        mock_response = Mock()
        mock_response.status_code = 200

        with patch("requests.head", return_value=mock_response):
            status = downloader.health_check()

            assert isinstance(status, dict)
            assert len(status) > 0

    def test_health_check_marks_available(self, downloader, mock_config):
        """Available files marked as True (HTTP 200).

        Purpose: Identify available files.
        """
        mock_response = Mock()
        mock_response.status_code = 200

        with patch("requests.head", return_value=mock_response):
            status = downloader.health_check()

            # All should be True
            assert all(status.values())

    def test_health_check_marks_unavailable(self, downloader, mock_config):
        """Unavailable files marked as False.

        Purpose: Identify missing or broken files.
        """
        mock_response = Mock()
        mock_response.status_code = 404

        with patch("requests.head", return_value=mock_response):
            status = downloader.health_check()

            # All should be False
            assert not any(status.values())
