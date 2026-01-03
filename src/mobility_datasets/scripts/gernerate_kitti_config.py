#!/usr/bin/env python3
"""
Generate complete KITTI configuration from HTML data.

This script generates the kitti.yaml with all sequences from the KITTI dataset,
including City, Residential, Road, Campus, and Person location types.

Usage:
    python generate_kitti_config.py [--output kitti.yaml]
    poe generate-kitti [--output kitti.yaml]
"""

from datetime import datetime
from pathlib import Path

import yaml

# All City sequences from the KITTI raw data website
CITY_SEQUENCES = [
    ("2011_09_26_drive_0001", 114, 660, True),
    ("2011_09_26_drive_0002", 83, 480, True),
    ("2011_09_26_drive_0005", 160, 960, True),
    ("2011_09_26_drive_0009", 453, 2700, True),
    ("2011_09_26_drive_0011", 238, 1380, True),
    ("2011_09_26_drive_0013", 150, 900, True),
    ("2011_09_26_drive_0014", 320, 1920, True),
    ("2011_09_26_drive_0017", 120, 720, True),
    ("2011_09_26_drive_0018", 276, 1656, True),
    ("2011_09_26_drive_0048", 28, 120, True),
    ("2011_09_26_drive_0051", 444, 2640, True),
    ("2011_09_26_drive_0056", 300, 1800, True),
    ("2011_09_26_drive_0057", 367, 2160, True),
    ("2011_09_26_drive_0059", 379, 2220, True),
    ("2011_09_26_drive_0060", 84, 480, False),
    ("2011_09_26_drive_0084", 389, 2280, True),
    ("2011_09_26_drive_0091", 346, 2040, True),
    ("2011_09_26_drive_0093", 439, 2580, True),
    ("2011_09_26_drive_0095", 274, 1620, False),
    ("2011_09_26_drive_0096", 481, 2880, False),
    ("2011_09_26_drive_0104", 318, 1860, False),
    ("2011_09_26_drive_0106", 233, 1380, False),
    ("2011_09_26_drive_0113", 93, 540, False),
    ("2011_09_26_drive_0117", 666, 3960, False),
    ("2011_09_28_drive_0001", 111, 660, False),
    ("2011_09_28_drive_0002", 382, 2280, False),
    ("2011_09_29_drive_0026", 164, 960, False),
    ("2011_09_29_drive_0071", 1065, 6360, False),
]

# Residential sequences
RESIDENTIAL_SEQUENCES = [
    ("2011_09_26_drive_0019", 487, 2880, True),
    ("2011_09_26_drive_0020", 92, 540, True),
    ("2011_09_26_drive_0022", 806, 4800, True),
    ("2011_09_26_drive_0023", 480, 2880, True),
    ("2011_09_26_drive_0035", 137, 820, True),
    ("2011_09_26_drive_0036", 809, 4860, True),
    ("2011_09_26_drive_0039", 401, 2400, True),
    ("2011_09_26_drive_0046", 131, 780, True),
    ("2011_09_26_drive_0061", 709, 4260, True),
    ("2011_09_26_drive_0064", 576, 3420, True),
    ("2011_09_26_drive_0079", 107, 600, True),
    ("2011_09_26_drive_0086", 711, 4260, True),
    ("2011_09_26_drive_0087", 735, 4380, True),
    ("2011_09_30_drive_0018", 2768, 16560, False),
    ("2011_09_30_drive_0020", 1111, 6660, False),
    ("2011_09_30_drive_0027", 1112, 6672, False),
    ("2011_09_30_drive_0028", 5183, 31080, False),
    ("2011_09_30_drive_0033", 1600, 9600, False),
    ("2011_09_30_drive_0034", 1230, 7380, False),
    ("2011_10_03_drive_0027", 4550, 27300, False),
    ("2011_10_03_drive_0034", 4669, 28020, False),
]

# Road sequences (from HTML data provided)
ROAD_SEQUENCES = [
    ("2011_09_26_drive_0015", 303, 1800, True),
    ("2011_09_26_drive_0027", 194, 1140, True),
    ("2011_09_26_drive_0028", 435, 2580, True),
    ("2011_09_26_drive_0029", 436, 2580, True),
    ("2011_09_26_drive_0032", 396, 2340, True),
    ("2011_09_26_drive_0052", 84, 480, True),
    ("2011_09_26_drive_0070", 426, 2520, True),
    ("2011_09_26_drive_0101", 941, 5640, False),
    ("2011_09_29_drive_0004", 345, 2040, False),
    ("2011_09_30_drive_0016", 285, 1680, False),
    ("2011_10_03_drive_0042", 1176, 7020, False),
    ("2011_10_03_drive_0047", 844, 5040, False),
]

