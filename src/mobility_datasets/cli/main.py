"""Command-line interface for mobility-datasets.

Provides commands to download and manage autonomous driving datasets.

Command Structure:
  mds download <dataset>          # Download data
  mds info <dataset>              # Show available data (collections, sizes, status)
  mds list [<dataset>]            # List local downloads (future feature)
"""

from pathlib import Path
from typing import Optional

import click
import humanize

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


# =============================================================================
# DOWNLOAD COMMANDS
# =============================================================================


@cli.command()
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
@click.option(
    "--estimate-only",
    is_flag=True,
    help="Show download size without downloading.",
)
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
    """Download dataset files from a specific dataset.

    Download specific sessions, collections, or the entire dataset.
    Supports resume on interrupted downloads and validates files with MD5 checksums.

    \b
    Examples:

    # Download single session from KITTI
    mds download kitti --collection raw_data --sessions 2011_09_26_drive_0001

    # Download multiple sessions
    mds download kitti -c raw_data -s 2011_09_26_drive_0001,2011_09_26_drive_0002

    # Download all nuScenes trainval
    mds download nuscenes --collection v1.0-trainval

    # See download size first (dry-run)
    mds download kitti --estimate-only

    # Download to custom directory
    mds download kitti --data-dir /mnt/datasets
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
        click.echo(f"SESSIONS: {sessions}")
        if sessions:
            click.echo("SESSION NONE")
            session_list = [s.strip() for s in sessions.split(",")]
            click.echo(session_list)

        # ESTIMATE MODE
        if estimate_only:
            click.echo(f"\n{'='*60}")
            click.echo("Download Size Estimate")
            click.echo("=" * 60)

            for coll_id in collections_to_download:
                size_info = downloader.get_download_size(
                    collection_id=coll_id,
                    sessions=session_list or None,
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


# =============================================================================
# INFORMATION COMMANDS (About available datasets/data online)
# =============================================================================


@cli.command()
@click.argument(
    "dataset_name",
    type=click.Choice(get_available_datasets(), case_sensitive=False),
)
@click.option(
    "--collection",
    "-c",
    default=None,
    help="Show info for specific collection. If not specified, shows all.",
)
@click.option(
    "--verify",
    is_flag=True,
    help="Verify file availability on remote servers (may take a few minutes).",
)
@click.option(
    "--timeout",
    default=10,
    type=int,
    help="Timeout for verification requests in seconds. Default: 10",
)
def info(
    dataset_name: str,
    collection: Optional[str],
    verify: bool,
    timeout: int,
):
    """Show information about available dataset collections and sizes.

    Displays:
    - Available collections and their sessions
    - Download size per collection
    - File availability status (optional)

    This helps you understand what data is available before downloading.

    \b
    Examples:

    # Show all KITTI collections
    mds info kitti

    # Show specific collection
    mds info kitti --collection raw_data

    # Verify files are actually available on servers
    mds info kitti --verify

    # Check nuScenes with custom timeout
    mds info nuscenes --verify --timeout 30
    """
    try:
        # Initialize downloader
        downloader = DatasetDownloader(dataset=dataset_name.lower())

        click.echo(f"\n{'='*60}")
        click.echo(f"Dataset: {dataset_name.upper()}")
        click.echo("=" * 60)

        # Metadata
        config = downloader.config
        click.echo(f"\nName: {config.metadata.name}")
        click.echo(f"Description: {config.metadata.description}")
        click.echo(f"License: {config.metadata.license.name}")

        # Collections
        available_collections = [c.id for c in config.collections]

        if collection is None:
            collections_to_show = available_collections
        else:
            if collection not in available_collections:
                click.echo(
                    f"\n✗ Collection '{collection}' not found. "
                    f"Available: {', '.join(available_collections)}",
                    err=True,
                )
                raise click.Abort()
            collections_to_show = [collection]

        # Show each collection
        click.echo(f"\n{'─'*60}")
        click.echo("Collections:")
        click.echo("─" * 60)

        for coll_id in collections_to_show:
            coll = downloader.config.get_collection_by_id(coll_id)
            click.echo(f"\n  {coll_id}")
            click.echo(f"    Sessions: {len(coll.sessions)}")

            # Size info
            size_info = downloader.get_download_size(
                collection_id=coll_id,
                sessions=None,
                with_optional=True,
            )
            click.echo(f"    Total size: {size_info['total_readable']}")

            # Show first few sessions
            for _, session in enumerate(coll.sessions[:3]):
                click.echo(f"      - {session.id}")
            if len(coll.sessions) > 3:
                click.echo(f"      ... and {len(coll.sessions) - 3} more")

        # Verification (check if files are available)
        if verify:
            click.echo(f"\n{'─'*60}")
            click.echo("Checking file availability...")
            click.echo("─" * 60)

            status = downloader.health_check()

            available = sum(status.values())
            total = len(status)
            unavailable_count = total - available

            if unavailable_count > 0:
                click.echo(f"\n⚠ {available}/{total} files available")
                unavailable_ids = [k for k, v in status.items() if not v]
                for file_id in unavailable_ids[:5]:
                    click.echo(f"  - {file_id}")
                if len(unavailable_ids) > 5:
                    click.echo(f"  ... and {len(unavailable_ids) - 5} more")
            else:
                click.echo(f"\n✓ All {total} files available!")

        click.echo(f"\n{'='*60}\n")

    except FileNotFoundError as e:
        click.echo(f"✗ Dataset configuration not found: {e}", err=True)
        raise click.Abort() from None
    except Exception as e:
        click.echo(f"✗ Failed to get info: {e}", err=True)
        raise click.Abort() from None


if __name__ == "__main__":
    cli()
