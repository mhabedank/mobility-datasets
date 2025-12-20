================================================================================
Command-Line Interface
================================================================================

The ``mdb`` command provides a convenient interface for downloading and
managing mobility datasets.

.. contents::
   :local:
   :depth: 2

---

Installation
============

The CLI is installed automatically with the package:

.. code-block:: bash

    pip install mobility-datasets

Verify installation:

.. code-block:: bash

    mdb --help

---

Quick Reference
===============

Common Commands
---------------

.. code-block:: bash

    # Download complete KITTI dataset
    mdb dataset download kitti --all

    # Download specific components
    mdb dataset download kitti --components oxts,poses

    # Download to custom directory
    mdb dataset download kitti --all --data-dir /mnt/datasets

    # Keep compressed archives
    mdb dataset download kitti --components oxts --keep-zip

---

Full Command Reference
======================

.. click:: mobility_datasets.cli.main:cli
   :prog: mdb
   :nested: full

---

Dataset Components
==================

KITTI Components
----------------

.. list-table::
   :header-rows: 1
   :widths: 20 50 15 15

   * - Component
     - Description
     - Size
     - Frequency
   * - ``oxts``
     - GPS/IMU sensor data
     - ~850 MB
     - 10-100 Hz
   * - ``poses``
     - Ground truth trajectories
     - ~5 MB
     - ~10 Hz
   * - ``calib``
     - Calibration files
     - ~10 MB
     - Static
   * - ``sequences``
     - Camera images, timestamps
     - ~100 GB
     - ~10 Hz

---

See Also
========

- :doc:`../quickstart/index` - Getting started guide
- :doc:`../guides/kitti_dataset` - KITTI dataset overview
- :doc:`../api/index` - Python API for programmatic downloads