# Campus sequences
CAMPUS_SEQUENCES = [
    ("2011_09_28_drive_0016", 192, 1140, False),
    ("2011_09_28_drive_0021", 215, 1260, False),
    ("2011_09_28_drive_0034", 55, 300, False),
    ("2011_09_28_drive_0035", 41, 240, False),
    ("2011_09_28_drive_0037", 94, 540, False),
    ("2011_09_28_drive_0038", 116, 660, False),
    ("2011_09_28_drive_0039", 358, 2100, False),
    ("2011_09_28_drive_0043", 151, 900, False),
    ("2011_09_28_drive_0045", 49, 240, False),
    ("2011_09_28_drive_0047", 37, 180, False),
]

# Person sequences
PERSON_SEQUENCES = [
    ("2011_09_28_drive_0053", 74, 420, False),
    ("2011_09_28_drive_0054", 51, 300, False),
    ("2011_09_28_drive_0057", 80, 480, False),
    ("2011_09_28_drive_0065", 45, 240, False),
    ("2011_09_28_drive_0066", 35, 180, False),
    ("2011_09_28_drive_0068", 73, 420, False),
    ("2011_09_28_drive_0070", 45, 240, False),
    ("2011_09_28_drive_0071", 49, 240, False),
    ("2011_09_28_drive_0075", 76, 420, False),
    ("2011_09_28_drive_0077", 48, 240, False),
    ("2011_09_28_drive_0078", 43, 240, False),
    ("2011_09_28_drive_0080", 46, 240, False),
    ("2011_09_28_drive_0082", 81, 480, False),
    ("2011_09_28_drive_0086", 36, 180, False),
    ("2011_09_28_drive_0087", 88, 480, False),
    ("2011_09_28_drive_0089", 45, 240, False),
    ("2011_09_28_drive_0090", 52, 300, False),
    ("2011_09_28_drive_0094", 92, 540, False),
    ("2011_09_28_drive_0095", 47, 240, False),
    ("2011_09_28_drive_0096", 51, 300, False),
    ("2011_09_28_drive_0098", 50, 300, False),
    ("2011_09_28_drive_0100", 83, 480, False),
    ("2011_09_28_drive_0102", 52, 300, False),
    ("2011_09_28_drive_0103", 44, 240, False),
    ("2011_09_28_drive_0104", 50, 300, False),
    ("2011_09_28_drive_0106", 81, 480, False),
    ("2011_09_28_drive_0108", 54, 300, False),
    ("2011_09_28_drive_0110", 69, 360, False),
    ("2011_09_28_drive_0113", 80, 480, False),
    ("2011_09_28_drive_0117", 42, 240, False),
    ("2011_09_28_drive_0119", 83, 480, False),
    ("2011_09_28_drive_0121", 52, 300, False),
    ("2011_09_28_drive_0122", 49, 240, False),
    ("2011_09_28_drive_0125", 66, 360, False),
    ("2011_09_28_drive_0126", 37, 180, False),
    ("2011_09_28_drive_0128", 35, 180, False),
    ("2011_09_28_drive_0132", 79, 420, False),
    ("2011_09_28_drive_0134", 61, 360, False),
    ("2011_09_28_drive_0135", 47, 240, False),
    ("2011_09_28_drive_0136", 36, 180, False),
    ("2011_09_28_drive_0138", 74, 420, False),
    ("2011_09_28_drive_0141", 77, 420, False),
    ("2011_09_28_drive_0143", 38, 180, False),
    ("2011_09_28_drive_0145", 42, 240, False),
    ("2011_09_28_drive_0146", 77, 420, False),
    ("2011_09_28_drive_0149", 52, 300, False),
    ("2011_09_28_drive_0153", 96, 540, False),
    ("2011_09_28_drive_0154", 49, 240, False),
    ("2011_09_28_drive_0155", 54, 300, False),
    ("2011_09_28_drive_0156", 36, 180, False),
    ("2011_09_28_drive_0160", 47, 240, False),
    ("2011_09_28_drive_0161", 43, 240, False),
    ("2011_09_28_drive_0162", 44, 240, False),
    ("2011_09_28_drive_0165", 89, 480, False),
    ("2011_09_28_drive_0166", 45, 240, False),
    ("2011_09_28_drive_0167", 60, 360, False),
    ("2011_09_28_drive_0168", 64, 360, False),
    ("2011_09_28_drive_0171", 33, 180, False),
    ("2011_09_28_drive_0174", 60, 360, False),
    ("2011_09_28_drive_0177", 84, 480, False),
    ("2011_09_28_drive_0179", 49, 240, False),
    ("2011_09_28_drive_0183", 46, 240, False),
    ("2011_09_28_drive_0184", 92, 540, False),
    ("2011_09_28_drive_0185", 86, 480, False),
    ("2011_09_28_drive_0186", 47, 240, False),
    ("2011_09_28_drive_0187", 61, 360, False),
    ("2011_09_28_drive_0191", 44, 240, False),
    ("2011_09_28_drive_0192", 91, 540, False),
    ("2011_09_28_drive_0195", 45, 240, False),
    ("2011_09_28_drive_0198", 69, 360, False),
    ("2011_09_28_drive_0199", 41, 240, False),
    ("2011_09_28_drive_0201", 89, 480, False),
    ("2011_09_28_drive_0204", 57, 300, False),
    ("2011_09_28_drive_0205", 41, 240, False),
    ("2011_09_28_drive_0208", 60, 360, False),
    ("2011_09_28_drive_0209", 92, 540, False),
    ("2011_09_28_drive_0214", 48, 240, False),
    ("2011_09_28_drive_0216", 65, 360, False),
    ("2011_09_28_drive_0220", 83, 480, False),
    ("2011_09_28_drive_0222", 60, 360, False),
]


