================================================================================
KITTI Dataset Guide
================================================================================

KITTI (Karlsruhe Institute of Technology and Toyota Technological Institute at Chicago) is one of the most influential datasets for autonomous driving research. This guide shows how to download, access, and work with KITTI data using mobility-datasets.

.. contents::
   :local:
   :depth: 2

---

Dataset Overview
-----------------

Introduction
^^^^^^^^^^^^

The KITTI Vision Benchmark Suite contains real-world traffic scenarios recorded in and around Karlsruhe, Germany. It provides synchronized multi-modal sensor data including cameras, LiDAR, and GPS/IMU measurements.

**Key Characteristics:**

- **Recording Platform:** Modified VW Passat B6 station wagon
- **Total Duration:** ~6 hours of driving data
- **Recording Frequency:** 10-100 Hz depending on sensor
- **Data Volume:** >50 GB (raw data significantly larger)
- **Environments:** Urban, suburban, rural, and highway scenarios
- **Recording Dates:** September 26, 28, 29, 30, 2011 and October 3, 2011

Sensor Suite
^^^^^^^^^^^^

The recording platform was equipped with:

**Cameras:**

- 2× PointGray Flea2 grayscale cameras (1392×512 px, global shutter)
- 2× PointGray Flea2 color cameras (1392×512 px, global shutter)
- 4× Edmund Optics lenses (4mm, ~90° horizontal FOV)
- Stereo baseline: ~54 cm for both grayscale and color pairs
- Frame rate: ~10 Hz

**3D LiDAR:**

- 1× Velodyne HDL-64E rotating 3D laser scanner
- 64 beams, 0.09° angular resolution
- Rotation speed: 10 Hz
- Range: 120 m
- Point cloud density: ~100,000 points/scan

**GPS/IMU:**

- 1× OXTS RT3003 inertial navigation system
- 6-axis IMU (3-axis gyroscope + 3-axis accelerometer)
- Frequency: 100 Hz
- GPS: L1/L2 RTK (Real-Time Kinematic)
- Position accuracy: <10 cm (with RTK)

---

Downloading KITTI
-----------------

Quick Start
^^^^^^^^^^^

Show available KITTI collections and their sizes:

.. code-block:: bash

   mds info kitti

Estimate download size before committing to download:

.. code-block:: bash

   mds download kitti --estimate-only

Download a specific session from raw_data collection:

.. code-block:: bash

   mds download kitti --collection raw_data --sessions 2011_09_26_drive_0001

Download multiple sessions:

.. code-block:: bash

   mds download kitti --collection raw_data --sessions 2011_09_26_drive_0001,2011_09_26_drive_0002

Download to a custom directory:

.. code-block:: bash

   mds download kitti --collection raw_data --data-dir /mnt/datasets

CLI Reference
^^^^^^^^^^^^^

**Show dataset info:**

.. code-block:: bash

   mds info kitti [OPTIONS]

Options:

- ``-c, --collection <name>`` — Show info for specific collection only
- ``--verify`` — Verify files are available on remote servers (slow)
- ``--timeout <seconds>`` — Timeout for verification requests (default: 10)

**Example:**

.. code-block:: bash

   # Show all collections and their sizes
   mds info kitti

   # Show only raw_data collection
   mds info kitti --collection raw_data

   # Verify all files are accessible
   mds info kitti --verify

---

**Download dataset files:**

.. code-block:: bash

   mds download kitti [OPTIONS]

Options:

- ``-c, --collection <name>`` — Collection to download (e.g., ``raw_data``, ``synced_data``)
- ``-s, --sessions <ids>`` — Comma-separated session IDs. Download all sessions if not specified
- ``--with-optional`` — Include optional dataset parts
- ``--keep-zip`` — Keep archive files after extraction
- ``--estimate-only`` — Show download size without downloading
- ``--data-dir <path>`` — Download directory (default: ``./data``)

**Examples:**

