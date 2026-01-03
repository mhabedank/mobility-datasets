================================================================================
User Guides
================================================================================

In-depth guides for working with autonomous driving datasets.

These guides explain concepts, workflows, and best practices for using
mobility datasets in your research, development, or applications.

.. contents::
   :local:
   :depth: 1

---

Getting Started
===============

.. toctree::
   :maxdepth: 1

Start with these guides if you're new to mobility-datasets:

- :doc:`../quickstart/index` - 5-minute quick start
- :doc:`../cli/index` - Command-line interface tutorial

---

Dataset Guides
==============

Learn the structure and use of specific datasets:

KITTI Dataset
-------------

.. toctree::
   :maxdepth: 2

   kitti_dataset

Complete guide to the KITTI Vision Benchmark Suite:

- Dataset collections (city, residential, road)
- Raw sensor data (OXTS, camera, LiDAR)
- Ground truth annotations (poses, calibration)
- GPS/IMU data format (30 fields per frame)
- Pose transformation matrices
- Sequence-to-raw-data mapping
- Working with trajectories
- Coordinate systems and transformations

**Best for:** Understanding KITTI structure, accessing raw data, working with trajectories

nuScenes (Coming Soon)
----------------------

Guide to the nuScenes autonomous driving dataset:

- Collections (mini, trainval, test)
- Data formats (sensor data, annotations, metadata)
- Accessing 3D annotations
- Working with map data
- Using the visualization tools

**Best for:** 3D object detection, nuScenes-specific workflows

Waymo Open Dataset (Coming Soon)
-------------------------------

Guide to Waymo's open autonomous driving dataset:

- Collections and scenarios
- Sensor suite (cameras, LiDAR, radar)
- Data formats and access patterns
- Working with 3D object annotations
- Handling multi-modal sensor data

**Best for:** Multi-sensor fusion, large-scale benchmarks

---

Workflow Guides
===============

Common tasks and workflows with mobility datasets:

Downloading Datasets
--------------------

How to efficiently download datasets for your project:

- Using the CLI for downloads
- Estimating download sizes
- Resuming interrupted downloads
- Managing download locations
- Keeping or removing archives
- Verifying file availability before downloading

**Best for:** Planning downloads, managing disk space, scripting automations

Programmatic Access
-------------------

Using the Python API for data access:

- Initializing `DatasetDownloader`
- Querying available collections and sessions
- Getting dataset configurations
- Size estimation
- Checking file availability
- Error handling and retries

**Best for:** Integration into Python applications, automation scripts

Data Processing Pipelines
-------------------------

Building data processing pipelines with mobility datasets:

- Loading and parsing raw data (OXTS, poses, images)
- Batch processing multiple sessions
- Handling sensor synchronization
- Working with timestamps
- Memory-efficient processing

**Best for:** Research workflows, data analysis, batch processing

Sensor Fusion
-------------

Combining multiple sensor modalities:

- Fusing GPS/IMU (OXTS) with camera data
- Calibration and coordinate transformations
- Handling sensor delays and synchronization
- Implementing Kalman filters (EKF, UKF)
- Evaluating fusion results

**Best for:** Localization, sensor fusion research

Evaluation and Metrics
----------------------

Benchmarking algorithms against ground truth:

- Computing trajectory metrics (RMSE, ATE)
- Evaluating pose estimation accuracy
- Cross-dataset comparison
- Handling outliers and failure cases

**Best for:** Algorithm validation, research papers

---

Conceptual Guides
=================

Deep dives into concepts used across datasets:

Coordinate Systems
------------------

Understanding coordinate frames in autonomous driving datasets:

- Local coordinate frames (camera, vehicle, GPS)
- Global coordinate frames (ENU, ECEF, latitude/longitude)
- Transformation matrices
- Rotation representations (Euler angles, quaternions)
- Working with calibration data

**Best for:** Understanding transformations, implementing coordinate conversions

GPS/IMU Data Processing
-----------------------

Working with inertial measurement data:

- OXTS format and fields
- GPS accuracy and error models
- IMU integration and drift
- Coordinate conversions (WGS84 to local)
- Filtering noisy sensor data

**Best for:** Localization, sensor fusion, trajectory estimation

Ground Truth Annotations
------------------------

Understanding and using ground truth data:

- Pose transformations and SE(3) group
- Calibration files and interpretation
- Timestamp synchronization
- Handling missing or corrupt data
- Verification and validation

**Best for:** Algorithm training, benchmarking

---

Example Workflows
=================

Complete, runnable examples for common tasks:

Example 1: Load and Visualize a Trajectory
-------------------------------------------

Download a KITTI sequence and plot the GPS trajectory.

**Topics:** Download, OXTS data, plotting, coordinate conversion

Example 2: Evaluate a Localization Algorithm
----------------------------------------------

Implement a simple Kalman filter and compare with ground truth.

**Topics:** Pose data, metrics, algorithm evaluation, ground truth

Example 3: Batch Process Multiple Datasets
-------------------------------------------

Process KITTI and nuScenes with a unified interface.

**Topics:** Multiple datasets, batch processing, data access patterns

Example 4: Sensor Fusion Pipeline
----------------------------------

Fuse GPS/IMU with camera data for improved localization.

**Topics:** Sensor fusion, OXTS, calibration, coordinate transforms

---

Troubleshooting
===============

Common issues and solutions:

Download Issues
---------------

**Problem:** Download fails or is slow

**Solutions:**
- Check internet connection and try resuming
- Verify file availability: ``mds info <dataset> --verify``
- Download specific sessions instead of entire collections
- Use ``--estimate-only`` to check size first

See :doc:`../cli/index` for more CLI troubleshooting.

Data Access Issues
------------------

**Problem:** Can't find or read downloaded files

**Solutions:**
- Verify files were extracted: check directory structure
- Use correct path (includes dataset subdirectory)
- Check file permissions
- See Data Access section in :doc:`../api/index`

---

Contributing Guides
===================

We welcome contributions! If you'd like to write or improve a guide:

1. Follow the :doc:`../DOCUMENTATION_STANDARDS`
2. Use English throughout
3. Include runnable code examples
4. Add troubleshooting or "Common Pitfalls" sections
5. Link to related documentation
6. Test all code examples before submitting

See our `CONTRIBUTING.md <https://github.com/mhabedank/mobility-datasets>`_
for the full contribution process.

---

See Also
========

- :doc:`../quickstart/index` - 5-minute quick start
- :doc:`../cli/index` - Command-line reference
- :doc:`../api/index` - Python API documentation
- :doc:`../DOCUMENTATION_STANDARDS` - Writing standards for this project

---

**Last Updated:** 2025-01-03

Have a question? Open an issue on `GitHub <https://github.com/mhabedank/mobility-datasets/issues>`_
