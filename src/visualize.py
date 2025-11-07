"""Visualization utilities for creating static and interactive maps."""

import logging
from pathlib import Path
from typing import Any, Optional

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import Colormap

logger = logging.getLogger(__name__)


def export_static_choropleth(
    gdf: gpd.GeoDataFrame,
    metric_col: str,
    title: str,
    out_path: str | Path,
    cmap: str = "RdBu",
    figsize: tuple[int, int] = (12, 10),
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    legend_label: Optional[str] = None,
) -> None:
    """
    Export a static choropleth map as PNG.

    Args:
        gdf: GeoDataFrame with geometry and data
        metric_col: Column name to visualize
        title: Map title
        out_path: Output PNG file path
        cmap: Matplotlib colormap name
        figsize: Figure size (width, height)
        vmin: Minimum value for color scale (default: auto)
        vmax: Maximum value for color scale (default: auto)
        legend_label: Label for color bar (default: metric_col)
    """
    from .io_utils import ensure_output_dir

    logger.info(f"Creating static map: {title}")

    if metric_col not in gdf.columns:
        raise ValueError(f"Column '{metric_col}' not found in GeoDataFrame")

    # Remove missing values
    plot_gdf = gdf[gdf[metric_col].notna()].copy()

    if plot_gdf.empty:
        logger.warning(f"No data to plot for metric '{metric_col}'")
        return

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot choropleth
    plot_gdf.plot(
        column=metric_col,
        cmap=cmap,
        linewidth=0.3,
        edgecolor="0.4",
        alpha=0.9,
        ax=ax,
        legend=True,
        vmin=vmin,
        vmax=vmax,
        legend_kwds={
            "label": legend_label or metric_col,
            "orientation": "horizontal",
            "shrink": 0.8,
            "pad": 0.05,
        },
    )

    ax.set_title(title, fontsize=16, fontweight="bold")
    ax.axis("off")

    # Try to add basemap if contextily is available
    try:
        import contextily as ctx

        # Reproject to Web Mercator for basemap
        plot_gdf_wm = plot_gdf.to_crs(epsg=3857)
        ctx.add_basemap(
            ax,
            crs=plot_gdf_wm.crs.to_string(),
            source=ctx.providers.CartoDB.Positron,
            alpha=0.3,
        )
    except Exception as e:
        logger.debug(f"Could not add basemap: {e}")

    plt.tight_layout()

    # Save
    out_path = Path(out_path)
    ensure_output_dir(out_path.parent)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()

    logger.info(f"Saved map to {out_path}")