.. code-block:: bash

   # Download single session from raw_data
   mds download kitti --collection raw_data --sessions 2011_09_26_drive_0001

   # Download multiple sessions
   mds download kitti -c raw_data -s 2011_09_26_drive_0001,2011_09_26_drive_0002

   # Estimate size first (dry-run)
   mds download kitti --collection raw_data --estimate-only

   # Download all sessions in collection
   mds download kitti --collection raw_data

   # Download all collections
   mds download kitti

   # Keep archives for backup
   mds download kitti --collection raw_data --keep-zip

   # Custom download location
   mds download kitti --data-dir /mnt/large_disk

.. tip::

   Always run with ``--estimate-only`` first to see how much disk space is required. Then download to a location with enough free space.

---

Available Collections
^^^^^^^^^^^^^^^^^^^^^

KITTI has several collections organized by data type:

.. list-table:: KITTI Collections
   :header-rows: 1
   :widths: 25 60 15

   * - Collection ID
     - Description
     - Typical Size
   * - ``raw_data``
     - Raw sensor data (OXTS GPS/IMU, camera images, point clouds)
     - 4-10 GB per session
   * - ``synced_data``
     - Time-synchronized processed data (images, point clouds, IMU)
     - 1-3 GB per session
   * - ``poses``
     - Ground truth trajectories (Odometry Benchmark)
     - ~5 MB total
   * - ``calib``
     - Calibration files for camera-LiDAR alignment
     - ~10 MB total

**Available Sessions by Collection:**

To see all available sessions in a collection:

.. code-block:: bash

   mds info kitti --collection raw_data

This will list all available session IDs that you can reference with ``--sessions``.

---

Python API
----------

Using the Downloader
^^^^^^^^^^^^^^^^^^^^

**Import:**

.. code-block:: python

   from mobility_datasets import DatasetDownloader

**Initialize:**

.. code-block:: python

   downloader = DatasetDownloader(dataset="kitti", data_dir="./data")

**Check info before downloading:**

.. code-block:: python

   # Get download size estimate
   size_info = downloader.get_download_size(
       collection_id="raw_data",
       sessions=["2011_09_26_drive_0001"]
   )
   print(f"Total size: {size_info['total_readable']}")

**Download specific sessions:**

.. code-block:: python

   # Download single session
   downloader.download(
       collection_id="raw_data",
       sessions=["2011_09_26_drive_0001"],
       keep_zip=False
   )

   # Download multiple sessions
   downloader.download(
       collection_id="raw_data",
       sessions=["2011_09_26_drive_0001", "2011_09_26_drive_0002"],
       keep_zip=False
   )

**Download all sessions in a collection:**

.. code-block:: python

   # Download entire raw_data collection
   downloader.download(
       collection_id="raw_data",
       sessions=downloader.config.get_collection_or_raise("raw_data").session_ids(),
       keep_zip=False
   )

**Download all data:**

.. code-block:: python

   # Download all collections and sessions
   downloader.download_all(keep_zip=False)

**Check file availability:**

.. code-block:: python

   # Verify all files still exist on S3 before downloading
   status = downloader.health_check()
   unavailable = [k for k, v in status.items() if not v]
   if unavailable:
       print(f"Warning: {len(unavailable)} files unavailable")
   else:
       print("All files available!")

Complete Example
^^^^^^^^^^^^^^^^

.. code-block:: python

   from mobility_datasets import DatasetDownloader
   from pathlib import Path
   import numpy as np

   # 1. Initialize and check what's available
   downloader = DatasetDownloader(dataset="kitti", data_dir="./data")

   # 2. See how big the download is
   size_info = downloader.get_download_size(
       collection_id="raw_data",
       sessions=["2011_09_26_drive_0001"]
   )
   print(f"Download size: {size_info['total_readable']}")

   # 3. Download the session
   downloader.download(
       collection_id="raw_data",
       sessions=["2011_09_26_drive_0001"],
       keep_zip=False
   )

   # 4. Load poses
   poses_file = Path("./data/kitti/dataset/poses/00.txt")
   poses = np.loadtxt(poses_file)
   poses = poses.reshape(-1, 3, 4)
   print(f"Loaded {len(poses)} poses")

   # 5. Load OXTS data
   oxts_dir = Path("./data/kitti/raw_data/2011_09_26/2011_09_26_drive_0001_sync/oxts/data")
   oxts_files = sorted(oxts_dir.glob("*.txt"))
   print(f"Found {len(oxts_files)} OXTS measurements")

   for oxts_file in oxts_files[:5]:  # First 5 frames
       data = np.loadtxt(oxts_file)
       lat, lon, alt = data[0], data[1], data[2]
       print(f"Frame {oxts_file.stem}: {lat:.6f}°, {lon:.6f}°, {alt:.2f}m")

