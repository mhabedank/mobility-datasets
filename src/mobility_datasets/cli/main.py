"""Command-line interface for mobility-datasets.

Provides commands to download and manage autonomous driving datasets.
"""

from pathlib import Path
from typing import Optional

import click

from mobility_datasets.config.provider import ConfigProvider
from mobility_datasets.core.downloader import DatasetDownloader


def get_available_datasets() -> list[str]:
    """Get list of available datasets from config files.

    Returns
    -------
    list[str]
        Names of available datasets (e.g., ['kitti', 'nuscenes', 'waymo']).
    """
    provider = ConfigProvider()
    return provider.list_datasources()


@click.group()
def cli():
    """Mobility Datasets - Download and manage autonomous driving datasets."""
    pass


@cli.group()
def dataset():
    """Dataset management commands."""
    pass


@dataset.command()
@click.argument(
    "dataset_name",
    type=click.Choice(get_available_datasets(), case_sensitive=False),
)
@click.option(
    "--collection",
    "-c",
    default=None,
    help="Collection to download (e.g., raw_data, v1.0-trainval). "
    "If not specified, downloads all collections.",
)
@click.option(
    "--sessions",
    "-s",
    default=None,
    help="Comma-separated session IDs. If not specified, downloads all sessions.",
)
@click.option(
    "--with-optional",
    is_flag=True,
    help="Include optional dataset parts.",
)
@click.option(
    "--keep-zip",
    is_flag=True,
    help="Keep archive files after extraction (useful for backup).",
)
@click.option("--estimate-only", is_flag=True, help="Estimate size without downloading")
@click.option(
    "--data-dir",
    default="./data",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Base directory for downloads. Subdirectory per dataset will be created. "
    "Default: ./data",
)
def download(
    dataset_name: str,
    collection: Optional[str],
    sessions: Optional[str],
    with_optional: bool,
    keep_zip: bool,
    estimate_only: bool,
    data_dir: Path,
):
    """Download dataset files.

    Download specific sessions from a dataset, or all sessions if not specified.
    Supports resume on interrupted downloads and validates files with MD5 checksums.

    \b
    Examples:

    # Download single session from KITTI raw_data
    mdb dataset download kitti --collection raw_data --sessions 2011_09_26_drive_0001

    # Download multiple sessions
    mdb dataset download kitti -c raw_data -s 2011_09_26_drive_0001,2011_09_26_drive_0002

    # Download all sessions from nuScenes trainval
    mdb dataset download nuscenes --collection v1.0-trainval

    # Download with optional parts
    mdb dataset download waymo --with-optional

    # Download to custom directory
    mdb dataset download kitti --data-dir /mnt/datasets
    """
    try:
        # Initialize downloader
        downloader = DatasetDownloader(dataset=dataset_name.lower(), data_dir=str(data_dir))

        # Get available collections from config
        available_collections = [c.id for c in downloader.config.collections]

        # If no collection specified, download all
        if collection is None:
            collections_to_download = available_collections
            click.echo(
                f"No collection specified. Downloading all: {', '.join(available_collections)}"
            )
        else:
            if collection not in available_collections:
                click.echo(
                    f"✗ Collection '{collection}' not found. Available: {', '.join(available_collections)}",
                    err=True,
                )
                raise click.Abort()
            collections_to_download = [collection]

        # Parse session list
        session_list = None
        if sessions:
            session_list = [s.strip() for s in sessions.split(",")]

        # ESTIMATE MODE
        if estimate_only:
            click.echo(f"\n{'='*60}")
            click.echo("Download Size Estimate")
            click.echo("=" * 60)

            for coll_id in collections_to_download:
                size_info = downloader.get_download_size(
                    collection_id=coll_id,
                    sessions=session_list or [],
                    with_optional=with_optional,
                )

                click.echo(f"\nCollection: {coll_id}")
                if session_list:
                    click.echo(f"Sessions: {', '.join(session_list)}")
                else:
                    click.echo(f"Sessions: all ({size_info['sessions_count']})")

                click.echo(f"\nTotal Download Size: {size_info['total_readable']}")

                click.echo("\nParts breakdown:")
                for part_id, size_bytes in size_info["parts"].items():
                    # Get readable format from humanize via the dict
                    import humanize

                    click.echo(f"  - {part_id}: {humanize.naturalsize(size_bytes)}")

            click.echo(f"\n{'='*60}")
            click.echo("✓ Ready to download?")
            click.echo("  Run without --estimate-only to start download")
            return

        # Download from each collection
        for coll_id in collections_to_download:
            click.echo(f"\n{'='*60}")
            click.echo(f"Downloading from collection: {coll_id}")
            if session_list:
                click.echo(f"Sessions: {', '.join(session_list)}")
            else:
                click.echo("Sessions: all")

            downloader.download(
                collection_id=coll_id,
                sessions=session_list or [],
                keep_zip=keep_zip,
                with_optional=with_optional,
            )

        click.echo(f"\n{'='*60}")
        click.echo("✓ Download complete!")
        click.echo(f"Files saved to: {downloader.data_dir}")

    except FileNotFoundError as e:
        click.echo(f"✗ Dataset configuration not found: {e}", err=True)
        raise click.Abort() from None
    except ValueError as e:
        click.echo(f"✗ Invalid configuration: {e}", err=True)
        raise click.Abort() from None
    except Exception as e:
        click.echo(f"✗ Download failed: {e}", err=True)
        raise click.Abort() from None


