"""Test summary and execution guide for DatasetDownloader unit tests."""

# Test Execution Guide

## Quick Start

```bash
# Run all core downloader unit tests
pytest tests/unit/core/ -v

# Run specific test class
pytest tests/unit/core/test_downloader.py::TestValidateFile -v

# Run specific test
pytest tests/unit/core/test_downloader.py::TestValidateFile::test_validate_valid_file -v

# Run with coverage
pytest tests/unit/core/ --cov=src/mobility_datasets/core --cov-report=html

# Show print statements
pytest tests/unit/core/ -v -s
```

## Test Structure

Total: 33 Unit Tests across 10 Test Classes

### Test Classes

1. **TestDatasetDownloaderInit** (3 tests)
   - test_init_creates_data_directory
   - test_init_loads_config_from_provider
   - test_init_raises_on_invalid_dataset

2. **TestValidateFile** (4 tests)
   - test_validate_missing_file
   - test_validate_partial_file
   - test_validate_wrong_md5
   - test_validate_valid_file

3. **TestCalculateMd5** (2 tests)
   - test_calculate_md5_small_file
   - test_calculate_md5_large_file

4. **TestDownloadFromStart** (3 tests)
   - test_download_removes_existing_file
   - test_download_creates_file_with_content
   - test_download_handles_http_error

5. **TestDownloadResume** (4 tests)
   - test_resume_checks_range_support
   - test_resume_fallback_no_range_support
   - test_resume_continues_with_range_header
   - test_resume_fallback_server_returns_full_file

6. **TestDownloadPart** (5 tests)
   - test_download_skips_valid_file
   - test_download_missing_file
   - test_download_partial_file
   - test_download_retries_on_failure
   - test_download_wrong_md5_redownloads

7. **TestExtractFile** (6 tests)
   - test_extract_skips_missing_file
   - test_extract_zip_format
   - test_extract_tar_gz_format
   - test_extract_tfrecord_no_extraction
   - test_extract_unknown_format_skipped
   - test_extract_removes_archive_if_not_keep_zip

8. **TestDownload** (2 tests)
   - test_download_skips_nonexistent_sessions
   - test_download_skips_optional_parts

9. **TestDownloadAll** (1 test)
   - test_download_all_calls_download_per_collection

10. **TestHealthCheck** (3 tests)
    - test_health_check_returns_dict
    - test_health_check_marks_available
    - test_health_check_marks_unavailable

## Test Fixtures

### conftest.py Fixtures

- **mock_config**: Basic DatasetConfig with 1 collection, 1 session, 1 part
- **mock_config_with_optional**: Config with optional parts
- **mock_config_multiple_collections**: Config with 2 collections
- **downloader**: Ready-to-use DatasetDownloader with mocked ConfigProvider
- **test_zip_file**: Real ZIP file for extraction tests
- **test_tar_gz_file**: Real TAR.GZ file for extraction tests

## Mocking Strategy

### What is Mocked
- `ConfigProvider.get_from_datasource()` - Returns mock_config
- `requests.get()` - Stream responses
- `requests.head()` - HEAD responses with status codes

### What is Real (Not Mocked)
- `pathlib.Path` operations
- `hashlib.md5()` hashing
- `zipfile.ZipFile` extraction
- `tarfile` extraction

## Expected Behavior

All tests should:
- ✅ Pass without errors
- ✅ Complete in < 1 second total
- ✅ Use only pytest fixtures (tmp_path, mock_config, etc.)
- ✅ Have docstrings explaining purpose
- ✅ Be independent (no test ordering dependencies)

## CI/CD Integration

Add to `.github/workflows/tests.yml`:

```yaml
- name: Unit Tests (Core)
  run: pytest tests/unit/core/ -v --cov=src/mobility_datasets/core

- name: Upload Coverage
  run: codecov
```