---

Data Formats
------------

Ground Truth Poses
^^^^^^^^^^^^^^^^^^

**Location:** ``dataset/poses/00.txt`` (and 01.txt, 02.txt, etc. for other sequences)

**Format:** One 3×4 transformation matrix per line

Each line contains 12 space-separated values representing a 3×4 matrix:

.. code-block:: text

   r11 r12 r13 tx r21 r22 r23 ty r31 r32 r33 tz

Where:

- ``R`` (3×3): Rotation matrix (orientation)
- ``t`` (3×1): Translation vector (position)

**Python:**

.. code-block:: python

   import numpy as np

   # Read poses
   poses = np.loadtxt("dataset/poses/00.txt")
   poses = poses.reshape(-1, 3, 4)  # Shape: (N_frames, 3, 4)

   # Access individual pose
   pose = poses[0]
   rotation = pose[:3, :3]    # 3×3 matrix
   position = pose[:3, 3]     # 3×1 vector

   print(f"Position: {position}")
   # Output: [-1.64048222e-02  5.10477959e-03 -8.61842105e-02]

**Coordinate System:**

- **X:** Right
- **Y:** Down
- **Z:** Forward

**Frequency:** ~10 Hz
**Accuracy:** <10 cm (RTK-GPS corrected)

OXTS GPS/IMU Data
^^^^^^^^^^^^^^^^^^

