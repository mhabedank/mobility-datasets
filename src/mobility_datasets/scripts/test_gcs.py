#!/usr/bin/env python3
"""
Waymo GCS Test - Funktioniert OHNE GCP Project.

Das Problem: storage.Client() erfordert ein Project, aber
wir brauchen keines für öffentliche Buckets!

Lösung: Spezifiziere ein beliebiges Project (wird ignoriert
für öffentliche Buckets).
"""

import base64
import sys

try:
    from google.api_core import exceptions as api_exceptions
    from google.auth import exceptions as auth_exceptions
    from google.cloud import storage
except ImportError:
    print("Installing google-cloud-storage...")
    import subprocess

    subprocess.check_call(["pip", "install", "google-cloud-storage"])
    from google.api_core import exceptions as api_exceptions
    from google.auth import exceptions as auth_exceptions
    from google.cloud import storage


def get_hex_md5(blob) -> str:
    """Convert GCS base64 MD5 to hex format."""
    if blob.md5_hash:
        try:
            return base64.b64decode(blob.md5_hash).hex()
        except Exception:
            return "unknown"
    return "unknown"


def test_waymo_gcs_access():
    """Test basic GCS access to Waymo files (HEAD equivalent)."""

    print("=" * 70)
    print("Testing Waymo GCS Access (NO Project Required)")
    print("=" * 70)
    print()

    # Test files from different Waymo collections
    test_files = [
        {
            "bucket": "waymo_open_dataset_motion_v_1_3_1",
            "blob": "motion_dataset_v1.3.1_training.tar",
            "collection": "motion_v1.3.1",
            "session": "train",
        },
        {
            "bucket": "waymo_open_dataset_v_1_4_3",
            "blob": "training_data.tar",
            "collection": "perception_v1.4.3",
            "session": "train",
        },
        {
            "bucket": "waymo_open_dataset_end_to_end_camera_v_1_0_0",
            "blob": "training_camera_data.tar",
            "collection": "e2e_v1.0.0",
            "session": "train",
        },
    ]

    try:
        # WICHTIG: Für öffentliche Buckets brauchen wir kein echtes Project
        # Wir können einfach ein beliebiges Project angeben (wird ignoriert)
        client = storage.Client(project="mobility-datasets")
        print("✓ Connected to Google Cloud Storage")
        print("  (Note: Project ist für öffentliche Buckets nicht nötig)")
        print()

    except auth_exceptions.DefaultCredentialsError:
        print("✗ Authentication failed - Credentials not found")
        print()
        print("Fix: Set up credentials with:")
        print("  gcloud auth application-default login")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        return False

    all_passed = True

    for test_file in test_files:
        bucket_name = test_file["bucket"]
        blob_path = test_file["blob"]
        collection = test_file["collection"]
        session = test_file["session"]

        print(f"Testing: {collection}/{session}")
        print(f"  URL: gs://{bucket_name}/{blob_path}")

        try:
            bucket = client.bucket(bucket_name)
            blob = bucket.get_blob(blob_path)

            if blob is None:
                print("  ✗ Blob not found")
                all_passed = False
                print()
                continue

            # This is the HEAD equivalent - just metadata, no download
            size_bytes = blob.size
            size_gb = size_bytes / (1024**3)
            md5_hex = get_hex_md5(blob)
            updated = blob.updated.isoformat() if blob.updated else "unknown"

            print("  ✓ File exists")
            print(f"    Size: {size_bytes:,} bytes ({size_gb:.2f} GB)")
            print(f"    MD5: {md5_hex[:16]}...")
            print(f"    Updated: {updated}")

            # This is what we'll put in waymo.yaml
            print("    → For YAML:")
            print(f"      size_bytes: {size_bytes}")
            print(f"      md5: {md5_hex}")

        except api_exceptions.NotFound:
            print(f"  ✗ Bucket not found: {bucket_name}")
            all_passed = False

        except api_exceptions.PermissionDenied:
            print("  ✗ Permission denied")
            print("     This shouldn't happen for public Waymo buckets")
            all_passed = False

        except Exception as e:
            print(f"  ✗ Error: {type(e).__name__}: {e}")
            all_passed = False

        print()

    print("=" * 70)
    if all_passed:
        print("✓ All tests passed! GCS access is working.")
        print()
        print("Next steps:")
        print("  1. Run: poetry run python scripts/populate_waymo_metadata.py")
        print("  2. This fetches real metadata for all Waymo files")
        print("  3. Updates waymo.yaml automatically")
        return True
    else:
        print("✗ Some tests failed. Check errors above.")
        return False


if __name__ == "__main__":
    success = test_waymo_gcs_access()
    sys.exit(0 if success else 1)
