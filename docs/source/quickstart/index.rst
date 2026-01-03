================================================================================
Quick Start
================================================================================

Get up and running with mobility-datasets in 5 minutes.

.. contents::
   :local:
   :depth: 2

---

Installation
============

Install via pip:

.. code-block:: bash

    pip install mobility-datasets

This installs both the Python library and the ``mds`` CLI tool.

---

Your First Download
===================

Let's download a single small session from KITTI to get started:

.. code-block:: bash

    mds download kitti --collection city --sessions 2011_09_26_drive_0001

This downloads one session (~700 MB) from the city collection. You'll see progress output showing the download status.

Your data will be saved to ``./data/kitti/``.

---

See What's Available First
===========================

Before downloading, explore what KITTI offers:

.. code-block:: bash

    # Show all KITTI collections and sessions
    mds info kitti

    # Show only city collection
    mds info kitti --collection city

    # Verify files are actually available (checks remote servers)
    mds info kitti --verify

This is useful to:

- Understand available data before downloading
- See collection names and session IDs
- Check how much data each session is
- Verify S3 files are accessible in your region

---

Download Full Collections
==========================

Ready to download more? Download entire collections:

.. code-block:: bash

    # Download all city collection sessions
    mds download kitti --collection city

    # Download multiple collections
    mds download kitti --collection city --collection road

---

Download Multiple Sessions
===========================

Pick specific sessions without downloading the whole collection:

.. code-block:: bash

    # Download multiple sessions from city collection
    mds download kitti --collection city --sessions 2011_09_26_drive_0001,2011_09_26_drive_0002

    # Download all sessions (omit --sessions)
    mds download kitti --collection city

---

Preview Download Size
======================

Check how much data you're about to download:

.. code-block:: bash

    # Estimate download size without downloading
    mds download kitti --collection city --estimate-only

Output shows breakdown by session and data type (synced, calibration, etc).

This lets you understand the actual download size before committing your disk space.

---

Custom Download Location
=========================

By default, data is saved to ``./data``. Use a custom directory:

.. code-block:: bash

    # Download to external drive
    mds download kitti --collection city --data-dir /mnt/external/datasets

    # Each dataset gets its own subfolder
    ls /mnt/external/datasets/
    # kitti/

---

Keep Downloaded Archives
=========================

By default, ZIP archives are deleted after extraction. Keep them for backup:

.. code-block:: bash

    mds download kitti --collection city --keep-zip

This is useful if:
- You want to back up the original archives
- You're on unstable internet (resume downloads from archives)
- You plan to re-extract the data later

---

Load Data in Python
====================

Once downloaded, use the Python API to explore the data:

.. code-block:: python

    from mobility_datasets.core.downloader import DatasetDownloader

    # Initialize downloader (points to downloaded data)
    downloader = DatasetDownloader(dataset="kitti", data_dir="./data")

    # Access dataset information
    print(downloader.config.metadata.name)
    # Output: The KITTI Vision Benchmark Suite

    # List available collections
    for collection in downloader.config.collections:
        print(f"Collection: {collection.id}")
        print(f"  Sessions: {len(collection.sessions)}")

    # Access a specific session
    city_collection = downloader.config.get_collection_by_id("city")
    first_session = city_collection.sessions[0]
    print(f"Session: {first_session.id}")
    print(f"  Parts: {[p.id for p in first_session.parts]}")

You can now use the data for sensor fusion, localization, or perception algorithms.

---

Common Issues
=============

**"Collection not found"**

Use ``mds info kitti`` to see available collections and session IDs before downloading.

**"Dataset configuration not found"**

Check you're using a supported dataset name: ``kitti``, ``nuscenes`` (coming soon), ``waymo`` (coming soon).

**"Storage full during download"**

Use ``--estimate-only`` to check size first. Download specific sessions instead of entire collections.

---

Next Steps
==========

- :doc:`../guides/kitti_dataset` - Learn about KITTI data structure and formats
- :doc:`../cli/index` - Full CLI reference and all options
- :doc:`../api/index` - Complete Python API documentation
