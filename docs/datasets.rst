Datasets
========

This section provides information about the supported autonomous driving datasets.

KITTI
------

Overview
~~~~~~~~

The KITTI Vision Benchmark Suite is one of the most popular benchmarks for computer
vision research in autonomous driving. It contains hours of traffic scenarios recorded
with a variety of sensors including high-resolution color and grayscale cameras, a
Velodyne 3D laser scanner, and a GPS localization system.

Website
~~~~~~~

http://www.cvlibs.net/datasets/kitti/

Splits
~~~~~~

* **training**: Training data with annotations
* **testing**: Test data without public annotations

Modalities
~~~~~~~~~~

* Stereo color cameras (left and right)
* Grayscale cameras
* Velodyne HDL-64E LiDAR
* GPS/IMU data

Usage
~~~~~

.. code-block:: python

    from mobility_datasets.kitti import KITTIDataset
    from mobility_datasets import DatasetConfig

    config = DatasetConfig(root_dir="/path/to/kitti", split="training")
    dataset = KITTIDataset(config)

nuScenes
--------

Overview
~~~~~~~~

The nuScenes dataset is a large-scale autonomous driving dataset featuring data
collected in Boston and Singapore. It provides a full sensor suite including 6 cameras,
1 LiDAR, 5 radars, GPS, and IMU data. The dataset includes rich 3D annotations for
23 object classes.

Website
~~~~~~~

https://www.nuscenes.org/

Splits
~~~~~~

* **train**: Training data
* **val**: Validation data
* **test**: Test data
* **mini**: Mini version for quick testing (subset of train/val)

Modalities
~~~~~~~~~~

* 6 cameras (front, front-left, front-right, back, back-left, back-right)
* 1x Velodyne HDL-32E LiDAR
* 5x Continental radars
* GPS/IMU data
* CAN bus data

Usage
~~~~~

.. code-block:: python

    from mobility_datasets.nuscenes import NuScenesDataset
    from mobility_datasets import DatasetConfig

    config = DatasetConfig(root_dir="/path/to/nuscenes", split="train")
    dataset = NuScenesDataset(config)

Waymo Open Dataset
------------------

Overview
~~~~~~~~

The Waymo Open Dataset is one of the largest and most diverse autonomous driving
datasets available. It contains data collected by Waymo's autonomous vehicles in
various cities and weather conditions. The dataset includes high-resolution camera
images, LiDAR point clouds, and rich 3D annotations.

Website
~~~~~~~

https://waymo.com/open/

Splits
~~~~~~

* **training**: Training data
* **validation**: Validation data
* **testing**: Test data

Modalities
~~~~~~~~~~

* 5 cameras (front, front-left, front-right, side-left, side-right)
* 5 LiDAR sensors (1 mid-range, 4 short-range)

Usage
~~~~~

.. code-block:: python

    from mobility_datasets.waymo import WaymoDataset
    from mobility_datasets import DatasetConfig

    config = DatasetConfig(root_dir="/path/to/waymo", split="training")
    dataset = WaymoDataset(config)

Dataset Comparison
------------------

+-------------+---------------+------------------+--------------------+
| Dataset     | # Samples     | Recording Time   | Annotation Types   |
+=============+===============+==================+====================+
| KITTI       | ~15K frames   | ~2 hours         | 2D/3D boxes        |
+-------------+---------------+------------------+--------------------+
| nuScenes    | ~40K keyframes| ~5.5 hours       | 3D boxes, tracking |
+-------------+---------------+------------------+--------------------+
| Waymo       | ~200K segments| ~570 hours       | 2D/3D boxes        |
+-------------+---------------+------------------+--------------------+
