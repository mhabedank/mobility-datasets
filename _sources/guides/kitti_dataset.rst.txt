================================================================================
KITTI Dataset Overview
================================================================================

The KITTI Vision Benchmark Suite is one of the most influential datasets for autonomous driving research, providing synchronized multi-modal sensor data for various computer vision and robotics tasks.

.. contents::
   :local:
   :depth: 2

---

Dataset Information
-------------------

Overview
^^^^^^^^

The KITTI (Karlsruhe Institute of Technology and Toyota Technological Institute at Chicago) dataset was created to advance computer vision and robotic algorithms for autonomous driving. It contains real-world traffic scenarios recorded in and around Karlsruhe, Germany.

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
- 4× Edmund Optics lenses (4mm, ~90° horizontal FOV, ~35° vertical ROI)
- Stereo baseline: ~54 cm for both grayscale and color pairs
- Frame rate: ~10 Hz (triggered by Velodyne)

**3D LiDAR:**

- 1× Velodyne HDL-64E rotating 3D laser scanner
- 64 beams, 0.09° angular resolution
- Rotation speed: 10 Hz
- Range: 120 m
- Accuracy: 2 cm distance
- Point cloud density: ~100,000 points/scan (~1.3M points/second)
- Field of view: 360° horizontal, 26.8° vertical

**GPS/IMU:**

- 1× OXTS RT3003 inertial navigation system
- 6-axis IMU (3-axis gyroscope + 3-axis accelerometer)
- Frequency: 100 Hz
- GPS: L1/L2 RTK (Real-Time Kinematic) corrections
- Position accuracy: <10 cm (with RTK), 0.02 m resolution
- Orientation accuracy: 0.1° resolution

Available Benchmarks
^^^^^^^^^^^^^^^^^^^^

The KITTI dataset supports multiple computer vision tasks:

- **Stereo Vision** (2012/2015): 194/200 stereo pairs with ground truth disparities
- **Optical Flow** (2012/2015): Semi-dense ground truth for motion estimation
- **Visual Odometry/SLAM:** 22 sequences (11 training, 11 test) with accurate trajectories
- **Object Detection/Tracking:** 7,481 training + 7,518 test images with 3D bounding boxes
- **Semantic Segmentation:** Pixel-level and instance-level annotations
- **Depth Prediction/Completion:** LiDAR-based depth maps
- **Road/Lane Detection:** Road surface segmentation

For sensor fusion applications, the **Odometry Benchmark** is most relevant as it provides:

- Ground truth 6-DOF poses from RTK-GPS/IMU
- Raw GPS/IMU measurements (OXTS data)
- Synchronized camera images
- LiDAR point clouds

---

Licensing and Citation
----------------------

License
^^^^^^^

The KITTI dataset is distributed under the **Creative Commons Attribution-NonCommercial-ShareAlike 3.0 License** (CC BY-NC-SA 3.0).

This means:

- ✓ **Attribution:** You must cite the original authors
- ✓ **Share-Alike:** Derivative works must use the same license
- ✗ **Non-Commercial:** Commercial use is not permitted
- ✓ **Academic Use:** Freely available for research and education

.. important::

   The KITTI dataset is **made available for academic use only**. Commercial applications require permission from the dataset creators.

Required Citations
^^^^^^^^^^^^^^^^^^

When using the KITTI dataset, you must cite the appropriate papers:

**For Odometry/Stereo/Flow/Object Detection/Tracking:**

