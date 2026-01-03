================================================================================
Command-Line Interface
================================================================================

The ``mds`` command provides a convenient interface for downloading and managing
autonomous driving datasets from your terminal.

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

    mds --help

---

Core Commands
=============

The CLI has three main commands:

**mds download** — Download dataset files
    Download specific sessions, collections, or entire datasets.

**mds info** — Show dataset information
    Display available collections, sessions, and file sizes. Optionally verify
    that files are accessible on remote servers.

---

Download Command
================

Download dataset files from a collection.

Basic Usage
-----------

.. code-block:: bash

    mds download <dataset> [OPTIONS]

Download entire dataset (all collections):

.. code-block:: bash

    mds download kitti

Download specific collection:

.. code-block:: bash

    mds download kitti --collection city

Download specific sessions:

.. code-block:: bash

    mds download kitti --collection city --sessions 2011_09_26_drive_0001

Download multiple sessions:

.. code-block:: bash

    mds download kitti -c city -s 2011_09_26_drive_0001,2011_09_26_drive_0002

---

Download Options
----------------

**--collection, -c** <collection>
    Download from specific collection. If not specified, downloads all collections.

    .. code-block:: bash

        mds download kitti --collection city

**--sessions, -s** <sessions>
    Comma-separated session IDs to download. If not specified, downloads all sessions
    in the collection.

    .. code-block:: bash

        mds download kitti -c city -s 2011_09_26_drive_0001,2011_09_26_drive_0002

**--data-dir** <path>
    Base directory for downloads. Each dataset creates a subdirectory.
    Default: ``./data``

    .. code-block:: bash

        mds download kitti --data-dir /mnt/external/datasets

**--keep-zip**
    Keep archive files after extraction. By default, archives are deleted to save
    disk space.

    .. code-block:: bash

        mds download kitti --keep-zip

**--with-optional**
    Include optional dataset parts (marked as optional in configuration).
    Default: skip optional parts.

    .. code-block:: bash

        mds download kitti --with-optional

**--estimate-only**
    Preview download size without downloading. Useful for checking disk space
    requirements before committing to download.

    .. code-block:: bash

        mds download kitti --collection city --estimate-only

    Output shows:

    .. code-block:: text

        ============================================================
        Download Size Estimate
        ============================================================

        Collection: city
        Sessions: all (61)

        Total Download Size: 180 GB

        Parts breakdown:
          - synced_rectified: 150 GB
          - unsynced_unrectified: 20 GB
          - calib: 5 MB
          - tracklets: 2 GB

---

Info Command
============

Show information about available datasets, collections, and sessions.

Basic Usage
-----------

.. code-block:: bash

    mds info <dataset> [OPTIONS]

Show all collections:

.. code-block:: bash

    mds info kitti

Show specific collection:

.. code-block:: bash

    mds info kitti --collection city

Verify files are available on servers:

.. code-block:: bash

    mds info kitti --verify

---

Info Options
------------

**--collection, -c** <collection>
    Show information about specific collection only. If not specified, shows all
    collections.

    .. code-block:: bash

        mds info kitti --collection city

**--verify**
    Verify that all files are available on remote servers. This performs HTTP
    HEAD requests to check file accessibility without downloading.

    Useful before starting large downloads to catch missing files early.

    .. code-block:: bash

        mds info kitti --verify

**--timeout** <seconds>
    Timeout for verification requests in seconds. Default: 10

    .. code-block:: bash

        mds info kitti --verify --timeout 30

---

Info Output
-----------

Shows dataset metadata and collection/session information:

.. code-block:: text

    ============================================================
    Dataset: KITTI
    ============================================================

    Name: The KITTI Vision Benchmark Suite
    Description: A project of Karlsruhe Institute of Technology...
    License: CC BY-NC-SA 3.0

    ────────────────────────────────────────────────────────────
    Collections:
    ────────────────────────────────────────────────────────────

      city
        Sessions: 61
        Total size: 180 GB
          - 2011_09_26_drive_0001
          - 2011_09_26_drive_0002
          - 2011_09_26_drive_0005
          ... and 58 more

      residential
        Sessions: 44
        Total size: 120 GB

When using ``--verify``, also shows:

.. code-block:: text

    ────────────────────────────────────────────────────────────
    Checking file availability...
    ────────────────────────────────────────────────────────────

    ✓ All 15340 files available!

---

Common Examples
===============

Preview Before Download
-----------------------

Always check size before downloading:

.. code-block:: bash

    # See what's available
    mds info kitti

    # Check specific collection size
    mds info kitti --collection city

    # Estimate download size
    mds download kitti --collection city --estimate-only

    # Verify files are accessible
    mds info kitti --verify

---

Download Single Session
-----------------------

Download just one small session to get started:

.. code-block:: bash

    mds download kitti --collection city --sessions 2011_09_26_drive_0001

---

Download Multiple Sessions
---------------------------

Download several sessions at once:

.. code-block:: bash

    mds download kitti \
      --collection city \
      --sessions 2011_09_26_drive_0001,2011_09_26_drive_0002,2011_09_26_drive_0005

---

Download to External Drive
---------------------------

Download to an external drive or network mount:

.. code-block:: bash

    mds download kitti --data-dir /mnt/external/datasets

Data will be saved to: ``/mnt/external/datasets/kitti/``

---

Resume Interrupted Downloads
-----------------------------

Downloads automatically resume if interrupted:

.. code-block:: bash

    # First attempt (interrupted)
    mds download kitti --collection city

    # Resume later (automatically continues from where it stopped)
    mds download kitti --collection city

Files are validated with MD5 checksums. Already-valid files are skipped
automatically.

---

Troubleshooting
===============

"Collection not found"
----------------------

Use ``mds info kitti`` to see available collection names.

.. code-block:: bash

    mds info kitti

---

"Download failed" / Network errors
-----------------------------------

The CLI automatically retries failed downloads up to 3 times. For persistent
issues:

1. Check your internet connection
2. Verify files are available: ``mds info kitti --verify``
3. Try resuming the download (already-downloaded files are skipped)

---

"Storage full during download"
-------------------------------

Use ``--estimate-only`` to check total size before starting:

.. code-block:: bash

    mds download kitti --collection city --estimate-only

Consider downloading specific sessions instead of entire collections:

.. code-block:: bash

    # Download just one session (~700 MB)
    mds download kitti -c city -s 2011_09_26_drive_0001

    # Instead of all sessions (~180 GB)
    mds download kitti --collection city

---

Available Datasets
==================

KITTI
-----

The KITTI Vision Benchmark Suite — autonomous driving benchmark with raw sensor
data and ground truth.

Collections:

- **city** — Urban driving sequences
- **residential** — Residential area sequences
- **road** — Road sequences

.. code-block:: bash

    mds info kitti
    mds download kitti --collection city

nuScenes (Coming Soon)
----------------------

Large-scale 3D autonomous driving dataset.

Waymo Open Dataset (Coming Soon)
--------------------------------

Large-scale autonomous driving dataset from Waymo.

---

See Also
========

- :doc:`../quickstart/index` - Getting started guide with examples
- :doc:`../guides/kitti_dataset` - KITTI dataset structure and usage
- :doc:`../api/index` - Python API for programmatic access
