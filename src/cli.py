"""Command-line interface for Franklin Shifts precinct analysis."""

import logging
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.logging import RichHandler

app = typer.Typer(
    name="ffs",
    help="Franklin Shifts - Analyze precinct-level partisan shifts in Franklin County, Ohio",
    add_completion=False,
)

console = Console()


def setup_logging(level: str = "INFO") -> None:
    """Configure logging with rich output."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
    )


@app.command()
def init(
    config_path: str = typer.Option("config/project.yaml", "--config", "-c", help="Config file path"),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
) -> None:
    """
    Initialize and validate project configuration.

    Checks that config file exists, paths are valid, and dependencies are available.
    """
    setup_logging(log_level)
    logging.getLogger(__name__)

    console.print("[bold cyan]Franklin Shifts - Initialization[/bold cyan]\n")

    # Check config file
    config_file = Path(config_path)
    if not config_file.exists():
        console.print(f"[bold red]✗[/bold red] Config file not found: {config_path}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Config file found: {config_path}")

    # Load config
    from .harmonize import load_config

    try:
        cfg = load_config(config_path)
        console.print("[green]✓[/green] Config loaded successfully")
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to load config: {e}")
        raise typer.Exit(1)

    # Validate structure
    required_keys = ["base_year", "crs", "id_fields", "paths"]
    missing = [k for k in required_keys if k not in cfg]
    if missing:
        console.print(f"[bold red]✗[/bold red] Missing config keys: {missing}")
        raise typer.Exit(1)

    console.print("[green]✓[/green] Config structure valid")
    console.print(f"  Base year: {cfg['base_year']}")
    console.print(f"  CRS: {cfg['crs']}")
    console.print(f"  Years configured: {len(cfg['paths']['shapefiles'])}")

    # Check dependencies
    try:
        import geopandas
        import pandas
        import shapely

        console.print("[green]✓[/green] Core dependencies available")
        console.print(f"  GeoPandas: {geopandas.__version__}")
        console.print(f"  Shapely: {shapely.__version__}")
    except ImportError as e:
        console.print(f"[bold red]✗[/bold red] Missing dependency: {e}")
        raise typer.Exit(1)

    # Create output directories
    from .io_utils import ensure_output_dir

    output_dirs = [
        cfg.get("output", {}).get("crosswalk_dir", "data/interim/crosswalks"),
        Path(cfg.get("output", {}).get("harmonized_gpkg", "data/processed/harmonized.gpkg")).parent,
        cfg.get("output", {}).get("maps_dir", "data/processed/maps"),
        cfg.get("output", {}).get("interactive_dir", "data/processed/interactive"),
    ]

    for d in output_dirs:
        ensure_output_dir(d)

    console.print("[green]✓[/green] Output directories created")

    console.print("\n[bold green]✓ Initialization complete![/bold green]")


@app.command()
def crosswalk(
    year: str = typer.Argument(..., help="Year to build crosswalk for"),
    weight: str = typer.Option("area", "--weight", "-w", help="Weighting method (area or pop)"),
    config_path: str = typer.Option("config/project.yaml", "--config", "-c"),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """
    Build spatial crosswalk from a past year to base geography.

    Example: ffs crosswalk 2008 --weight area
    """
    setup_logging(log_level)
    logger = logging.getLogger(__name__)

    from .harmonize import load_config

    cfg = load_config(config_path)
    base_year = str(cfg["base_year"])

    if year == base_year:
        console.print(f"[yellow]Warning:[/yellow] Year {year} is the base year, no crosswalk needed")
        return

    console.print(f"[bold cyan]Building crosswalk: {year} → {base_year}[/bold cyan]\n")

    try:
        from .harmonize import reallocate_votes_to_base

        _, crosswalk_df = reallocate_votes_to_base(year, cfg, weight=weight, save_outputs=True)

        console.print("\n[bold green]✓ Crosswalk complete![/bold green]")
        console.print(f"  Mappings: {len(crosswalk_df)}")
        console.print(f"  Coverage: {crosswalk_df.groupby(year)['frac'].sum().mean():.1%}")
    except Exception as e:
        console.print(f"\n[bold red]✗ Failed:[/bold red] {e}")
        logger.exception("Crosswalk failed")
        raise typer.Exit(1)


@app.command()
def harmonize(
    year: str = typer.Argument(..., help="Year to harmonize"),
    weight: str = typer.Option("area", "--weight", "-w", help="Weighting method (area or pop)"),
    config_path: str = typer.Option("config/project.yaml", "--config", "-c"),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """
    Reallocate votes from a past year to base geography.

    Builds crosswalk and reallocates votes, saving GeoPackage layer and CSV.

    Example: ffs harmonize 2008
    """
    setup_logging(log_level)

    from .harmonize import load_config

    cfg = load_config(config_path)
    base_year = str(cfg["base_year"])

    console.print(f"[bold cyan]Harmonizing {year} → {base_year}[/bold cyan]\n")

    try:
        from .harmonize import reallocate_votes_to_base

        gdf, _ = reallocate_votes_to_base(year, cfg, weight=weight, save_outputs=True)

        console.print("\n[bold green]✓ Harmonization complete![/bold green]")
        console.print(f"  Precincts: {len(gdf)}")
        console.print(f"  Total votes: {gdf['total'].sum():,}")
        console.print(f"  D share: {gdf['D_share'].mean():.1%}")
    except Exception as e:
        console.print(f"\n[bold red]✗ Failed:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def harmonize_all(
    weight: str = typer.Option("area", "--weight", "-w", help="Weighting method (area or pop)"),
    config_path: str = typer.Option("config/project.yaml", "--config", "-c"),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """
    Harmonize all non-base years to base geography.

    Processes all years defined in config, building crosswalks and reallocating votes.

    Example: ffs harmonize-all
    """
    setup_logging(log_level)

    from .harmonize import harmonize_all as harmonize_all_impl
    from .harmonize import load_config

    cfg = load_config(config_path)
    base_year = str(cfg["base_year"])
    all_years = list(cfg["paths"]["shapefiles"].keys())

    console.print(f"[bold cyan]Harmonizing all years → {base_year}[/bold cyan]")
    console.print(f"Years: {', '.join(all_years)}\n")

    try:
        harmonize_all_impl(cfg, weight=weight)
        console.print("\n[bold green]✓ All years harmonized successfully![/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]✗ Failed:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def metrics(
    config_path: str = typer.Option("config/project.yaml", "--config", "-c"),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """
    Compute partisan metrics and time-series tables.

    Reads harmonized data and computes D_share, swings, turnout changes, etc.
    Saves both long and wide format CSV files.

    Example: ffs metrics
    """
    setup_logging(log_level)

    from .harmonize import load_config
    from .metrics import compute_and_save_metrics

    cfg = load_config(config_path)

    console.print("[bold cyan]Computing metrics and time-series[/bold cyan]\n")

    try:
        compute_and_save_metrics(cfg)
        console.print("\n[bold green]✓ Metrics computed successfully![/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]✗ Failed:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def maps(
    year: str = typer.Argument(..., help="Year to visualize"),
    metric: str = typer.Argument(..., help="Metric to map (e.g., D_share, swing_vs_2008)"),
    config_path: str = typer.Option("config/project.yaml", "--config", "-c"),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """
    Create static PNG and interactive HTML maps for a year and metric.

    Example: ffs maps 2024 D_share
    Example: ffs maps 2020 swing_vs_2008
    """
    setup_logging(log_level)

    from .harmonize import load_config
    from .visualize import create_maps_for_metric

    cfg = load_config(config_path)

    console.print(f"[bold cyan]Creating maps: {year} - {metric}[/bold cyan]\n")

    try:
        create_maps_for_metric(cfg, year, metric)
        console.print("\n[bold green]✓ Maps created successfully![/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]✗ Failed:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def summary(
    config_path: str = typer.Option("config/project.yaml", "--config", "-c"),
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """
    Display county-wide aggregates and trends.

    Shows summary statistics from processed data.

    Example: ffs summary
    """
    setup_logging(log_level)

    from .harmonize import load_config
    from .metrics import build_timeseries_table, county_aggregates

    cfg = load_config(config_path)

    console.print("[bold cyan]County-wide Summary[/bold cyan]\n")

    try:
        df_long = build_timeseries_table(cfg)
        agg = county_aggregates(df_long)

        # Display table
        console.print("[bold]County-Wide Results by Year:[/bold]\n")

        for _, row in agg.iterrows():
            swing_str = f", Swing: {row['swing_yoy']:+.1%}" if pd.notna(row["swing_yoy"]) else ""
            turnout_str = (
                f", Turnout Δ: {row['turnout_change_yoy_pct']:+.1%}"
                if pd.notna(row["turnout_change_yoy_pct"])
                else ""
            )

            console.print(
                f"  {row['year']}: D={row['D_share']:.1%}, "
                f"Votes={row['turnout']:,.0f}{swing_str}{turnout_str}"
            )

        console.print("\n[bold green]✓ Summary complete![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]✗ Failed:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def demo(
    log_level: str = typer.Option("INFO", "--log-level", "-l"),
) -> None:
    """
    Run complete pipeline on synthetic example data.

    Creates synthetic precincts, runs harmonization, computes metrics, and generates maps.
    Useful for testing and CI.

    Example: ffs demo
    """
    setup_logging(log_level)
    logger = logging.getLogger(__name__)

    console.print("[bold cyan]Running Demo Pipeline[/bold cyan]\n")

    try:
        # Generate synthetic data
        console.print("[bold]Step 1:[/bold] Generating synthetic data...")
        from .demo import generate_synthetic_example

        demo_config = generate_synthetic_example()

        # Harmonize
        console.print("\n[bold]Step 2:[/bold] Harmonizing years...")
        from .harmonize import harmonize_all as harmonize_all_impl

        harmonize_all_impl(demo_config, weight="area")

        # Metrics
        console.print("\n[bold]Step 3:[/bold] Computing metrics...")
        from .metrics import compute_and_save_metrics

        compute_and_save_metrics(demo_config)

        # Maps
        console.print("\n[bold]Step 4:[/bold] Creating maps...")
        from .visualize import create_maps_for_metric

        create_maps_for_metric(demo_config, "2024", "D_share")
        create_maps_for_metric(demo_config, "2024", "swing_vs_2020")

        console.print("\n[bold green]✓ Demo pipeline complete![/bold green]")
        console.print("  Check data/examples/ for outputs")

    except Exception as e:
        console.print(f"\n[bold red]✗ Demo failed:[/bold red] {e}")
        logger.exception("Demo failed")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

