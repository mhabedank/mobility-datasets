# mobility-datasets

[![codecov](https://codecov.io/gh/mhabedank/mobility-datasets/branch/main/graph/badge.svg)](https://codecov.io/gh/mhabedank/mobility-datasets)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python library for downloading and managing autonomous driving datasets like KITTI, nuScenes, and Waymo.

---

## Features

- **Easy Downloads**: Simple CLI and Python API for dataset downloads
- **Multiple Datasets**: Support for KITTI (more coming soon)
- **Flexible Storage**: Download to any directory
- **Resume Support**: Interrupted downloads can be resumed
- **Minimal Dependencies**: Lightweight with NumPy and Click

---

## Installation
```bash
pip install mobility-datasets
```

---

## Quick Start

### Download via CLI
```bash
# Download KITTI GPS/IMU data and ground truth
mdb dataset download kitti --components oxts,poses

# Download complete KITTI dataset (~165 GB)
mdb dataset download kitti --all

# Download to custom directory
mdb dataset download kitti --components oxts --data-dir /mnt/datasets
```

### Download via Python
```python
from mobility_datasets.kitti.loader import KITTIDownloader

# Initialize downloader
downloader = KITTIDownloader(data_dir="./data/kitti")

# Download specific components
downloader.download(["oxts", "poses"], keep_zip=False)

# Or download everything
downloader.download_all(keep_zip=False)
```

---

## Supported Datasets

| Dataset | Status | Components |
|---------|--------|------------|
| **KITTI** | ✅ Available | oxts, poses, calib, sequences |
| **nuScenes** | 🚧 Planned | - |
| **Waymo** | 🚧 Planned | - |

---

## KITTI Dataset Components

| Component | Description | Size | Frequency |
|-----------|-------------|------|-----------|
| `oxts` | GPS/IMU sensor data | ~850 MB | 10-100 Hz |
| `poses` | Ground truth trajectories | ~5 MB | ~10 Hz |
| `calib` | Calibration files | ~10 MB | Static |
| `sequences` | Camera images, timestamps | ~100 GB | ~10 Hz |

**Total KITTI size**: ~165 GB (all components)

---

## Documentation

Full documentation available at: [Read the Docs](#) *(coming soon)*

- **Quick Start**: Get running in 5 minutes
- **CLI Reference**: Complete command-line guide
- **API Reference**: Python API documentation
- **KITTI Guide**: Dataset structure and usage

---

## Requirements

- Python 3.11+
- NumPy
- Click
- Requests

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Follow the [Documentation Standards](docs/DOCUMENTATION_STANDARDS.md)
4. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Citation

If you use this library in your research, please cite the original datasets:

**KITTI Dataset:**
```bibtex
@INPROCEEDINGS{Geiger2012CVPR,
  author = {Andreas Geiger and Philip Lenz and Raquel Urtasun},
  title = {Are we ready for Autonomous Driving? The KITTI Vision Benchmark Suite},
  booktitle = {Conference on Computer Vision and Pattern Recognition (CVPR)},
  year = {2012}
}
```

---

## Acknowledgments

- [KITTI Vision Benchmark Suite](http://www.cvlibs.net/datasets/kitti/)
- All dataset providers for making their data publicly available
