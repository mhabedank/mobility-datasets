# mobility-datasets

[![CI](https://github.com/mhabedank/mobility-datasets/workflows/CI/badge.svg)](https://github.com/mhabedank/mobility-datasets/actions)
[![Documentation](https://github.com/mhabedank/mobility-datasets/workflows/Documentation/badge.svg)](https://github.com/mhabedank/mobility-datasets/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python package for autonomous driving datasets with support for KITTI, nuScenes, and Waymo Open Dataset.

## Features

- **Modern src layout**: Clean package structure with `src/mobility_datasets/`
- **Unified API**: Consistent interface across different datasets
- **Dual data access**: Both pandas DataFrames and typed dataclasses
- **Lazy loading**: Efficient memory usage with on-demand data loading
- **Coordinate systems**: Built-in transformation utilities
- **Abstract base classes**: Easy to extend with new datasets
- **CLI tool**: Command-line interface for dataset management
- **Type hints**: Full type annotations throughout
- **Well-tested**: Comprehensive test suite with pytest
- **Documentation**: Sphinx-generated RST documentation

## Installation

### From PyPI (when published)

```bash
pip install mobility-datasets
```

### From Source

```bash
git clone https://github.com/mhabedank/mobility-datasets.git
cd mobility-datasets
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev,docs]"
pre-commit install
```

## Quick Start

### Python API

```python
from pathlib import Path
from mobility_datasets import DatasetConfig
from mobility_datasets.kitti import KITTIDataset

# Configure and load dataset
config = DatasetConfig(root_dir=Path("/path/to/kitti"), split="training")
dataset = KITTIDataset(config)

# Access samples
print(f"Dataset has {len(dataset)} samples")
sample = dataset[0]
print(f"Sample ID: {sample.sample_id}")

# Convert to pandas DataFrame
df = dataset.to_dataframe()
print(df.head())

# Use coordinate transformations
from mobility_datasets import Transform
import numpy as np

transform = Transform(translation=np.array([1.0, 0.0, 0.0]))
points = np.array([[0, 0, 0], [1, 0, 0]])
transformed = transform.transform_points(points)
```

### Command-Line Interface

```bash
# List available datasets
mds dataset list

# Get dataset information
mds dataset info kitti --root-dir /path/to/kitti --split training

# Download dataset (shows download instructions)
mds dataset download kitti --root-dir /path/to/kitti --split training
```

## Supported Datasets

### KITTI Vision Benchmark Suite
- Website: http://www.cvlibs.net/datasets/kitti/
- Splits: training, testing
- Modalities: Camera, LiDAR, GPS

### nuScenes
- Website: https://www.nuscenes.org/
- Splits: train, val, test, mini
- Modalities: Camera (6x), LiDAR, Radar, CAN bus

### Waymo Open Dataset
- Website: https://waymo.com/open/
- Splits: training, validation, testing
- Modalities: Camera (5x), LiDAR (5x)

## Project Structure

```
mobility-datasets/
├── src/
│   └── mobility_datasets/
│       ├── __init__.py
│       ├── common/          # Base classes and utilities
│       │   ├── base.py
│       │   └── coordinates.py
│       ├── kitti/           # KITTI dataset implementation
│       ├── nuscenes/        # nuScenes dataset implementation
│       ├── waymo/           # Waymo dataset implementation
│       └── cli/             # Command-line interface
├── tests/                   # Test suite
├── docs/                    # Sphinx documentation
├── pyproject.toml          # Package configuration
└── .pre-commit-config.yaml # Pre-commit hooks
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting and Linting

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src/mobility_datasets
```

### Building Documentation

```bash
cd docs
sphinx-build -b html . _build/html
```

## Requirements

- Python 3.8+
- numpy >= 1.20.0
- scipy >= 1.7.0
- pandas >= 1.3.0
- click >= 8.0.0
- requests >= 2.26.0
- tqdm >= 4.62.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this package in your research, please cite:

```bibtex
@software{mobility_datasets,
  title = {mobility-datasets: A Python package for autonomous driving datasets},
  author = {Mobility Datasets Contributors},
  year = {2024},
  url = {https://github.com/mhabedank/mobility-datasets}
}
```
