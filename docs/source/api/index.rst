================================================================================
API Reference
================================================================================

Complete Python API documentation for mobility-datasets.

This reference covers all public classes, functions, and modules available
in the library for programmatic dataset access and management.

.. contents::
   :local:
   :depth: 2

---

Quick Navigation
================

**Core Classes:**

- :ref:`dataset-downloader` - Generic dataset downloader (all datasets)
- :ref:`config-provider` - Dataset configuration loader

**Data Access:**

- Data readers and parsers (coming soon)
- Coordinate transformations (coming soon)
- Visualization tools (coming soon)

---

Core Classes
============

.. _dataset-downloader:

DatasetDownloader
-----------------

Generic downloader for any configured dataset (KITTI, nuScenes, Waymo, etc.).

.. autoclass:: mobility_datasets.core.downloader.DatasetDownloader
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

**Example - Download KITTI:**

.. code-block:: python

    from mobility_datasets.core.downloader import DatasetDownloader

    # Initialize downloader
    downloader = DatasetDownloader(dataset="kitti", data_dir="./data")

    # Download specific collection and sessions
    downloader.download(
        collection_id="city",
        sessions=["2011_09_26_drive_0001"],
        keep_zip=False,
        with_optional=False
    )

**Example - Get download size estimate:**

.. code-block:: python

    downloader = DatasetDownloader(dataset="kitti")

    # Estimate size before downloading
    size_info = downloader.get_download_size(
        collection_id="city",
        sessions=None,  # None = all sessions
        with_optional=False
    )

    print(f"Total size: {size_info['total_readable']}")
    # Output: Total size: 180 GB

    # See breakdown by part
    for part_id, size_bytes in size_info['parts'].items():
        print(f"  {part_id}: {size_info['total_readable']}")

**Example - Verify file availability:**

.. code-block:: python

    downloader = DatasetDownloader(dataset="kitti")

    # Check which files are available on remote servers
    availability = downloader.health_check()

    available = sum(availability.values())
    total = len(availability)
    print(f"{available}/{total} files available")

---

.. _config-provider:

ConfigProvider
--------------

Load and access dataset configurations (YAML-based).

.. autoclass:: mobility_datasets.config.provider.ConfigProvider
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

**Example - List available datasets:**

.. code-block:: python

    from mobility_datasets.config.provider import ConfigProvider

    provider = ConfigProvider()
    datasets = provider.list_datasources()
    # Output: ['kitti', 'nuscenes', 'waymo']

**Example - Get dataset configuration:**

.. code-block:: python

    provider = ConfigProvider()
    config = provider.get_from_datasource("kitti")

    # Access metadata
    print(config.metadata.name)
    # Output: The KITTI Vision Benchmark Suite

    # List collections
    for collection in config.collections:
        print(f"{collection.id}: {len(collection.sessions)} sessions")

---

Configuration Classes
======================

These classes represent the structure of dataset configurations:

**DatasetConfig**

.. autoclass:: mobility_datasets.config.provider.DatasetConfig
   :members:
   :undoc-members:
   :show-inheritance:

**Collection**

.. autoclass:: mobility_datasets.config.provider.Collection
   :members:
   :undoc-members:
   :show-inheritance:

**Session**

.. autoclass:: mobility_datasets.config.provider.Session
   :members:
   :undoc-members:
   :show-inheritance:

**Part**

.. autoclass:: mobility_datasets.config.provider.Part
   :members:
   :undoc-members:
   :show-inheritance:

**DownloadInfo**

.. autoclass:: mobility_datasets.config.provider.DownloadInfo
   :members:
   :undoc-members:
   :show-inheritance:

---

Data Access
===========

After downloading, access data directly from the file system. Helper classes
for reading and parsing data are coming in future releases.

Reading Downloaded Data
-----------------------

Files are organized by dataset:

.. code-block:: text

    ./data/
    ├── kitti/
    │   ├── raw_data/               # Raw sensor data
    │   │   └── 2011_09_26/
    │   │       └── 2011_09_26_drive_0001/
    │   │           ├── oxts/       # GPS/IMU
    │   │           ├── image_2/    # Left camera
    │   │           ├── image_3/    # Right camera
    │   │           └── velodyne/   # LiDAR
    │   └── dataset/
    │       ├── poses/              # Ground truth
    │       ├── calib/              # Calibration
    │       └── tracklets/          # Object tracking

**Example - Read OXTS (GPS/IMU) data:**

.. code-block:: python

    import numpy as np
    from pathlib import Path

    # Load GPS/IMU data
    oxts_dir = Path("./data/kitti/raw_data/2011_09_26/2011_09_26_drive_0001/oxts/data")
    oxts_files = sorted(oxts_dir.glob("*.txt"))

    # Read all frames
    oxts_data = []
    for f in oxts_files:
        data = np.loadtxt(f)
        oxts_data.append(data)

    oxts_data = np.array(oxts_data)
    print(f"Loaded {len(oxts_data)} frames")

    # Access specific fields
    latitude = oxts_data[:, 0]      # Index 0
    longitude = oxts_data[:, 1]     # Index 1
    altitude = oxts_data[:, 2]      # Index 2
    roll = oxts_data[:, 3]          # Index 3 (radians)
    pitch = oxts_data[:, 4]         # Index 4 (radians)
    yaw = oxts_data[:, 5]           # Index 5 (radians)

