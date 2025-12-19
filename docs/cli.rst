Command Line Interface
======================

The ``mds`` command provides tools for managing and working with datasets.

Commands
--------

dataset list
~~~~~~~~~~~~

List all available datasets with their information.

.. code-block:: bash

    mds dataset list [--format FORMAT]

Options:

* ``--format``: Output format (table or json). Default: table

Examples:

.. code-block:: bash

    # List datasets in table format
    mds dataset list

    # List datasets in JSON format
    mds dataset list --format json

dataset info
~~~~~~~~~~~~

Get detailed information about a specific dataset.

.. code-block:: bash

    mds dataset info DATASET_NAME --root-dir PATH [OPTIONS]

Arguments:

* ``DATASET_NAME``: Name of the dataset (kitti, nuscenes, or waymo)

Options:

* ``--root-dir PATH``: Root directory of the dataset (required)
* ``--split TEXT``: Dataset split. Default: train
* ``--format``: Output format (text or json). Default: text

Examples:

.. code-block:: bash

    # Get KITTI dataset info
    mds dataset info kitti --root-dir /data/kitti --split training

    # Get info in JSON format
    mds dataset info nuscenes --root-dir /data/nuscenes --format json

dataset download
~~~~~~~~~~~~~~~~

Download a dataset (provides download instructions).

.. code-block:: bash

    mds dataset download DATASET_NAME --root-dir PATH [OPTIONS]

Arguments:

* ``DATASET_NAME``: Name of the dataset (kitti, nuscenes, or waymo)

Options:

* ``--root-dir PATH``: Root directory of the dataset (required)
* ``--split TEXT``: Dataset split. Default: train
* ``--output-dir PATH``: Output directory for downloads

Examples:

.. code-block:: bash

    # Download KITTI dataset
    mds dataset download kitti --root-dir /data/kitti --split training

    # Download to specific output directory
    mds dataset download waymo --root-dir /data/waymo --output-dir /tmp/downloads
