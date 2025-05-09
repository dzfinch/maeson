"""Main module."""

import os
import tempfile
import requests
import rasterio
import ipyleaflet
import ipywidgets
import localtileserver
import ee
import geemap
from localtileserver import TileClient, get_leaflet_tile_layer
from ipywidgets import widgets, Dropdown, Button, VBox
from ipyleaflet import (
    WidgetControl,
    basemaps,
    basemap_to_tiles,
    WMSLayer,
    VideoOverlay,
    TileLayer,
    LocalTileLayer,
    DrawControl,
)

try:
    # primary: use leafmap if installed
    from leafmap.leafmap import Map as Leafmap
except ImportError:
    # fallback to pure ipyleaflet
    from ipyleaflet import Map as LeafletMap

    Leafmap = LeafletMap


class Map(Leafmap):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("toolbar_control", True)
        kwargs.setdefault("layer_control", True)
        super().__init__(*args, **kwargs)

    def add_basemap(self, basemap="Esri.WorldImagery"):
        """
        Args:
            basemap (str): Basemap name. Default is "Esri.WorldImagery".
        """
        """Add a basemap to the map."""
        basemaps = [
            "OpenStreetMap.Mapnik",
            "Stamen.Terrain",
            "Stamen.TerrainBackground",
            "Stamen.Watercolor",
            "Esri.WorldImagery",
            "Esri.DeLorme",
            "Esri.NatGeoWorldMap",
            "Esri.WorldStreetMap",
            "Esri.WorldTopoMap",
            "Esri.WorldGrayCanvas",
            "Esri.WorldShadedRelief",
            "Esri.WorldPhysical",
            "Esri.WorldTerrain",
            "Google.Satellite",
            "Google.Street",
            "Google.Hybrid",
            "Google.Terrain",
        ]
        url = eval(f"ipyleaflet.basemaps.{basemap}").build_url()
        basemap_layer = ipyleaflet.TileLayer(url=url, name=basemap)
        self.add(basemap_layer)

    def layer(self, layer) -> None:
        """
        Args:
            layer (str or dict): Layer to be added to the map.
            **kwargs: Additional arguments for the layer.
        Returns:
            None
        Raises:
            ValueError: If the layer is not a valid type.
        """
        """ Convert url to layer"""
        if isinstance(layer, str):
            layer = ipyleaflet.TileLayer(url=layer)
        elif isinstance(layer, dict):
            layer = ipyleaflet.GeoJSON(data=layer)
        elif not isinstance(layer, ipyleaflet.Layer):
            raise ValueError("Layer must be an instance of ipyleaflet.Layer")
        return layer

    def add_layer_control(self, position="topright") -> None:
        """Adds a layer control to the map.

        Args:
            position (str, optional): The position of the layer control. Defaults to 'topright'.
        """

        self.add(ipyleaflet.LayersControl(position=position))

    def add_geojson(self, geojson, **kwargs):
        """
        Args:
            geojson (dict): GeoJSON data.
            **kwargs: Additional arguments for the GeoJSON layer.
        """
        """Add a GeoJSON layer to the map."""
        geojson_layer = ipyleaflet.GeoJSON(data=geojson, **kwargs)
        self.add(geojson_layer)

    def set_center(self, lat, lon, zoom=6, **kwargs):
        """
        Args:
            lat (float): Latitude of the center.
            lon (float): Longitude of the center.
            zoom (int): Zoom level.
            **kwargs: Additional arguments for the map.
        """
        """Set the center of the map."""
        self.center = (lat, lon)
        self.zoom = zoom

    def center_object(self, obj, zoom=6, **kwargs):
        """
        Args:
            obj (str or dict): Object to center the map on.
            zoom (int): Zoom level.
            **kwargs: Additional arguments for the map.
        """
        """Center the map on an object."""
        if isinstance(obj, str):
            obj = ipyleaflet.GeoJSON(data=obj, **kwargs)
        elif not isinstance(obj, ipyleaflet.Layer):
            raise ValueError("Object must be an instance of ipyleaflet.Layer")
        self.center = (obj.location[0], obj.location[1])
        self.zoom = zoom

    def add_vector(self, vector, **kwargs):
        """
        Args:
            vector (dict): Vector data.
            **kwargs: Additional arguments for the GeoJSON layer.
        """
        """Add a vector layer to the map from Geopandas."""
        vector_layer = ipyleaflet.GeoJSON(data=vector, **kwargs)
        self.add(vector_layer)

    def add_raster(
        self,
        filepath: str,
        name: str = None,
        colormap="greys",
        opacity: float = 1.0,
        zoom_to_layer: bool = True,
        **kwargs,
    ):
        """
        Add a raster (COG) layer to the map and return it.

        Parameters
        ----------
        filepath : str
            URL or local path to a Cloud‑Optimized GeoTIFF.
        name : str, optional
            Display name for the layer. Defaults to filename.
        colormap : dict or str, optional
            A colormap dictionary or registered name (e.g. "viridis").
        opacity : float, optional
            0.0 (transparent) – 1.0 (opaque).
        zoom_to_layer : bool, optional
            If True, fit the map to the raster’s bounds after adding.
        **kwargs : dict
            Extra kwargs passed to `get_leaflet_tile_layer`.

        Returns
        -------
        ipyleaflet.Layer
            The tile layer that was added.
        """
        # 1) If it’s a GitHub “release/download” URL, pull it down locally
        if (
            filepath.startswith("https://github.com/")
            and "/releases/download/" in filepath
        ):
            fname = os.path.basename(filepath)
            tmp_dir = tempfile.gettempdir()
            local_fp = os.path.join(tmp_dir, fname)
            if not os.path.exists(local_fp):
                resp = requests.get(filepath, stream=True)
                resp.raise_for_status()
                with open(local_fp, "wb") as f:
                    for chunk in resp.iter_content(1024 * 1024):
                        f.write(chunk)
            filepath = local_fp

        # 2) Inspect with rasterio: get colormap if needed + bounds
        with rasterio.open(filepath) as src:
            if colormap is None:
                try:
                    colormap = src.colormap(1)
                except Exception:
                    colormap = "greys"
            left, bottom, right, top = src.bounds

        # 3) Spin up the tile server + leaflet layer
        client = TileClient(filepath)
        layer_name = name or os.path.basename(filepath)
        tile_layer = get_leaflet_tile_layer(
            client, name=layer_name, colormap=colormap, opacity=opacity, **kwargs
        )

        # 4) Add to the map
        try:
            self.add_layer(tile_layer)
        except AttributeError:
            # fallback if your class uses .add() instead
            self.add(tile_layer)

        # 5) Ensure it has a valid name
        if hasattr(tile_layer, "name") and not tile_layer.name:
            tile_layer.name = layer_name

        # 6) Auto‑zoom if requested
        if zoom_to_layer:
            sw = (bottom, left)
            ne = (top, right)
            try:
                self.fit_bounds([sw, ne])
            except Exception:
                # if you're using leafmap you could also call:
                # self.zoom_to_layer(tile_layer)
                pass

        return tile_layer

    def add_image(self, url, bounds, opacity=1, **kwargs):
        """
        Adds an image or animated GIF overlay to the map.

        Parameters:
            url (str): The URL of the image or GIF.
            bounds (tuple): Geographic coordinates as ((south, west), (north, east)).
            opacity (float, optional): The transparency level of the overlay (default is 1, fully opaque).
            **kwargs: Additional keyword arguments for ipyleaflet.ImageOverlay.

        Raises:
            ValueError: If bounds is not provided or is improperly formatted.
        """

        # Validate bounds: It should be a tuple of two coordinate tuples, each of length 2.
        if not (
            isinstance(bounds, tuple)
            and len(bounds) == 2
            and all(isinstance(coord, tuple) and len(coord) == 2 for coord in bounds)
        ):
            raise ValueError(
                "bounds must be a tuple in the format ((south, west), (north, east))"
            )

        # Create the image overlay using ipyleaflet.ImageOverlay.
        overlay = ipyleaflet.ImageOverlay(
            url=url, bounds=bounds, opacity=opacity, **kwargs
        )

        # Add the overlay to the map.
        self.add(overlay)
        self.center = [
            (bounds[0][0] + bounds[1][0]) / 2,
            (bounds[0][1] + bounds[1][1]) / 2,
        ]

    def add_video(
        self,
        url: str,
        bounds,
        opacity: float = 1.0,
        autoplay: bool = True,
        loop: bool = True,
        muted: bool = True,
        **kwargs,
    ):
        """
        Adds a video overlay to the map using ipyleaflet.VideoOverlay.
        """
        # 1) Validate & normalize bounds
        if not (
            isinstance(bounds, (tuple, list))
            and len(bounds) == 2
            and all(isinstance(c, (tuple, list)) and len(c) == 2 for c in bounds)
        ):
            raise ValueError("bounds must be ((south, west), (north, east))")

        bounds = [list(bounds[0]), list(bounds[1])]

        # 2) Create the VideoOverlay (url must be a string)
        overlay = VideoOverlay(
            url=url,
            bounds=bounds,
            opacity=opacity,
            autoplay=autoplay,
            loop=loop,
            muted=muted,
            **kwargs,
        )

        # 3) Add to map and fit to the bounds
        self.add_layer(overlay)  # or self.map.add_layer if you wrap it
        self.fit_bounds(bounds)

    def add_wms_layer(self, url, layers, name, format, transparent, **kwargs):
        """
        Adds a WMS (Web Map Service) layer to the map using ipyleaflet.WMSLayer.

        Parameters:
            url (str): Base WMS endpoint.
            layers (str): Comma-separated layer names.
            name (str): Display name for the layer.
            format (str): Image format (e.g., 'image/png').
            transparent (bool): Whether the WMS layer should be transparent.
            **kwargs: Additional keyword arguments for ipyleaflet.WMSLayer.
        """

        # Create the WMS layer using the provided parameters.
        wms_layer = WMSLayer(
            url=url,
            layers=layers,
            name=name,
            format=format,
            transparent=transparent,
            **kwargs,
        )

        # Add the WMS layer to the map.
        self.add(wms_layer)

    def add_basemap_dropdown(self):
        """
        Adds a dropdown + hide button as a map control.
        Keeps track of the current basemap layer so that selecting
        a new one removes the old and adds the new immediately.

        Returns:
            None
        """
        # 1. define your choices
        basemap_dict = {
            "OpenStreetMap": basemaps.OpenStreetMap.Mapnik,
            "OpenTopoMap": basemaps.OpenTopoMap,
            "Esri.WorldImagery": basemaps.Esri.WorldImagery,
            "CartoDB.DarkMatter": basemaps.CartoDB.DarkMatter,
        }

        # 2. build widgets
        dropdown = widgets.Dropdown(
            options=list(basemap_dict.keys()),
            value="OpenStreetMap",
            layout={"width": "180px"},
            description="Basemap:",
        )
        hide_btn = widgets.Button(description="Hide", button_style="danger")
        container = widgets.VBox([dropdown, hide_btn])

        # 3. add the initial basemap layer and remember it
        initial = basemap_dict[dropdown.value]
        self._current_basemap = basemap_to_tiles(initial)
        self.add_layer(self._current_basemap)

        # 4. when user picks a new basemap, swap layers
        def _on_change(change):
            if change["name"] == "value":
                new_tiles = basemap_to_tiles(basemap_dict[change["new"]])
                # remove old
                self.remove_layer(self._current_basemap)
                # add new & store reference
                self._current_basemap = new_tiles
                self.add_layer(self._current_basemap)

        dropdown.observe(_on_change, names="value")

        # 5. hide control if needed
        hide_btn.on_click(lambda _: setattr(container.layout, "display", "none"))

        # 6. wrap in a WidgetControl and add to map
        ctrl = WidgetControl(widget=container, position="topright")
        self.add_control(ctrl)

    def add_earthengine(self, ee_object, vis_params=None, name="EE Layer"):
        """
        Adds an Earth Engine layer to the map.

        Parameters
        ----------
        ee_object : ee.Image, ee.ImageCollection, or str
            If str, will be wrapped as ee.Image; for ImageCollection,
            you should reduce it (e.g. .mean()) before passing.
        vis_params : dict, optional
            Visualization parameters, e.g. {"min":0,"max":3000,"palette":["blue","red"]}.
        name : str, optional
            A display name for the layer.
        """
        # 1) Initialize EE if needed
        try:
            ee.Initialize()
        except Exception:
            ee.Authenticate()
            ee.Initialize()

        # 2) Wrap strings into Images
        if isinstance(ee_object, str):
            ee_object = ee.Image(ee_object)

        # 3) Build the TileLayer via geemap helper
        vis_params = vis_params or {}
        tile_layer = geemap.ee_tile_layer(ee_object, vis_params, name)

        # 4) Add to the map
        self.add_layer(tile_layer)

        # 5) Optionally fit bounds (EE layers often global)
        # comment this out if you don’t want auto‑zoom
        try:
            bounds = ee_object.geometry().bounds().getInfo()["coordinates"][0]
            # bounds is [[lon, lat], …], ipyleaflet wants [[lat, lon], …]
            latlng_bounds = [[lat, lon] for lon, lat in bounds]
            self.fit_bounds(latlng_bounds)
        except Exception:
            pass

        return tile_layer
