"""Main module."""

import ipyleaflet
import folium
import rasterio
import localtileserver
import ipywidgets as widgets
from ipywidgets import Dropdown, Button, VBox
from ipyleaflet import WidgetControl, basemaps, basemap_to_tiles
from ipyleaflet import WMSLayer, VideoOverlay, TileLayer, LocalTileLayer


class Map(ipyleaflet.Map):
    def __init__(self, center=[20, 0], zoom=2, **kwargs):
        super(Map, self).__init__(center=center, zoom=zoom, **kwargs)

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

    def add_raster(self, filepath, name=None, colormap="greys", opacity=1, **kwargs):
        """
        Add a raster (COG) layer to the map.

        Parameters:
        filepath (str): Path or URL to the cloud-optimized GeoTIFF (COG).
        name (str, optional): Display name for the layer.
        colormap (dict or str, optional): A colormap dictionary or a string identifier.
        opacity (float, optional): Transparency level (default is 1 for fully opaque).
        **kwargs: Additional keyword arguments to pass to the tile layer generator.
        """
        import rasterio
        from localtileserver import TileClient, get_leaflet_tile_layer

        # Open the raster with rasterio to inspect metadata.
        with rasterio.open(filepath) as src:
            # If no colormap is provided (i.e., None), try extracting it from the raster's first band.
            if colormap is None:
                try:
                    colormap = src.colormap(1)
                except Exception:
                    # Leave colormap unchanged if extraction fails.
                    colormap = "greys"

        # Create the tile client from the provided file path.
        client = TileClient(filepath)

        # Generate the leaflet tile layer using the provided parameters.
        tile_layer = get_leaflet_tile_layer(
            client, name=name, colormap=colormap, opacity=opacity, **kwargs
        )

        # Add the layer to the viewer and update the center and zoom based on the raster metadata.
        self.add(tile_layer)

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

    def add_video(self, url, bounds, opacity=1.0, **kwargs):
        """
        Adds a video overlay to the map using ipyleaflet.VideoOverlay.

        Parameters:
            url (str or list): The URL or list of URLs for the video file(s).
            bounds (tuple): Geographic bounds in the format ((south, west), (north, east)).
            opacity (float): Transparency level of the overlay (0 = fully transparent, 1 = fully opaque).
            **kwargs: Additional keyword arguments for ipyleaflet.VideoOverlay.
        """

        # Validate and normalize bounds format
        if not (
            isinstance(bounds, (tuple, list))
            and len(bounds) == 2
            and all(
                isinstance(coord, (tuple, list)) and len(coord) == 2 for coord in bounds
            )
        ):
            raise ValueError(
                "bounds must be provided as ((south, west), (north, east))"
            )

        # Convert bounds to tuple of tuples
        bounds = tuple(tuple(coord) for coord in bounds)

        # Create and add the VideoOverlay
        overlay = VideoOverlay(url=url, bounds=bounds, opacity=opacity, **kwargs)
        self.add(overlay)

        # Center the map on the video bounds
        south, west = bounds[0]
        north, east = bounds[1]
        self.center = [(south + north) / 2, (west + east) / 2]

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
