#!/usr/bin/env python3
"""
Liste ECHTE Dateien (blobs) in Waymo Buckets auf.

Wichtig: Waymo hat die Daten nicht als .tar files gespeichert!
Es sind Ordner (prefixes) mit einzelnen Dateien darin.
"""

import humanize
from google.api_core import exceptions as api_exceptions
from google.cloud import storage


def list_files_in_prefix(bucket_name: str, prefix: str, max_results: int = 50):
    """
    Liste alle echten Dateien (blobs) unter einem Prefix.

    Args:
        bucket_name: GCS Bucket name
        prefix: Prefix zum durchsuchen (z.B. "motion_dataset_v1.3.1_training/")
        max_results: Wie viele Blobs zeigen
    """

    print(f"\n{'='*70}")
    print(f"Files in: gs://{bucket_name}/{prefix}")
    print(f"{'='*70}\n")

    try:
        client = storage.Client(project="mobility-datasets")
        bucket = client.bucket(bucket_name)

        # Zähle erst, wie viele Blobs es gibt
        all_blobs = list(bucket.list_blobs(prefix=prefix))

        if not all_blobs:
            print(f"✗ Kein Dateien gefunden unter '{prefix}'")
            print("  Vielleicht ist das der falsche Prefix?\n")
            return

        print(f"✓ {len(all_blobs)} Dateien gefunden\n")

        # Zeige die ersten N
        for i, blob in enumerate(all_blobs[:max_results], 1):
            size = humanize.naturalsize(blob.size) if blob.size else "0 B"
            print(f"{i}. {blob.name}")
            print(f"   Size: {size}")
            if blob.updated:
                print(f"   Updated: {blob.updated}")
            print()

        if len(all_blobs) > max_results:
            print(f"... and {len(all_blobs) - max_results} more files\n")

        # Gib Sample für YAML
        if all_blobs:
            print("Sample file for YAML:")
            blob = all_blobs[0]
            print(f"  url: gs://{bucket_name}/{blob.name}")
            print(f"  size_bytes: {blob.size}")
            print()

    except api_exceptions.NotFound:
        print(f"✗ Bucket nicht gefunden: {bucket_name}\n")
    except Exception as e:
        print(f"✗ Fehler: {type(e).__name__}: {e}\n")


def main():
    """Explore alle Waymo Prefixes."""

    print("\n" + "=" * 70)
    print("WAYMO BUCKET - ECHTE DATEIEN AUFLISTEN")
    print("=" * 70)

    # Motion Dataset v1.3.1
    print("\n\n1. MOTION DATASET v1.3.1")
    list_files_in_prefix(
        "waymo_open_dataset_motion_v_1_3_1", "motion_dataset_v1.3.1_training/", max_results=10
    )

    list_files_in_prefix(
        "waymo_open_dataset_motion_v_1_3_1", "motion_dataset_v1.3.1_validation/", max_results=5
    )

    list_files_in_prefix(
        "waymo_open_dataset_motion_v_1_3_1", "motion_dataset_v1.3.1_test/", max_results=5
    )

    # Perception Dataset v1.4.3
    print("\n\n2. PERCEPTION DATASET v1.4.3")
    list_files_in_prefix("waymo_open_dataset_v_1_4_3", "training_data/", max_results=10)

    list_files_in_prefix("waymo_open_dataset_v_1_4_3", "validation_data/", max_results=10)

    # End-to-End Dataset
    print("\n\n3. END-TO-END DATASET v1.0.0")
    list_files_in_prefix(
        "waymo_open_dataset_end_to_end_camera_v_1_0_0", "training_camera/", max_results=10
    )

    list_files_in_prefix(
        "waymo_open_dataset_end_to_end_camera_v_1_0_0", "training_control/", max_results=10
    )

    print("\n" + "=" * 70)
    print("WICHTIG:")
    print("=" * 70)
    print(
        """
Die Waymo Daten sind NICHT als einzelne .tar Files gespeichert!

Stattdessen:
- Es gibt Ordner (prefixes) wie "motion_dataset_v1.3.1_training/"
- Darin sind viele einzelne Dateien (tfrecord, etc.)
- Jede Datei kann einzeln runterladen werden

Für dein Download System brauchst du ZWEI Möglichkeiten:

1. EINZELNE DATEIEN downloaden:
   gs://waymo_open_dataset_motion_v_1_3_1/motion_dataset_v1.3.1_training/scenario_0000/tfexample.tfrecord

2. ODER: Bei Ordnern alle Dateien darin downloaden:
   prefix = "motion_dataset_v1.3.1_training/"
   # Dann alle Dateien unter diesem Prefix runterladen

Schau die Ausgabe oben an und entscheide welcher Approach besser passt!
"""
    )


if __name__ == "__main__":
    main()
