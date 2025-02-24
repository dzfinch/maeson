"""
gps_metrics.py

A module for calculating GPS accuracy metrics from Emlid data according to ASPRS standards.
"""

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from typing import Tuple, Optional


def calculate_accuracy_metrics(
    gdf: gpd.GeoDataFrame,
    spot_id_col: str = "spot_id",
    crs: Optional[str] = None,
    return_merged: bool = False,
) -> Tuple[gpd.GeoDataFrame, Optional[gpd.GeoDataFrame]]:
    """
    Calculate GPS accuracy metrics for grouped points according to ASPRS standards.

    Parameters
    ----------
    gdf : GeoDataFrame
        Input GeoDataFrame containing GPS points with spot identifiers
    spot_id_col : str, optional
        Column name containing spot identifiers, default 'spot_id'
    crs : str, optional
        Target CRS for distance calculations (auto-detects UTM if None)
    return_merged : bool, optional
        Whether to return merged DataFrame with original points and distances

    Returns
    -------
    metrics_gdf : GeoDataFrame
        Metrics per spot with geometry of mean points
    merged_gdf : GeoDataFrame, optional
        Original data with calculated distances (only if return_merged=True)

    Raises
    ------
    ValueError
        If input is not a GeoDataFrame or required columns are missing
    """

    # Validate input
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise ValueError("Input must be a GeoDataFrame")
    if spot_id_col not in gdf.columns:
        raise ValueError(f"Spot ID column '{spot_id_col}' not found in DataFrame")

    # Store original CRS and reproject
    original_crs = gdf.crs
    working_gdf = gdf.copy()

    # Auto-detect UTM CRS if not provided
    if crs is None:
        avg_lon = working_gdf.geometry.x.mean()
        utm_zone = int((avg_lon + 180) // 6 + 1)
        crs = f"EPSG:326{utm_zone:02d}"  # Assumes northern hemisphere

    working_gdf = working_gdf.to_crs(crs)

    # Add coordinate columns
    working_gdf["x"] = working_gdf.geometry.x
    working_gdf["y"] = working_gdf.geometry.y

    # Calculate mean points
    mean_points = (
        working_gdf.groupby(spot_id_col)[["x", "y"]]
        .mean()
        .reset_index()
        .rename(columns={"x": "x_mean", "y": "y_mean"})
    )

    # Merge mean points with original data
    merged = working_gdf.merge(mean_points, on=spot_id_col, suffixes=("", "_mean"))

    # Calculate distances
    merged["distance"] = np.sqrt(
        (merged["x"] - merged["x_mean"]) ** 2 + (merged["y"] - merged["y_mean"]) ** 2
    )
    merged["squared_distance"] = merged["distance"] ** 2

    # Calculate metrics
    metrics = (
        merged.groupby(spot_id_col)
        .agg(
            n_points=pd.NamedAgg(column="distance", aggfunc="count"),
            rmse=pd.NamedAgg(
                column="squared_distance", aggfunc=lambda x: np.sqrt(x.mean())
            ),
            std_dev=pd.NamedAgg(column="distance", aggfunc=lambda x: x.std(ddof=1)),
            max_distance=pd.NamedAgg(column="distance", aggfunc="max"),
        )
        .reset_index()
    )

    # Create metrics GeoDataFrame
    metrics_gdf = gpd.GeoDataFrame(
        metrics.merge(mean_points, on=spot_id_col),
        geometry=gpd.points_from_xy(mean_points["x_mean"], mean_points["y_mean"]),
        crs=crs,
    ).to_crs(
        original_crs
    )  # Return to original CRS

    # Rename columns to standard names
    metrics_gdf = metrics_gdf.rename(columns={"x_mean": "mean_x", "y_mean": "mean_y"})[
        [spot_id_col, "n_points", "rmse", "std_dev", "max_distance", "geometry"]
    ]

    if return_merged:
        merged_gdf = merged.drop(["x", "y"], axis=1).to_crs(original_crs)
        return metrics_gdf, merged_gdf

    return metrics_gdf, None
