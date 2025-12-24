#!/usr/bin/env python3
"""
Download a file and compute its size and MD5 checksum.

Usage:
    python -m mobility_datasets.scripts.download_and_verify <url> <output_dir>
    poe download-file <url> <output_dir>

Example:
    poe download-file https://example.com/data.zip ./data
    # Output:
    # Filename: data.zip
    # Size: 1234567 bytes
    # MD5: abc123def456...
"""

import argparse
import hashlib
import sys
from pathlib import Path

import requests
from tqdm import tqdm


def download_file(url: str, output_dir: Path) -> None:
    """Download file and print size + MD5 hash."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract filename from URL
    filename = url.split("/")[-1]
    if not filename:
        raise ValueError(f"Could not extract filename from URL: {url}")

    output_path = output_dir / filename

    print(f"Downloading: {url}")

    response = requests.get(url, stream=True, timeout=30, allow_redirects=True)

    if response.status_code == 404:
        raise FileNotFoundError(f"Remote file not found (404): {url}")

    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    if total_size == 0:
        raise ValueError("Server didn't provide Content-Length header")

    hasher = hashlib.md5()
    bytes_downloaded = 0

    with open(output_path, "wb") as f:
        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=filename,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    hasher.update(chunk)
                    bytes_downloaded += len(chunk)
                    pbar.update(len(chunk))

    if bytes_downloaded != total_size:
        raise ValueError(f"Incomplete: got {bytes_downloaded}, expected {total_size}")

    print(f"\nFilename: {filename}")
    print(f"Size: {bytes_downloaded} bytes")
    print(f"MD5: {hasher.hexdigest()}")


def main():
    parser = argparse.ArgumentParser(
        description="Download a file and print its size and MD5 checksum"
    )
    parser.add_argument("url", help="URL to download")
    parser.add_argument("output_dir", help="Output directory")

    args = parser.parse_args()

    try:
        download_file(args.url, Path(args.output_dir))
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Cancelled", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