**Example - Read ground truth poses:**

.. code-block:: python

    import numpy as np
    from pathlib import Path

    # Load poses for sequence 00
    poses_file = Path("./data/kitti/dataset/poses/00.txt")
    poses_flat = np.loadtxt(poses_file)

    # Reshape to (N, 3, 4) transformation matrices
    poses = poses_flat.reshape(-1, 3, 4)

    # Extract rotation and translation
    for i, pose in enumerate(poses[:5]):  # First 5 poses
        rotation = pose[:3, :3]         # 3x3 rotation matrix
        translation = pose[:3, 3]        # 3x1 position vector
        print(f"Frame {i}: position = {translation}")

OXTS Data Format
----------------

OXTS files contain 30 space-separated values per frame:

.. list-table::
   :header-rows: 1
   :widths: 8 35 12 12

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
     - Additional sensor data
     - various
     - float64

Pose Data Format
----------------

Pose files contain 12 values per frame (3x4 transformation matrix):

.. code-block:: text

    r11 r12 r13 tx
    r21 r22 r23 ty
    r31 r32 r33 tz

Where:

- **r11...r33** — 3x3 rotation matrix
- **tx, ty, tz** — 3x1 translation vector

---

Complete Workflow Example
=========================

Download data and analyze it:

.. code-block:: python

    from mobility_datasets.core.downloader import DatasetDownloader
    import numpy as np
    from pathlib import Path

    # Step 1: Initialize downloader
    downloader = DatasetDownloader(dataset="kitti", data_dir="./data")

    # Step 2: Check size before downloading
    size_info = downloader.get_download_size(
        collection_id="city",
        sessions=["2011_09_26_drive_0001"]
    )
    print(f"Will download: {size_info['total_readable']}")

    # Step 3: Download
    downloader.download(
        collection_id="city",
        sessions=["2011_09_26_drive_0001"]
    )

    # Step 4: Access downloaded data
    oxts_dir = Path("./data/kitti/raw_data/2011_09_26/"
                    "2011_09_26_drive_0001/oxts/data")
    oxts_files = sorted(oxts_dir.glob("*.txt"))

    # Load GPS/IMU data
    oxts_data = np.array([np.loadtxt(f) for f in oxts_files])

    # Extract trajectory
    lats = oxts_data[:, 0]
    lons = oxts_data[:, 1]
    alts = oxts_data[:, 2]

    print(f"Trajectory: {len(lats)} frames")
    print(f"Lat range: {lats.min():.6f} to {lats.max():.6f}")
    print(f"Lon range: {lons.min():.6f} to {lons.max():.6f}")

---

Coming Soon
===========

These modules are planned for future releases:

Data Readers
------------

High-level API for reading and parsing data:

.. code-block:: python

    # Planned API
    from mobility_datasets.readers import KITTIReader

    reader = KITTIReader(data_dir="./data/kitti")

    # Load sequence as structured data
    oxts = reader.load_oxts(sequence="00")
    poses = reader.load_poses(sequence="00")

    # Access with named attributes
    for frame in oxts[:5]:
        print(f"GPS: {frame.lat}, {frame.lon}")
        print(f"Orientation: roll={frame.roll}, pitch={frame.pitch}, yaw={frame.yaw}")

Coordinate Transformations
---------------------------

Transform between coordinate frames:

.. code-block:: python

    # Planned API
    from mobility_datasets.coordinates import CoordinateTransformer

    transformer = CoordinateTransformer()

    # Transform from camera frame to ENU (East-North-Up)
    pose_enu = transformer.transform(
        pose_camera,
        from_frame="CAMERA",
        to_frame="ENU"
    )

Visualization
-------------

Plot trajectories and sensor data:

.. code-block:: python

    # Planned API
    from mobility_datasets.visualization import plot_trajectory, plot_point_cloud

    plot_trajectory(ground_truth, estimated,
                   title="EKF Localization")

    plot_point_cloud(lidar_data, pose)

Metrics and Evaluation
----------------------

Calculate performance metrics:

.. code-block:: python

    # Planned API
    from mobility_datasets.metrics import TrajectoryMetrics

    metrics = TrajectoryMetrics(ground_truth, estimated)
    print(f"Position RMSE: {metrics.position_rmse():.2f} m")
    print(f"Orientation RMSE: {metrics.orientation_rmse():.2f} rad")
    print(f"ATE: {metrics.absolute_trajectory_error():.2f} m")

---

See Also
========

- :doc:`../quickstart/index` - Quick start guide with examples
- :doc:`../guides/kitti_dataset` - KITTI dataset structure and details
- :doc:`../cli/index` - Command-line interface reference