**Location:** ``raw_data/{date}/{drive}_sync/oxts/data/*.txt``

Example: ``raw_data/2011_09_26/2011_09_26_drive_0001_sync/oxts/data/0000000000.txt``

**Format:** One measurement per line, 30 space-separated values

**Frequency:** 100 Hz raw, ~10 Hz when synchronized

**Python:**

.. code-block:: python

   import numpy as np

   # Read single measurement
   oxts = np.loadtxt("oxts/data/0000000000.txt")

   # Extract key fields (see field reference below)
   lat, lon, alt = oxts[0], oxts[1], oxts[2]
   roll, pitch, yaw = oxts[3], oxts[4], oxts[5]
   vn, ve, vf = oxts[6], oxts[7], oxts[8]  # Velocities
   ax, ay, az = oxts[11], oxts[12], oxts[13]  # Accelerations
   wx, wy, wz = oxts[17], oxts[18], oxts[19]  # Angular rates

   print(f"Position: {lat:.6f}°N, {lon:.6f}°E, {alt:.2f}m")
   print(f"Orientation: roll={roll:.3f} rad, pitch={pitch:.3f} rad, yaw={yaw:.3f} rad")

OXTS Field Reference
^^^^^^^^^^^^^^^^^^^^

Each OXTS line contains 30 values:

.. list-table:: OXTS Data Fields
   :header-rows: 1
   :widths: 5 25 20 50

   * - Index
     - Field
     - Unit
     - Description
   * - 0-2
     - lat, lon, alt
     - deg, deg, m
     - WGS84 position (latitude, longitude, altitude)
   * - 3-5
     - roll, pitch, yaw
     - rad
     - Vehicle orientation (vehicle frame)
   * - 6-8
     - vn, ve, vf
     - m/s
     - Velocity (north, east, forward on earth surface)
   * - 9-10
     - vl, vu
     - m/s
     - Velocity (left, up on earth surface)
   * - 11-13
     - ax, ay, az
     - m/s²
     - Acceleration (vehicle frame: forward, left, up)
   * - 14-16
     - af, al, au
     - m/s²
     - Acceleration (earth frame: forward, left, up)
   * - 17-19
     - wx, wy, wz
     - rad/s
     - Angular rate (vehicle frame)
   * - 20-22
     - wf, wl, wu
     - rad/s
     - Angular rate (earth frame)
   * - 23-25
     - pos_accuracy, vel_accuracy, navstat
     - m, m/s, —
     - GPS accuracy and navigation status
   * - 26-29
     - numsats, posmode, velmode, orimode
     - —
     - Satellite count and mode indicators

Velodyne LiDAR
^^^^^^^^^^^^^^

**Location:** ``raw_data/{date}/{drive}_sync/velodyne_points/data/*.bin``

**Format:** Binary files with (x, y, z, reflectance) point clouds

**Data Type:** 4× ``float32`` (16 bytes per point)

**Python:**

.. code-block:: python

   import numpy as np

   # Read point cloud
   points = np.fromfile("velodyne_points/data/0000000000.bin", dtype=np.float32)
   points = points.reshape(-1, 4)  # Shape: (N_points, 4)

   # Extract coordinates and intensity
   xyz = points[:, :3]        # 3D positions
   reflectance = points[:, 3] # Intensity values

   print(f"Cloud contains {len(points)} points")

**Coordinate System:**

- **X:** Forward
- **Y:** Left
- **Z:** Up

Camera Images & Timestamps
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Location:** ``sequences/{seq_id}/image_0/``, ``image_1/``, ``image_2/``, ``image_3/``

**Format:** PNG images, one per frame

**Cameras:**

- ``image_0/``: Left grayscale
- ``image_1/``: Right grayscale
- ``image_2/``: Left color
- ``image_3/``: Right color

**Python:**

.. code-block:: python

   from pathlib import Path
   from PIL import Image

   # List all left grayscale images
   images = sorted(Path("sequences/00/image_0").glob("*.png"))

   # Load first image
   img = Image.open(images[0])
   print(f"Image size: {img.size}")  # Output: (1392, 512)

---

Working with Sequences
----------------------

Available Sequences
^^^^^^^^^^^^^^^^^^^

KITTI Odometry Benchmark contains 22 sequences:

.. list-table:: Odometry Sequences
   :header-rows: 1
   :widths: 8 25 12 12 20

   * - Seq
     - Raw Drive
     - Frames
     - Distance
     - Environment
   * - 00
     - 2011_10_03_drive_0027
     - 4,541
     - 3.7 km
     - Residential
   * - 01
     - 2011_10_03_drive_0042
     - 1,101
     - 1.1 km
     - Highway
   * - 02
     - 2011_10_03_drive_0034
     - 4,661
     - 5.1 km
     - Urban
   * - 03
     - 2011_09_26_drive_0067
     - 801
     - 0.6 km
     - Residential
   * - 04
     - 2011_09_30_drive_0016
     - 271
     - 0.4 km
     - Road
   * - 05
     - 2011_09_30_drive_0018
     - 2,761
     - 2.2 km
     - Residential
   * - 06
     - 2011_09_30_drive_0020
     - 1,101
     - 1.2 km
     - Residential
   * - 07
     - 2011_09_30_drive_0027
     - 1,101
     - 0.7 km
     - Residential
   * - 08
     - 2011_09_30_drive_0028
     - 4,071
     - 3.4 km
     - Urban
   * - 09
     - 2011_09_30_drive_0033
     - 1,591
     - 1.7 km
     - Residential
   * - 10
     - 2011_09_30_drive_0034
     - 1,201
     - 0.9 km
     - Residential

**Training Sequences:** 00-10 (ground truth available)

**Test Sequences:** 11-21 (ground truth withheld)

Sequence 00 Example
^^^^^^^^^^^^^^^^^^^

Start with Sequence 00 for development. It provides:

- **Duration:** 7.5 minutes
- **Frames:** 4,541 images @ 10 Hz
- **Environment:** Typical residential driving
- **Data Size:** ~4 GB (raw_data)

**Download via CLI:**

.. code-block:: bash

   mds download kitti --collection raw_data --sessions 2011_10_03_drive_0027

**Download via Python:**

.. code-block:: python

   from mobility_datasets import DatasetDownloader

   downloader = DatasetDownloader(dataset="kitti")
   downloader.download(
       collection_id="raw_data",
       sessions=["2011_10_03_drive_0027"]
   )

**Access in Python:**

.. code-block:: python

   from pathlib import Path
   import numpy as np

   data_dir = Path("./data/kitti")

   # Poses for sequence 00
   poses = np.loadtxt(data_dir / "dataset/poses/00.txt")

   # OXTS for sequence 00 (from raw_data drive 0027)
   oxts_dir = data_dir / "raw_data/2011_10_03/2011_10_03_drive_0027_sync/oxts/data"
   oxts_files = sorted(oxts_dir.glob("*.txt"))

   print(f"Sequence 00: {len(poses)} poses, {len(oxts_files)} OXTS measurements")

---

Licensing and Citation
----------------------

License
^^^^^^^

The KITTI dataset is distributed under the **Creative Commons Attribution-NonCommercial-ShareAlike 3.0 License** (CC BY-NC-SA 3.0).

This means:

- ✓ **Academic Use:** Freely available for research and education
- ✓ **Attribution:** You must cite the original authors
- ✓ **Share-Alike:** Derivative works must use the same license
- ✗ **Commercial Use:** Commercial applications require permission

.. important::

   The KITTI dataset is **made available for academic use only**. Commercial applications require explicit permission from the dataset creators.

Required Citations
^^^^^^^^^^^^^^^^^^

When using KITTI data, cite the appropriate papers:

**For Odometry:**

.. code-block:: bibtex

   @inproceedings{Geiger2012CVPR,
     author = {Andreas Geiger and Philip Lenz and Raquel Urtasun},
     title = {Are we ready for Autonomous Driving?
              The KITTI Vision Benchmark Suite},
     booktitle = {Conference on Computer Vision and Pattern Recognition (CVPR)},
     year = {2012}
   }

**For Raw Dataset:**

.. code-block:: bibtex

   @article{Geiger2013IJRR,
     author = {Andreas Geiger and Philip Lenz and
               Christoph Stiller and Raquel Urtasun},
     title = {Vision meets Robotics: The KITTI Dataset},
     journal = {International Journal of Robotics Research (IJRR)},
     year = {2013}
   }

---

Troubleshooting
---------------

Download Issues
^^^^^^^^^^^^^^^

**Issue:** Download is slow or times out

**Solution:**

.. code-block:: bash

   # Estimate size first
   mds download kitti --collection raw_data --sessions 2011_10_03_drive_0027 --estimate-only

   # Then download with patience
   mds download kitti --collection raw_data --sessions 2011_10_03_drive_0027

**Issue:** "Collection not found"

**Solution:**

.. code-block:: bash

   # Check available collections
   mds info kitti

   # Verify collection name and try again
   mds download kitti --collection raw_data

**Issue:** "Session not found in collection"

**Solution:**

.. code-block:: bash

   # List available sessions for a collection
   mds info kitti --collection raw_data

   # Use exact session ID from the list
   mds download kitti --collection raw_data --sessions 2011_10_03_drive_0027

File Not Found After Download
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue:** After download, data directory is empty or incomplete

**Solution:**

.. code-block:: bash

   # Check what was downloaded
   ls -la ./data/kitti/

   # Run health check to see if files are still available
   mds info kitti --verify

   # If files are available, retry the download
   mds download kitti --collection raw_data

Missing Data in OXTS
^^^^^^^^^^^^^^^^^^^^^

**Issue:** Some OXTS measurements have ``-1`` values

**Note:** This is expected. Communication outages (~1 second) are indicated by ``-1`` in the ``posmode``, ``velmode``, and ``orimode`` fields (indices 28-30).

**Solution:** Interpolate missing values or skip frames with missing data.

---

See Also
--------

- :doc:`../quickstart/02_download_data` — Step-by-step download instructions
- :doc:`coordinate_systems` — Understanding KITTI coordinate frames
- :doc:`../api/index` — Python API reference

**External Resources:**

- `KITTI Official Website <http://www.cvlibs.net/datasets/kitti/>`_
- `KITTI Raw Data Format <http://www.cvlibs.net/datasets/kitti/raw_data.php>`_
- `KITTI Odometry Benchmark <http://www.cvlibs.net/datasets/kitti/eval_odometry.php>`_
