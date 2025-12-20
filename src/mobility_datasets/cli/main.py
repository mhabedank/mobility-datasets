# src/mobility_datasets/cli/main.py
"""Command-line interface for mobility-datasets."""

import click


@click.group()
def cli():
    """
    Mobility Datasets CLI - Download and manage autonomous driving datasets.

    This CLI provides commands to download, manage, and inspect mobility datasets
    like KITTI, nuScenes, and Waymo. Use the subcommands to interact with specific
    datasets.

    Examples
    --------
    Download all KITTI components:

    .. code-block:: bash

        mdb dataset download kitti --all

    Download specific components:

    .. code-block:: bash

        mdb dataset download kitti --components oxts,calib
    """
    pass


@cli.group()
def dataset():
    """
    Dataset management commands.

    Commands for downloading, listing, and managing datasets. Each dataset
    has its own set of downloadable components (e.g., GPS data, calibration files).
    """
    pass


@dataset.command()
@click.argument("name", type=click.Choice(["kitti"]))
@click.option(
    "--components",
    "-c",
    help="Components to download (comma-separated). Available: oxts, calib, poses, sequences",
)
@click.option(
    "--all", "download_all", is_flag=True, help="Download all available components for the dataset"
)
@click.option(
    "--data-dir", default="./data", help="Target directory for downloads (default: ./data)"
)
@click.option(
    "--keep-zip", is_flag=True, help="Keep compressed archives after extraction (useful for backup)"
)
def download(name, components, download_all, data_dir, keep_zip):
    """
    Download dataset files from cloud storage.

    This command downloads the specified components of a dataset from AWS S3
    or other cloud providers. Files are automatically extracted unless --keep-zip
    is specified.

    Parameters
    ----------
    name : str
        Dataset name. Currently supported: 'kitti'
    components : str, optional
        Comma-separated list of components to download
    download_all : bool
        If True, downloads all available components
    data_dir : str
        Root directory for dataset storage
    keep_zip : bool
        If True, preserves compressed archives after extraction

    Raises
    ------
    click.Abort
        If neither --components nor --all is specified

    Examples
    --------
    Download all KITTI data:

    .. code-block:: bash

        mdb dataset download kitti --all

    Download only GPS/IMU data and calibration:

    .. code-block:: bash

        mdb dataset download kitti --components oxts,calib

    Download to custom directory and keep archives:

    .. code-block:: bash

        mdb dataset download kitti --all --data-dir /mnt/datasets --keep-zip

    Notes
    -----
    - KITTI dataset is approximately 165 GB when fully downloaded
    - Download speed depends on your internet connection
    - Extraction requires additional temporary disk space

    See Also
    --------
    mdb dataset list : Show available datasets and components
    """
    if name == "kitti":
        from mobility_datasets.kitti.loader import KITTIDownloader

        downloader = KITTIDownloader(data_dir=f"{data_dir}/{name}")

        if download_all:
            click.echo("Downloading all KITTI components...")
            downloader.download_all(keep_zip=keep_zip)
        elif components:
            component_list = [c.strip() for c in components.split(",")]
            click.echo(f"Downloading components: {', '.join(component_list)}")
            downloader.download(component_list, keep_zip=keep_zip)
        else:
            click.echo("Error: Specify --components or --all")
            raise click.Abort()

        click.echo("✓ Download complete!")


if __name__ == "__main__":
    cli()
