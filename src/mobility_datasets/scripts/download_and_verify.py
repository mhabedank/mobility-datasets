#!/usr/bin/env python3
"""
Verify and download KITTI configuration files.

Loads a kitti.yaml configuration, verifies all file URLs with HEAD requests,
downloads files where size_bytes and/or md5 are missing, and updates the YAML.

Usage:
    python verify_and_download_kitti.py <path_to_kitti.yaml> [--output-dir ./downloads]
    poe verify-kitti <path_to_kitti.yaml> [--output-dir ./downloads]

Example:
    python verify_and_download_kitti.py ./src/mobility_datasets/config/kitti.yaml
"""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import yaml
from tqdm import tqdm


class KittiVerifier:
    """Verify and download KITTI configuration files."""

    def __init__(self, config_path: Path, output_dir: Path):
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.config = self._load_config()
        self.files_to_process: List[Dict] = []
        self.failed_urls: List[Dict] = []
        self.session = requests.Session()
        self.session.timeout = 30
        self.log_messages = []

    def _log(self, message: str) -> None:
        """Log a message and print it."""
        print(message)
        self.log_messages.append(message)

    def _load_config(self) -> dict:
        """Load YAML configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        if not config or "collections" not in config:
            raise ValueError("Invalid KITTI config: missing 'collections'")

        return config

    def _extract_files(self) -> None:
        """Extract all files from config that need verification/download."""
        self.files_to_process = []

        for collection in self.config.get("collections", []):
            for session in collection.get("sessions", []):
                session_id = session.get("id", "unknown")
                for part in session.get("parts", []):
                    download_info = part.get("download", {})
                    url = download_info.get("url")
                    size_bytes = download_info.get("size_bytes")
                    md5 = download_info.get("md5", "")

                    if not url:
                        continue

                    # Check if needs processing (TODO or 0 or empty string)
                    needs_processing = (
                        size_bytes == "TODO" or size_bytes == 0 or md5 == "" or md5 == "TODO"
                    )

                    self.files_to_process.append(
                        {
                            "url": url,
                            "session_id": session_id,
                            "part_id": part.get("id"),
                            "filename": url.split("/")[-1],
                            "needs_processing": needs_processing,
                            "current_size": size_bytes,
                            "current_md5": md5,
                            "collection_idx": self.config["collections"].index(collection),
                            "session_idx": collection["sessions"].index(session),
                            "part_idx": session["parts"].index(part),
                        }
                    )

    def head_check_all(self) -> Tuple[int, List[Dict]]:
        """
        Perform HEAD requests on all URLs.

        Returns:
            Tuple of (successful_count, failed_urls_list)
        """
        self._log("\n" + "=" * 80)
        self._log("STAGE 1: Verifying all URLs with HEAD requests...")
        self._log("=" * 80)

        self.failed_urls = []
        successful = 0

        for file_info in tqdm(self.files_to_process, desc="HEAD checks"):
            try:
                response = self.session.head(file_info["url"], allow_redirects=True, timeout=10)

                if response.status_code == 404:
                    self.failed_urls.append({**file_info, "error": "404 Not Found"})
                elif response.status_code >= 400:
                    self.failed_urls.append({**file_info, "error": f"HTTP {response.status_code}"})
                else:
                    # Store content-length from HEAD
                    file_info["remote_size"] = int(response.headers.get("content-length", 0))
                    successful += 1

            except requests.RequestException as e:
                self.failed_urls.append({**file_info, "error": str(e)})

        return successful, self.failed_urls

    def download_and_verify(self) -> Tuple[int, int]:
        """
        Download all files that need processing and update YAML.

        Returns:
            Tuple of (successful_downloads, failed_downloads)
        """
        if self.failed_urls:
            self._log("\n" + "=" * 80)
            self._log(f"ERROR: {len(self.failed_urls)} URLs failed HEAD check!")
            self._log("=" * 80)
            self._print_failed_urls()
            return 0, len(self.failed_urls)

        # Filter files that need processing
        files_to_download = [f for f in self.files_to_process if f["needs_processing"]]

        # Filter files that are already complete
        files_complete = [f for f in self.files_to_process if not f["needs_processing"]]

        if files_complete:
            self._log("\n" + "=" * 80)
            self._log(f"SKIPPING: {len(files_complete)} files already verified")
            self._log("=" * 80)
            for file_info in files_complete:
                self._log(
                    f"  ✓ {file_info['filename']} ({file_info['session_id']}/{file_info['part_id']})"
                )

        if not files_to_download:
            self._log("\n" + "=" * 80)
            self._log("✓ All files are already verified (size_bytes and md5 present)")
            self._log("=" * 80)
            return 0, 0

        self._log("\n" + "=" * 80)
        self._log(f"STAGE 2: Downloading {len(files_to_download)} files...")
        self._log("=" * 80 + "\n")

        successful = 0
        failed = 0
        failed_downloads = []

        for file_info in files_to_download:
            try:
                size, md5 = self._download_file(file_info)
                file_info["downloaded_size"] = size
                file_info["downloaded_md5"] = md5

                # Update YAML
                self._update_yaml(file_info, size, md5)

                self._log(f"  ✓ {file_info['filename']}")
                self._log(f"    Size: {size} bytes")
                self._log(f"    MD5: {md5}")
                successful += 1
            except Exception as e:
                failed += 1
                failed_downloads.append({**file_info, "error": str(e)})
                self._log(f"  ✗ {file_info['filename']}: {str(e)}")

        self._print_summary(successful, failed_downloads)
        return successful, failed

    def _download_file(self, file_info: Dict) -> Tuple[int, str]:
        """
        Download a single file and return size and MD5.

        File is deleted after verification to prevent disk space issues.

        Returns:
            Tuple of (file_size_bytes, md5_hash)
        """
        url = file_info["url"]
        filename = file_info["filename"]
        output_path = self.output_dir / filename

        response = self.session.get(url, stream=True, allow_redirects=True)

        if response.status_code == 404:
            raise FileNotFoundError("Remote file not found (404)")

        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        if total_size == 0:
            raise ValueError("Server didn't provide Content-Length header")

        hasher = hashlib.md5()
        bytes_downloaded = 0

        try:
            with open(output_path, "wb") as f:
                with tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=filename,
                    leave=False,
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            hasher.update(chunk)
                            bytes_downloaded += len(chunk)
                            pbar.update(len(chunk))

            if bytes_downloaded != total_size:
                raise ValueError(
                    f"Incomplete download: got {bytes_downloaded}, " f"expected {total_size}"
                )

            md5_hash = hasher.hexdigest()
            return bytes_downloaded, md5_hash

        finally:
            # Delete file after verification to save disk space
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception as e:
                    self._log(f"    Warning: Could not delete {filename}: {e}")
                    raise

    def _update_yaml(self, file_info: Dict, size: int, md5: str) -> None:
        """Update the YAML configuration with downloaded size and MD5."""
        collection_idx = file_info["collection_idx"]
        session_idx = file_info["session_idx"]
        part_idx = file_info["part_idx"]

        # Update in-memory config
        download_info = self.config["collections"][collection_idx]["sessions"][session_idx][
            "parts"
        ][part_idx]["download"]
        download_info["size_bytes"] = size
        download_info["md5"] = md5

        # Write updated config back to file
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def _print_summary(self, successful: int, failed_downloads: List[Dict]) -> None:
        """Print summary of download results."""
        self._log("\n" + "=" * 80)
        self._log("SUMMARY")
        self._log("=" * 80)
        self._log(f"✓ Successfully downloaded and verified: {successful}")
        self._log(f"✗ Failed downloads: {len(failed_downloads)}")

        if failed_downloads:
            self._log("\nFailed Downloads:")
            for file_info in failed_downloads:
                self._log(f"\n  • {file_info['filename']}")
                self._log(f"    Session: {file_info['session_id']}")
                self._log(f"    Part: {file_info['part_id']}")
                self._log(f"    URL: {file_info['url']}")
                self._log(f"    Error: {file_info['error']}")

        if successful > 0:
            self._log("\n" + "-" * 80)
            self._log("✓ YAML configuration updated successfully!")
            self._log(f"  Updated: {self.config_path}")
            self._log("-" * 80)

        # Write log file
        log_file = self.output_dir / "verify_download.log"
        with open(log_file, "w") as f:
            f.write("\n".join(self.log_messages))
        self._log(f"\n✓ Log saved to: {log_file}")

    def run(self) -> int:
        """Execute the full verification and download workflow."""
        try:
            self._log(f"Loading config: {self.config_path}")
            self._extract_files()
            self._log(f"Found {len(self.files_to_process)} files to check")

            # Stage 1: HEAD checks
            successful_heads, failed = self.head_check_all()
            self._log(f"\n✓ HEAD checks passed: {successful_heads}")

            if failed:
                self._log(f"✗ HEAD checks failed: {len(failed)}")
                return 1

            # Stage 2: Download and verify
            successful_downloads, failed_downloads = self.download_and_verify()

            return 0 if failed_downloads == 0 else 1

        except FileNotFoundError as e:
            self._log(f"Error: {e}")
            return 1
        except ValueError as e:
            self._log(f"Error: {e}")
            return 1
        except KeyboardInterrupt:
            self._log("\n\nCancelled by user")
            return 130

    def _print_failed_urls(self) -> None:
        """Print detailed information about failed URLs."""
        self._log("\nFailed URLs (HEAD check):")
        for file_info in self.failed_urls:
            self._log(f"\n  • {file_info['filename']}")
            self._log(f"    Session: {file_info['session_id']}")
            self._log(f"    Part: {file_info['part_id']}")
            self._log(f"    URL: {file_info['url']}")
            self._log(f"    Error: {file_info['error']}")


def main():
    parser = argparse.ArgumentParser(description="Verify and download KITTI configuration files")
    parser.add_argument("config", help="Path to kitti.yaml configuration file")
    parser.add_argument(
        "--output-dir",
        default="./downloads",
        help="Output directory for downloaded files (default: ./downloads)",
    )

    args = parser.parse_args()

    verifier = KittiVerifier(Path(args.config), Path(args.output_dir))
    return verifier.run()


if __name__ == "__main__":
    sys.exit(main())
