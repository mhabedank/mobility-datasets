Quickstart
==========

This guide will help you get started with mobility-datasets.

Basic Usage
-----------

Loading a Dataset
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pathlib import Path
    from mobility_datasets import DatasetConfig
    from mobility_datasets.kitti import KITTIDataset

    # Configure dataset
    config = DatasetConfig(
        root_dir=Path("/path/to/kitti"),
        split="training"
    )

    # Load dataset
    dataset = KITTIDataset(config)

    # Get number of samples
    print(f"Dataset has {len(dataset)} samples")

Accessing Samples
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Access by index
    sample = dataset[0]
    print(f"Sample ID: {sample.sample_id}")
    print(f"Timestamp: {sample.timestamp}")

    # Access by sample ID
    sample = dataset["000001"]

    # Iterate over samples
    for sample in dataset:
        print(sample.sample_id)

Converting to DataFrame
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Convert to pandas DataFrame
    df = dataset.to_dataframe()
    print(df.head())

    # Filter and analyze
    print(df.describe())

Using Coordinate Transformations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import numpy as np
    from mobility_datasets import Transform, CoordinateSystem

    # Create a transform
    transform = Transform(
        translation=np.array([1.0, 0.0, 0.0]),
        from_coord=CoordinateSystem.LIDAR,
        to_coord=CoordinateSystem.CAMERA
    )

    # Transform points
    points = np.array([[0, 0, 0], [1, 0, 0]])
    transformed = transform.transform_points(points)

    # Compose transforms
    transform2 = Transform(translation=np.array([0.0, 1.0, 0.0]))
    composed = transform.compose(transform2)

CLI Usage
---------

List Available Datasets
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    mds dataset list

Get Dataset Information
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    mds dataset info kitti --root-dir /path/to/kitti --split training

Download Dataset
~~~~~~~~~~~~~~~~

.. code-block:: bash

    mds dataset download kitti --root-dir /path/to/kitti --split training

Working with Different Datasets
--------------------------------

KITTI
~~~~~

.. code-block:: python

    from mobility_datasets.kitti import KITTIDataset
    from mobility_datasets import DatasetConfig

    config = DatasetConfig(root_dir="/path/to/kitti", split="training")
    dataset = KITTIDataset(config)

nuScenes
~~~~~~~~

.. code-block:: python

    from mobility_datasets.nuscenes import NuScenesDataset
    from mobility_datasets import DatasetConfig

    config = DatasetConfig(root_dir="/path/to/nuscenes", split="train")
    dataset = NuScenesDataset(config)

Waymo
~~~~~

.. code-block:: python

    from mobility_datasets.waymo import WaymoDataset
    from mobility_datasets import DatasetConfig

    config = DatasetConfig(root_dir="/path/to/waymo", split="training")
    dataset = WaymoDataset(config)
