# src/mobility_datasets/cli/main.py
"""Command-line interface for mobility-datasets."""

import click


@click.group()
def cli():
    """Mobility Datasets CLI - Download and manage autonomous driving datasets."""
    pass


@cli.group()
def dataset():
    """Dataset management commands."""
    pass


@dataset.command()
@click.argument("name", type=click.Choice(["kitti"]))
@click.option(
    "--components", "-c", help="Components to download (comma-separated, e.g., oxts,calib)"
)
@click.option("--all", "download_all", is_flag=True, help="Download all components")
@click.option("--data-dir", default="./data", help="Data directory")
@click.option("--keep-zip", is_flag=True, help="Keep zip files after extraction")
def download(name, components, download_all, data_dir, keep_zip):
    """Download dataset files."""
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
