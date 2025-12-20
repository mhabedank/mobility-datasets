================================================================================
API Reference
================================================================================

Complete Python API documentation for mobility-datasets.

This reference covers all public classes, functions, and modules available
in the library.

.. contents::
   :local:
   :depth: 2

---

Quick Navigation
================

**Dataset Downloaders:**

- :ref:`kitti-downloader` - KITTI dataset downloader

**Utilities:**

- Coming soon: Data readers/parsers
- Coming soon: Coordinate transformations
- Coming soon: Visualization tools
- Coming soon: Metrics and evaluation

---

KITTI Dataset
=============

.. _kitti-downloader:

KITTIDownloader
---------------

.. autoclass:: mobility_datasets.kitti.loader.KITTIDownloader
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

**Example:**

.. code-block:: python

    from mobility_datasets.kitti.loader import KITTIDownloader

    # Initialize downloader
    downloader = KITTIDownloader(data_dir="./data/kitti")

    # Download specific components
    downloader.download(["oxts", "poses"], keep_zip=False)

    # Or download everything
    downloader.download_all(keep_zip=False)

---

Data Access
===========

Currently, data access is done directly through the file system. Helper
classes for reading and parsing data are coming in future releases.

Reading OXTS Data
-----------------

OXTS files are located at:

.. code-block:: text

    raw_data/2011_10_03/2011_10_03_drive_XXXX_sync/oxts/data/*.txt

Each file contains 30 space-separated values:

.. list-table::
   :header-rows: 1
   :widths: 10 40 15 15

   * - Index
     - Field
     - Unit
     - Type
   * - 0
     - Latitude
     - degrees
     - float64
   * - 1
     - Longitude
     - degrees
     - float64
   * - 2
     - Altitude
     - meters
     - float64
   * - 3
     - Roll
     - radians
     - float64
   * - 4
     - Pitch
     - radians
     - float64
   * - 5
     - Yaw
     - radians
     - float64
   * - 6-8
     - Velocity (vn, ve, vf)
     - m/s
     - float64
   * - 9-11
     - Velocity (vl, vu, ...)
     - m/s
     - float64
   * - 12-14
     - Acceleration (ax, ay, az)
     - m/s²
     - float64
   * - 15-17
     - Angular rate (wx, wy, wz)
     - rad/s
     - float64
   * - 18-29
     - Other sensor data
     - various
     - float64

**Example:**

.. code-block:: python

    import numpy as np
    from pathlib import Path

    # Read single OXTS file
    oxts_file = Path("./data/kitti/raw_data/2011_10_03/"
                     "2011_10_03_drive_0027_sync/oxts/data/0000000000.txt")
    data = np.loadtxt(oxts_file)

    lat, lon, alt = data[0], data[1], data[2]
    roll, pitch, yaw = data[3], data[4], data[5]

Reading Pose Data
-----------------

Pose files are located at:

.. code-block:: text

    dataset/poses/XX.txt

Each line contains 12 values representing a 3x4 transformation matrix:

.. code-block:: text

    r11 r12 r13 tx r21 r22 r23 ty r31 r32 r33 tz

**Example:**

.. code-block:: python

    import numpy as np
    from pathlib import Path

    # Read poses for sequence 00
    poses_file = Path("./data/kitti/dataset/poses/00.txt")
    poses_flat = np.loadtxt(poses_file)

    # Reshape to (N, 3, 4) matrices
    n_poses = len(poses_flat)
    poses = poses_flat.reshape(n_poses, 3, 4)

    # Extract rotation and translation
    for i, pose in enumerate(poses):
        rotation = pose[:3, :3]      # 3x3 rotation matrix
        translation = pose[:3, 3]     # 3x1 position vector

        print(f"Pose {i}: position = {translation}")

---

Sequence Mapping
================

KITTI sequences map to specific raw data drives:

.. list-table::
   :header-rows: 1
   :widths: 15 30 20 15 20

   * - Sequence
     - Raw Data Drive
     - Frames
     - Distance
     - Description
   * - 00
     - 2011_10_03_drive_0027
     - 4541
     - 3.7 km
     - Residential
   * - 01
     - 2011_10_03_drive_0042
     - 1101
     - 1.1 km
     - Highway
   * - 02
     - 2011_10_03_drive_0034
     - 4661
     - 5.1 km
     - Urban
   * - 04
     - 2011_09_30_drive_0016
     - 271
     - 0.4 km
     - Mixed
   * - 05
     - 2011_09_30_drive_0018
     - 2761
     - 2.2 km
     - Highway

**Example - Access sequence 00 data:**

.. code-block:: python

    from pathlib import Path

    data_dir = Path("./data/kitti")

    # Poses (ground truth)
    poses = data_dir / "dataset/poses/00.txt"

    # OXTS (GPS/IMU)
    oxts = data_dir / "raw_data/2011_10_03/2011_10_03_drive_0027_sync/oxts/data"

---

Coming Soon
===========

These modules are planned for future releases:

Data Readers
------------

.. code-block:: python

    # Planned API
    from mobility_datasets.kitti import KITTIReader

    reader = KITTIReader(data_dir="./data/kitti")

    # Load sequence data
    oxts_data = reader.load_oxts(sequence="00")
    poses = reader.load_poses(sequence="00")

    # Access as structured data
    print(f"First GPS: {oxts_data[0].lat}, {oxts_data[0].lon}")

Coordinate Transformations
---------------------------

.. code-block:: python

    # Planned API
    from mobility_datasets.coordinates import CoordinateTransformer

    transformer = CoordinateTransformer()
    pose_enu = transformer.transform(pose_camera,
                                     from_frame="CAMERA",
                                     to_frame="ENU")

Visualization
-------------

.. code-block:: python

    # Planned API
    from mobility_datasets.visualization import plot_trajectory

    plot_trajectory(ground_truth, estimated,
                   title="EKF vs Ground Truth")

Metrics
-------

.. code-block:: python

    # Planned API
    from mobility_datasets.metrics import TrajectoryMetrics

    metrics = TrajectoryMetrics(ground_truth, estimated)
    print(f"RMSE: {metrics.position_rmse():.2f} m")

---

Module Reference
================

Full module documentation:

.. autosummary::
   :toctree: _autosummary
   :recursive:

   mobility_datasets.kitti

---

See Also
========

- :doc:`../quickstart/index` - Quick start guide
- :doc:`../guides/kitti_dataset` - KITTI dataset structure
- :doc:`../cli/index` - Command-line interface
