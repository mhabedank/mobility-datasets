================================================================================
User Guides
================================================================================

In-depth guides for working with mobility datasets.

These guides explain concepts, workflows, and best practices for using
autonomous driving datasets in your research or applications.

---

Available Guides
================

KITTI Dataset
-------------

.. toctree::
   :maxdepth: 1

   kitti_dataset

Learn how to work with the KITTI benchmark dataset, including:

- Dataset structure and organization
- GPS/IMU data format (OXTS)
- Ground truth pose format
- Sequence-to-raw-data mapping
- Coordinate systems

---

Coming Soon
===========

These guides are planned for future releases:

Coordinate Systems
------------------

**Status:** In development

Topics covered:

- ENU (East-North-Up) coordinate system
- CAMERA coordinate system (KITTI standard)
- VEHICLE coordinate system
- Transformations between frames
- ECEF and GPS conversions

Sensor Fusion Workflows
-----------------------

**Status:** Planned

Topics covered:

- GPS + IMU data fusion
- Kalman filter implementation
- Ground truth comparison
- Performance metrics (RMSE, ATE)
- Parameter tuning

Custom Dataset Integration
--------------------------

**Status:** Planned

Topics covered:

- Adding new datasets
- Implementing custom loaders
- Standard data formats
- Testing and validation

nuScenes Dataset
----------------

**Status:** Planned

Topics covered:

- nuScenes data structure
- Multi-sensor data (camera, LiDAR, radar)
- Annotations and metadata
- Comparison with KITTI

Waymo Open Dataset
------------------

**Status:** Planned

Topics covered:

- Waymo data format
- TFRecord handling
- Sensor calibration
- Evaluation metrics

---

Contributing Guides
===================

We welcome contributions! If you'd like to write a guide:

1. Follow the :doc:`../development/documentation_standards` (coming soon)
2. Use English throughout
3. Include runnable code examples
4. Add troubleshooting sections
5. Submit a pull request

---

See Also
========

- :doc:`../quickstart/index` - Get started quickly
- :doc:`../cli/index` - Command-line reference
- :doc:`../api/index` - Python API documentation
