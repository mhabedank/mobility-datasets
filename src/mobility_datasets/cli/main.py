"""Main CLI entry point for mobility datasets."""

from pathlib import Path
from typing import Optional

import click

from mobility_datasets import __version__
from mobility_datasets.common.base import DatasetConfig
from mobility_datasets.kitti.dataset import KITTIDataset
from mobility_datasets.nuscenes.dataset import NuScenesDataset
from mobility_datasets.waymo.dataset import WaymoDataset

DATASET_CLASSES = {
    "kitti": KITTIDataset,
    "nuscenes": NuScenesDataset,
    "waymo": WaymoDataset,
}


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Mobility Datasets CLI - Tools for working with autonomous driving datasets."""
    pass


@cli.group()
def dataset() -> None:
    """Commands for managing datasets."""
    pass


@dataset.command()
@click.argument("dataset_name", type=click.Choice(["kitti", "nuscenes", "waymo"]))
@click.option(
    "--root-dir",
    type=click.Path(path_type=Path),
    required=True,
    help="Root directory of the dataset",
)
@click.option(
    "--split",
    type=str,
    default="train",
    help="Dataset split (e.g., train, val, test)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Output directory for downloaded files (defaults to root-dir)",
)
def download(dataset_name: str, root_dir: Path, split: str, output_dir: Optional[Path]) -> None:
    """Download a dataset.

    DATASET_NAME: Name of the dataset (kitti, nuscenes, or waymo)
    """
    click.echo(f"Downloading {dataset_name} dataset...")
    click.echo(f"Root directory: {root_dir}")
    click.echo(f"Split: {split}")

    # Create dataset instance
    dataset_class = DATASET_CLASSES[dataset_name]
    config = DatasetConfig(root_dir=root_dir, split=split)
    dataset_instance = dataset_class(config)

    # Download
    try:
        dataset_instance.download(output_dir=output_dir)
        click.echo(f"✓ Download instructions provided for {dataset_name}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort() from e


@dataset.command()
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list(format: str) -> None:
    """List available datasets and their information."""
    import json

    datasets = []
    for name, dataset_class in DATASET_CLASSES.items():
        info = dataset_class.DATASET_INFO
        datasets.append(
            {
                "name": name,
                "description": info["description"],
                "url": info["url"],
                "splits": ", ".join(info["splits"]),
                "modalities": ", ".join(info["modalities"]),
            }
        )

    if format == "json":
        click.echo(json.dumps(datasets, indent=2))
    else:
        # Table format
        click.echo("\nAvailable Datasets:\n")
        click.echo("=" * 80)
        for ds in datasets:
            click.echo(f"\nDataset: {ds['name']}")
            click.echo(f"Description: {ds['description']}")
            click.echo(f"URL: {ds['url']}")
            click.echo(f"Splits: {ds['splits']}")
            click.echo(f"Modalities: {ds['modalities']}")
            click.echo("-" * 80)


@dataset.command()
@click.argument("dataset_name", type=click.Choice(["kitti", "nuscenes", "waymo"]))
@click.option(
    "--root-dir",
    type=click.Path(path_type=Path),
    required=True,
    help="Root directory of the dataset",
)
@click.option(
    "--split",
    type=str,
    default="train",
    help="Dataset split (e.g., train, val, test)",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def info(dataset_name: str, root_dir: Path, split: str, format: str) -> None:
    """Get information about a dataset.

    DATASET_NAME: Name of the dataset (kitti, nuscenes, or waymo)
    """
    import json

    click.echo(f"Loading {dataset_name} dataset information...")

    # Create dataset instance
    dataset_class = DATASET_CLASSES[dataset_name]
    config = DatasetConfig(root_dir=root_dir, split=split)

    try:
        dataset_instance = dataset_class(config)
        info_dict = dataset_instance.get_info()

        if format == "json":
            click.echo(json.dumps(info_dict, indent=2))
        else:
            # Text format
            click.echo("\nDataset Information:\n")
            click.echo("=" * 60)
            for key, value in info_dict.items():
                click.echo(f"{key}: {value}")
            click.echo("=" * 60)

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    cli()