.. code-block:: bibtex

   @inproceedings{Geiger2012CVPR,
     author = {Andreas Geiger and Philip Lenz and Raquel Urtasun},
     title = {Are we ready for Autonomous Driving?
              The KITTI Vision Benchmark Suite},
     booktitle = {Conference on Computer Vision and
                  Pattern Recognition (CVPR)},
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

**Official Website:** http://www.cvlibs.net/datasets/kitti/

---

Dataset Structure
-----------------

Directory Organization
^^^^^^^^^^^^^^^^^^^^^^

The KITTI dataset is organized into two main components:

.. code-block:: text

   kitti/
   ├── dataset/                    # Processed benchmark data
   │   ├── poses/                  # Ground truth poses (odometry)
   │   │   ├── 00.txt              # Sequence 00 poses
   │   │   ├── 01.txt              # Sequence 01 poses
   │   │   └── ...                 # Sequences 02-10
   │   └── sequences/              # Odometry sequences
   │       ├── 00/                 # Sequence 00
   │       │   ├── image_0/        # Left grayscale camera
   │       │   ├── image_1/        # Right grayscale camera
   │       │   ├── image_2/        # Left color camera
   │       │   ├── image_3/        # Right color camera
   │       │   ├── calib.txt       # Calibration data
   │       │   └── times.txt       # Frame timestamps
   │       └── 01/                 # Sequence 01
   │           └── ...
   │
   └── raw_data/                   # Raw sensor data
       └── 2011_10_03/             # Recording date
           ├── 2011_10_03_drive_0027_sync/  # Drive (→ Sequence 00)
           │   ├── image_00/       # Cameras
           │   ├── image_01/
           │   ├── image_02/
           │   ├── image_03/
           │   ├── oxts/           # GPS/IMU data (100 Hz)
           │   │   ├── data/
           │   │   │   ├── 0000000000.txt
           │   │   │   └── ...
           │   │   ├── dataformat.txt
           │   │   └── timestamps.txt
           │   └── velodyne_points/ # LiDAR scans
           ├── 2011_10_03_drive_0042_sync/  # Drive (→ Sequence 01)
           └── calib_*.txt         # Calibration files

Odometry Sequences
^^^^^^^^^^^^^^^^^^

The odometry benchmark contains 22 sequences (00-21):

- **Training sequences:** 00-10 (ground truth available)
- **Test sequences:** 11-21 (ground truth withheld for evaluation)

.. list-table:: Odometry Sequence Details
   :header-rows: 1
   :widths: 10 30 15 15 30

   * - Seq
     - Raw Data Drive
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
     - Urban + Residential
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
     - Urban + Residential
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

---

Data Formats
------------

Ground Truth Poses (``dataset/poses/``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**File Format:** Plain text files (e.g., ``00.txt``, ``01.txt``)

**Content:** One 3×4 transformation matrix per line (12 values)

**Structure:** ``[R | t]`` where:

- ``R``: 3×3 rotation matrix (orientation)
- ``t``: 3×1 translation vector (position)

**Format per line:**

.. code-block:: text

   r11 r12 r13 tx r21 r22 r23 ty r31 r32 r33 tz

**Example (Frame 0 - Start position):**

.. code-block:: text

   1.000000e+00 9.043680e-12 2.326809e-11 5.551115e-17 ...

Represents the matrix:

.. math::

   T_0 = \begin{bmatrix}
   1.0 & 0.0 & 0.0 & 0.0 \\
   0.0 & 1.0 & 0.0 & 0.0 \\
   0.0 & 0.0 & 1.0 & 0.0
   \end{bmatrix}

**Coordinate System:**

- **X:** Right
- **Y:** Down
- **Z:** Forward

**Accuracy:** <10 cm (RTK-GPS corrected)

**Frequency:** ~10 Hz (matches camera frame rate)

OXTS GPS/IMU Data (``raw_data/.../oxts/``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Location:** ``raw_data/{date}/{drive}_sync/oxts/data/``

**File Format:** Plain text files, one per frame (e.g., ``0000000000.txt``)

**Content:** 30 space-separated values per line

**Frequency:** 100 Hz (resampled to ~10 Hz for synchronized data)

**Accuracy:**
- Position: 0.02 m (RTK-GPS)
- Orientation: 0.1°

See :ref:`oxts-data-dictionary` for detailed field descriptions.

Velodyne LiDAR (``raw_data/.../velodyne_points/``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**File Format:** Binary files (``*.bin``)

**Content:** (x, y, z, reflectance) point cloud

**Data Type:** 4× ``float32`` (4 bytes each = 16 bytes per point)

**Structure:** Flat array ``[x0, y0, z0, r0, x1, y1, z1, r1, ...]``

**Point Count:** ~100,000 points per scan

**Reading in Python:**

.. code-block:: python

   import numpy as np

   # Read point cloud
   points = np.fromfile('0000000000.bin', dtype=np.float32)
   points = points.reshape((-1, 4))  # Shape: (N, 4)

   # Extract components
   xyz = points[:, :3]        # 3D coordinates
   reflectance = points[:, 3] # Intensity values

**Coordinate System:**

- **X:** Forward
- **Y:** Left
- **Z:** Up

Timestamps
^^^^^^^^^^

**Location:** ``timestamps.txt`` in each sensor folder

**Format:** One timestamp per line

**Example:**

.. code-block:: text

   2011-10-03 09:47:51.802280320
   2011-10-03 09:47:51.902263040
   ...

**Precision:** Nanosecond accuracy

**Synchronization:**
- Cameras triggered by Velodyne at ~10 Hz
- GPS/IMU closest measurement selected from 100 Hz stream

---

.. _oxts-data-dictionary:

OXTS Data Dictionary
--------------------

Each OXTS file contains 30 values representing GPS position, orientation, velocities, accelerations, and sensor metadata.

Coordinate Systems
^^^^^^^^^^^^^^^^^^

OXTS data uses two coordinate systems:

**1. Vehicle Body Frame (x, y, z):**

- **x:** Forward (vehicle front)
- **y:** Left
- **z:** Up (vehicle top)

**2. Earth-Surface Tangent Plane (f, l, u):**

- **f:** Forward (tangent to earth surface)
- **l:** Leftward (parallel to earth surface)
- **u:** Upward (perpendicular to earth surface)

Field Descriptions
^^^^^^^^^^^^^^^^^^

.. list-table:: OXTS Data Fields (30 values per frame)
   :header-rows: 1
   :widths: 5 20 15 15 45

   * - #
     - Field Name
     - Unit
     - Frame
     - Description
   * - 1
     - ``lat``
     - deg
     - WGS84
     - Latitude of OXTS unit
   * - 2
     - ``lon``
     - deg
     - WGS84
     - Longitude of OXTS unit
   * - 3
     - ``alt``
     - m
     - WGS84
     - Altitude above WGS84 ellipsoid
   * - 4
     - ``roll``
     - rad
     - Vehicle
     - Roll angle (0=level, +left up, −right up), range: [−π, π]
   * - 5
     - ``pitch``
     - rad
     - Vehicle
     - Pitch angle (0=level, +nose up, −nose down), range: [−π, π]
   * - 6
     - ``yaw``
     - rad
     - Vehicle
     - Heading (0=east, +counterclockwise), range: [−π, π]
   * - 7
     - ``vn``
     - m/s
     - Earth
     - Velocity north
   * - 8
     - ``ve``
     - m/s
     - Earth
     - Velocity east
   * - 9
     - ``vf``
     - m/s
     - Earth
     - Forward velocity (parallel to earth surface)
   * - 10
     - ``vl``
     - m/s
     - Earth
     - Leftward velocity (parallel to earth surface)
   * - 11
     - ``vu``
     - m/s
     - Earth
     - Upward velocity (perpendicular to earth surface)
   * - 12
     - ``ax``
     - m/s²
     - Vehicle
     - Acceleration in x (forward direction)
   * - 13
     - ``ay``
     - m/s²
     - Vehicle
     - Acceleration in y (left direction)
   * - 14
     - ``az``
     - m/s²
     - Vehicle
     - Acceleration in z (up direction)
   * - 15
     - ``af``
     - m/s²
     - Earth
     - Forward acceleration
   * - 16
     - ``al``
     - m/s²
     - Earth
     - Leftward acceleration
   * - 17
     - ``au``
     - m/s²
     - Earth
     - Upward acceleration
   * - 18
     - ``wx``
     - rad/s
     - Vehicle
     - Angular rate around x (roll rate)
   * - 19
     - ``wy``
     - rad/s
     - Vehicle
     - Angular rate around y (pitch rate)
   * - 20
     - ``wz``
     - rad/s
     - Vehicle
     - Angular rate around z (yaw rate)
   * - 21
     - ``wf``
     - rad/s
     - Earth
     - Angular rate around forward axis
   * - 22
     - ``wl``
     - rad/s
     - Earth
     - Angular rate around leftward axis
   * - 23
     - ``wu``
     - rad/s
     - Earth
     - Angular rate around upward axis
   * - 24
     - ``pos_accuracy``
     - m
     - —
     - Position accuracy (north/east)
   * - 25
     - ``vel_accuracy``
     - m/s
     - —
     - Velocity accuracy (north/east)
   * - 26
     - ``navstat``
     - —
     - —
     - Navigation status (quality indicator)
   * - 27
     - ``numsats``
     - —
     - —
     - Number of satellites tracked
   * - 28
     - ``posmode``
     - —
     - —
     - Position mode of primary GPS receiver
   * - 29
     - ``velmode``
     - —
     - —
     - Velocity mode of primary GPS receiver
   * - 30
     - ``orimode``
     - —
     - —
     - Orientation mode of IMU

.. note::

   **Missing Data:** Communication outages (~1 second) are linearly interpolated, with fields 28-30 set to ``-1`` to indicate missing information.

Reading OXTS Data
^^^^^^^^^^^^^^^^^

**Python Example:**

.. code-block:: python

   import numpy as np

   # Read single OXTS measurement
   oxts_file = 'raw_data/2011_10_03/drive_0027_sync/oxts/data/0000000000.txt'
   data = np.loadtxt(oxts_file)

   # Extract specific fields
   lat, lon, alt = data[0], data[1], data[2]
   roll, pitch, yaw = data[3], data[4], data[5]
   ax, ay, az = data[11], data[12], data[13]  # Vehicle frame
   wx, wy, wz = data[17], data[18], data[19]  # Angular rates

   print(f"Position: {lat:.6f}°, {lon:.6f}°, {alt:.2f}m")
   print(f"Orientation: roll={roll:.3f}, pitch={pitch:.3f}, yaw={yaw:.3f}")
   print(f"IMU acc: ({ax:.3f}, {ay:.3f}, {az:.3f}) m/s²")

---

Data Access
-----------

Official Downloads
^^^^^^^^^^^^^^^^^^

**Primary Source:** http://www.cvlibs.net/datasets/kitti/

**AWS S3 (Public Access):**

.. code-block:: bash

   # List available data
   aws s3 ls --no-sign-request s3://avg-kitti/

   # Download specific sequences
   aws s3 sync --no-sign-request \
     s3://avg-kitti/data_odometry_poses/dataset/poses/ \
     ./kitti/dataset/poses/

**Registration Required:** Yes (free, for academic use tracking)

Available Downloads
^^^^^^^^^^^^^^^^^^^

For sensor fusion applications, download:

1. **Odometry Ground Truth Poses** (~1 MB)
   - Contains: 3×4 pose matrices for sequences 00-10

2. **Odometry Sequences** (~52 GB for all 22 sequences)
   - Contains: Camera images, calibration, timestamps

3. **Raw Data** (varies by sequence, ~4-10 GB each)
   - Contains: OXTS (GPS/IMU), Velodyne LiDAR, cameras
   - Download specific dates/drives as needed

.. tip::

   Start with **Sequence 00** (~4 GB raw data) for initial development and testing. It provides a good balance of duration (7.5 min) and scenario complexity (residential area).

---

See Also
--------

- :doc:`../quickstart/02_download_data` - Step-by-step download instructions
- :doc:`coordinate_systems` - Understanding KITTI coordinate frames
- :doc:`kitti_workflow` - Complete workflow for sensor fusion

**External Resources:**

- `KITTI Official Documentation <http://www.cvlibs.net/datasets/kitti/setup.php>`_
- `PyKITTI Library <https://github.com/utiasSTARS/pykitti>`_ - Python tools for KITTI
- `KITTI Odometry Benchmark Paper <http://www.cvlibs.net/publications/Geiger2012CVPR.pdf>`_
