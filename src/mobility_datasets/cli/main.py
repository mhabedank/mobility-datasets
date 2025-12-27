# src/mobility_datasets/cli/main.py
"""Command-line interface for mobility-datasets."""

from pathlib import Path

import click


@click.group()
def cli():
    pass


@cli.group()
def dataset():
    pass


@dataset.command()
@click.argument("dataset", type=click.Choice(["kitti"]))
@click.option(
    "--collection",
    "-c",
    default="raw_data",
    help="Collection to download (e.g., raw_data, synced_data). Default: raw_data",
)
@click.option(
    "--sessions",
    "-s",
    help="Comma-separated session IDs. If not specified, downloads all sessions.",
)
@click.option(
    "--with-unsynced",
    is_flag=True,
    help="Include unsynced_rectified variant (only with KITTI).",
)
@click.option(
    "--keep-zip",
    is_flag=True,
    help="Keep ZIP files after extraction (useful for backup).",
)
@click.option(
    "--data-dir",
    default="./data",
    help="Target directory for downloads. Default: ./data",
)
def download(dataset, collection, sessions, with_unsynced, keep_zip, data_dir):
    """Download dataset files.

    Examples:

    \b
    # Download single session from raw_data collection
    mdb dataset download kitti --collection raw_data --sessions 2011_09_26_drive_0001

    \b
    # Download all sessions from raw_data
    mdb dataset download kitti --collection raw_data

    \b
    # Download multiple specific sessions
    mdb dataset download kitti -c raw_data -s 2011_09_26_drive_0001,2011_09_26_drive_0002

    \b
    # Download synced_data collection
    mdb dataset download kitti --collection synced_data

    \b
    # Include unsynced variant
    mdb dataset download kitti --with-unsynced
    """
    if dataset == "kitti":
        from mobility_datasets.core.downloader import DatasetDownloader

        data_dir_path = Path(data_dir) / "kitti"
        downloader = DatasetDownloader(data_dir=str(data_dir_path))

        # Parse sessions
        session_list = None
        if sessions:
            session_list = [s.strip() for s in sessions.split(",")]

        click.echo(f"Downloading from collection: {collection}")
        if session_list:
            click.echo(f"Sessions: {', '.join(session_list)}")
        else:
            click.echo("Sessions: all")

        try:
            downloader.download(
                collection_id=collection,
                sessions=session_list,
                keep_zip=keep_zip,
                with_optional=with_unsynced,
            )
            click.echo("✓ Download complete!")
        except Exception as e:
            click.echo(f"✗ Download failed: {e}", err=True)
            raise click.Abort() from None


if __name__ == "__main__":
    cli()