def export_folium_map(
    gdf: gpd.GeoDataFrame,
    metric_col: str,
    title: str,
    out_path: str | Path,
    cmap: str = "RdBu",
    tooltip_cols: Optional[list[str]] = None,
) -> None:
    """
    Export an interactive Folium map as HTML.

    Args:
        gdf: GeoDataFrame with geometry and data
        metric_col: Column name to visualize
        title: Map title
        out_path: Output HTML file path
        cmap: Colormap name (for mapclassify)
        tooltip_cols: Additional columns to show in tooltip
    """
    import folium
    from folium import plugins

    from .io_utils import ensure_output_dir

    logger.info(f"Creating interactive map: {title}")

    if metric_col not in gdf.columns:
        raise ValueError(f"Column '{metric_col}' not found in GeoDataFrame")

    # Remove missing values
    plot_gdf = gdf[gdf[metric_col].notna()].copy()

    if plot_gdf.empty:
        logger.warning(f"No data to plot for metric '{metric_col}'")
        return

    # Reproject to WGS84 for Folium
    plot_gdf = plot_gdf.to_crs(epsg=4326)

    # Calculate map center
    bounds = plot_gdf.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="CartoDB positron",
    )

    # Determine color scheme
    try:
        import mapclassify

        # Use quantiles for better distribution
        scheme = mapclassify.Quantiles(plot_gdf[metric_col], k=7)
        bins = list(scheme.bins)
    except Exception as e:
        logger.debug(f"Could not use mapclassify: {e}")
        bins = None

    # Add choropleth
    folium.Choropleth(
        geo_data=plot_gdf,
        data=plot_gdf,
        columns=[plot_gdf.index, metric_col],
        key_on="feature.id",
        fill_color=cmap,
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name=metric_col,
        bins=bins,
        reset=True,
    ).add_to(m)

    # Add tooltips with precinct info
    if tooltip_cols is None:
        # Default tooltip columns
        tooltip_cols = [col for col in plot_gdf.columns if col != "geometry"][:5]

    # Create tooltip layer
    style_function = lambda x: {
        "fillColor": "#ffffff",
        "color": "#000000",
        "fillOpacity": 0.1,
        "weight": 0.1,
    }
    highlight_function = lambda x: {
        "fillColor": "#000000",
        "color": "#000000",
        "fillOpacity": 0.3,
        "weight": 1.5,
    }

    tooltip = folium.GeoJsonTooltip(
        fields=tooltip_cols,
        aliases=[col.replace("_", " ").title() for col in tooltip_cols],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: #F0EFEF;
            border: 2px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """,
    )

    folium.GeoJson(
        plot_gdf,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=tooltip,
    ).add_to(m)

    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 50px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; font-weight: bold; padding: 10px">
        {title}
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Add fullscreen button
    plugins.Fullscreen().add_to(m)

    # Save
    out_path = Path(out_path)
    ensure_output_dir(out_path.parent)
    m.save(str(out_path))

    logger.info(f"Saved interactive map to {out_path}")


def create_maps_for_metric(
    cfg: dict[str, Any],
    year: str,
    metric: str,
    title_suffix: str = "",
) -> None:
    """
    Create both static and interactive maps for a specific year and metric.

    Args:
        cfg: Configuration dictionary
        year: Year to visualize
        metric: Metric column name
        title_suffix: Additional text for map title
    """
    base_year = str(cfg["base_year"])
    gpkg_path = Path(cfg["output"]["harmonized_gpkg"])
    layer_name = f"yr_{year}_on_{base_year}"

    logger.info(f"Loading layer {layer_name} from {gpkg_path}")

    try:
        gdf = gpd.read_file(gpkg_path, layer=layer_name)
    except Exception as e:
        raise ValueError(f"Failed to load layer {layer_name}: {e}")

    if metric not in gdf.columns:
        raise ValueError(
            f"Metric '{metric}' not found in layer. Available columns: {list(gdf.columns)}"
        )

    # Generate title
    title = f"Franklin County Precincts - {year}"
    if title_suffix:
        title += f" - {title_suffix}"
    else:
        title += f" - {metric.replace('_', ' ').title()}"

    # Determine colormap based on metric type
    if "swing" in metric.lower() or "change" in metric.lower():
        cmap = "RdBu"  # Diverging for swing (Blue=Dem shift, Red=Rep shift)
        # Center on zero for swing metrics
        max_abs = gdf[metric].abs().max()
        vmin, vmax = -max_abs, max_abs
    elif "share" in metric.lower():
        cmap = "RdBu"  # Democratic = blue, Republican = red
        vmin, vmax = 0, 1
    else:
        cmap = "YlOrRd"  # Sequential for turnout
        vmin, vmax = None, None

    # Create static map
    maps_dir = Path(cfg["output"]["maps_dir"])
    static_path = maps_dir / f"{year}_{metric}.png"
    export_static_choropleth(
        gdf=gdf,
        metric_col=metric,
        title=title,
        out_path=static_path,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )

    # Create interactive map
    interactive_dir = Path(cfg["output"]["interactive_dir"])
    interactive_path = interactive_dir / f"{year}_{metric}.html"

    # Get ID column for tooltip
    base_id = cfg["id_fields"][base_year]
    tooltip_cols = [base_id, metric, "D_votes", "R_votes", "total"]
    tooltip_cols = [col for col in tooltip_cols if col in gdf.columns]

    export_folium_map(
        gdf=gdf,
        metric_col=metric,
        title=title,
        out_path=interactive_path,
        cmap=cmap,
        tooltip_cols=tooltip_cols,
    )


def create_comparison_map(
    cfg: dict[str, Any],
    years: list[str],
    metric: str,
) -> None:
    """
    Create a side-by-side comparison map for multiple years.

    Args:
        cfg: Configuration dictionary
        years: List of years to compare (max 4)
        metric: Metric to visualize
    """
    if len(years) > 4:
        raise ValueError("Maximum 4 years for comparison map")

    base_year = str(cfg["base_year"])
    gpkg_path = Path(cfg["output"]["harmonized_gpkg"])

    # Load data for all years
    gdfs = []
    for year in years:
        layer_name = f"yr_{year}_on_{base_year}"
        try:
            gdf = gpd.read_file(gpkg_path, layer=layer_name)
            gdfs.append((year, gdf))
        except Exception as e:
            logger.warning(f"Could not load {layer_name}: {e}")

    if not gdfs:
        logger.error("No data loaded for comparison")
        return

    # Determine global color scale
    all_values = pd.concat([gdf[metric] for _, gdf in gdfs if metric in gdf.columns])
    if "swing" in metric.lower() or "change" in metric.lower():
        cmap = "RdBu"  # Blue=Dem shift, Red=Rep shift
        max_abs = all_values.abs().max()
        vmin, vmax = -max_abs, max_abs
    elif "share" in metric.lower():
        cmap = "RdBu"  # Blue=Dem, Red=Rep
        vmin, vmax = 0, 1
    else:
        cmap = "YlOrRd"  # Sequential for turnout
        vmin, vmax = all_values.min(), all_values.max()

    # Create subplot figure
    n_maps = len(gdfs)
    ncols = min(2, n_maps)
    nrows = (n_maps + 1) // 2

    fig, axes = plt.subplots(nrows, ncols, figsize=(12 * ncols, 10 * nrows))
    if n_maps == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if n_maps > 2 else axes

    for idx, (year, gdf) in enumerate(gdfs):
        ax = axes[idx]
        plot_gdf = gdf[gdf[metric].notna()].copy()

        plot_gdf.plot(
            column=metric,
            cmap=cmap,
            linewidth=0.3,
            edgecolor="0.4",
            alpha=0.9,
            ax=ax,
            legend=True,
            vmin=vmin,
            vmax=vmax,
            legend_kwds={"shrink": 0.8, "pad": 0.05},
        )

        ax.set_title(f"{year} - {metric.replace('_', ' ').title()}", fontsize=14, fontweight="bold")
        ax.axis("off")

    # Hide unused subplots
    for idx in range(n_maps, len(axes)):
        axes[idx].axis("off")

    plt.suptitle(
        f"Franklin County Precincts - {metric.replace('_', ' ').title()} Comparison",
        fontsize=16,
        fontweight="bold",
    )
    plt.tight_layout()

    # Save
    maps_dir = Path(cfg["output"]["maps_dir"])
    from .io_utils import ensure_output_dir

    ensure_output_dir(maps_dir)
    out_path = maps_dir / f"comparison_{metric}_{'_'.join(years)}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()

    logger.info(f"Saved comparison map to {out_path}")

