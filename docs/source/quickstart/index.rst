================================================================================
Quick Start
================================================================================

Get up and running with mobility-datasets in 5 minutes.

Installation
============

Install via pip:

.. code-block:: bash

    pip install mobility-datasets

This installs both the Python library and the ``mdb`` command-line tool.

---

Download Data (CLI)
===================

Download KITTI GPS/IMU data and ground truth poses:

.. code-block:: bash

    mdb dataset download kitti --components oxts,poses

Download all components (~165 GB):

.. code-block:: bash

    mdb dataset download kitti --all

Download to custom directory:

.. code-block:: bash

    mdb dataset download kitti --components oxts,poses --data-dir /mnt/datasets

---

Download Data (Python)
======================

.. code-block:: python

    from mobility_datasets.kitti.loader import KITTIDownloader

    # Initialize downloader
    downloader = KITTIDownloader(data_dir="./data/kitti")

    # Download specific components
    downloader.download(["oxts", "poses"], keep_zip=False)

    # Or download everything
    downloader.download_all(keep_zip=False)

---

Next Steps
==========

- :doc:`../guides/kitti_dataset` - Learn about KITTI data structure
- :doc:`../cli/index` - Full CLI reference
- :doc:`../api/index` - Complete API documentation