def create_download_info(url: str) -> dict:
    """Create download info structure."""
    return {"url": url, "filename": url.split("/")[-1], "size_bytes": 0, "md5": "", "format": "zip"}


def create_part(part_id: str, name: str, url: str, optional: bool = False) -> dict:
    """Create a part specification."""
    return {
        "id": part_id,
        "name": name,
        "download": create_download_info(url),
        "optional": optional,
    }


def create_session(drive_id: str, frames: int, duration: int, has_tracklets: bool) -> dict:
    """Create a complete session with all parts."""
    date = drive_id[:10]
    calib_url = f"https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/{date}_calib.zip"

    parts = [
        create_part(
            "unsynced_unrectified",
            "Unsynced + Unrectified",
            f"https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/{drive_id}/{drive_id}_extract.zip",
            optional=True,
        ),
        create_part(
            "synced_rectified",
            "Synced + Rectified",
            f"https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/{drive_id}/{drive_id}_sync.zip",
            optional=False,
        ),
        create_part("calib", "Calibration", calib_url, optional=False),
    ]

    if has_tracklets:
        parts.append(
            create_part(
                "tracklets",
                "Tracklets",
                f"https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/{drive_id}/{drive_id}_tracklets.zip",
                optional=True,
            )
        )

    return {"id": drive_id, "name": drive_id, "date": date, "parts": parts}


def create_collection(collection_id: str, name: str, sequences_list: list) -> dict:
    """Create a collection with sessions."""
    sessions = [create_session(seq[0], seq[1], seq[2], seq[3]) for seq in sequences_list]

    return {
        "id": collection_id,
        "name": name,
        "description": f"Raw sensor data from KITTI {name.lower()} benchmark sequences",
        "sessions": sessions,
    }


def generate_config() -> dict:
    """Generate the complete KITTI configuration."""
    config = {
        "metadata": {
            "name": "The KITTI Vision Benchmark Suite",
            "description": "A project of Karlsruhe Institute of Technology and Toyota Technological Institute at Chicago",
            "license": {
                "name": "CC BY-NC-SA 3.0",
                "url": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
            },
            "citation": {
                "bibtex": """@article{Geiger2013IJRR,
  author = {Andreas Geiger and Philip Lenz and Christoph Stiller and Raquel Urtasun},
  title = {Vision meets Robotics: The KITTI Dataset},
  journal = {International Journal of Robotics Research (IJRR)},
  year = {2013}
}"""
            },
        },
        "collections": [],
    }

    # Build collections dynamically
    collections_data = [
        ("city", "City", CITY_SEQUENCES),
        ("residential", "Residential", RESIDENTIAL_SEQUENCES),
        ("road", "Road", ROAD_SEQUENCES),
        ("campus", "Campus", CAMPUS_SEQUENCES),
        ("person", "Person", PERSON_SEQUENCES),
    ]

    for collection_id, collection_name, sequences in collections_data:
        if sequences:
            config["collections"].append(
                create_collection(collection_id, collection_name, sequences)
            )

    return config


def main():
    """Generate the complete KITTI configuration and log results."""
    print("=" * 80)
    print("KITTI Configuration Generator")
    print("=" * 80)
    print(f"Generated: {datetime.now().isoformat()}\n")

    config = generate_config()

    # Prepare output path
    output_path = Path("kitti.yaml")

    # Write to file with nice formatting
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print("Configuration Summary:")
    print("-" * 80)

    total_sequences = 0
    total_with_tracklets = 0
    total_without_tracklets = 0

    for collection in config["collections"]:
        collection_name = collection["name"]
        num_sessions = len(collection["sessions"])

        # Count tracklets and stats in this collection
        has_tracklets = sum(
            1
            for session in collection["sessions"]
            if any(part["id"] == "tracklets" for part in session["parts"])
        )
        without_tracklets = num_sessions - has_tracklets

        print(f"\n📁 {collection_name.upper()}")
        print(f"   Sequences: {num_sessions}")
        print(f"   ✓ With tracklets: {has_tracklets}")
        print(f"   ✗ Without tracklets: {without_tracklets}")

        total_sequences += num_sessions
        total_with_tracklets += has_tracklets
        total_without_tracklets += without_tracklets

    print("\n" + "-" * 80)
    print("TOTALS:")
    print(f"  Total sequences: {total_sequences}")
    print(f"  With tracklets: {total_with_tracklets}")
    print(f"  Without tracklets: {total_without_tracklets}")
    print(f"  Total collections: {len(config['collections'])}")
    print("-" * 80)

    print(f"\n✓ Configuration saved to: {output_path}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