@dataset.command()
@click.argument(
    "dataset_name",
    type=click.Choice(get_available_datasets(), case_sensitive=False),
)
@click.option(
    "--timeout",
    default=10,
    type=int,
    help="Timeout for HEAD requests in seconds. Default: 10",
)
def health_check(dataset_name: str, timeout: int):
    """Check if all dataset files are available on remote servers.

    Performs HEAD requests to verify file availability without downloading.
    Useful for checking before starting large downloads.

    \b
    Examples:

    # Check KITTI availability
    mdb dataset health-check kitti

    # Check nuScenes with custom timeout
    mdb dataset health-check nuscenes --timeout 30
    """
    try:
        downloader = DatasetDownloader(dataset=dataset_name.lower())

        click.echo(f"Checking {dataset_name} dataset availability...")
        click.echo("(This may take a few minutes)\n")

        status = downloader.health_check()

        # Summary
        available = sum(status.values())
        total = len(status)
        unavailable_count = total - available

        click.echo(f"\n{'='*60}")
        click.echo(f"Summary: {available}/{total} files available")

        if unavailable_count > 0:
            click.echo(f"⚠ {unavailable_count} files are NOT available")
            unavailable_ids = [k for k, v in status.items() if not v]
            for file_id in unavailable_ids[:5]:  # Show first 5
                click.echo(f"  - {file_id}")
            if len(unavailable_ids) > 5:
                click.echo(f"  ... and {len(unavailable_ids) - 5} more")
        else:
            click.echo("✓ All files available!")

    except FileNotFoundError as e:
        click.echo(f"✗ Dataset configuration not found: {e}", err=True)
        raise click.Abort() from None
    except Exception as e:
        click.echo(f"✗ Health check failed: {e}", err=True)
        raise click.Abort() from None


@dataset.command()
def list_datasets():
    """List all available datasets.

    Shows dataset names and their configurations.

    \b
    Examples:

    mdb dataset list-datasets
    """
    try:
        provider = ConfigProvider()
        datasets = provider.list_datasources()

        if not datasets:
            click.echo("No datasets configured.")
            return

        click.echo("Available datasets:\n")
        for ds_name in datasets:
            config = provider.get_from_datasource(ds_name)
            click.echo(f"  {ds_name.upper()}")
            click.echo(f"    Name: {config.metadata.name}")
            click.echo(f"    Description: {config.metadata.description}")
            click.echo(f"    License: {config.metadata.license.name}")
            click.echo(f"    Collections: {len(config.collections)}")
            click.echo()

    except Exception as e:
        click.echo(f"✗ Failed to list datasets: {e}", err=True)
        raise click.Abort() from None


if __name__ == "__main__":
    cli()
