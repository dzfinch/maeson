"""Main module."""

import ipyleaflet
import folium


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

    def add_raster(self, filepath, **kwargs):
        """Add a raster layer to the map."""
        raster_layer = ipyleaflet.ImageOverlay(url=filepath, **kwargs)
        self.add(raster_layer)

    def add_image(self, image, bounds=None, **kwargs):
        """
        Args:
            image (str): URL to the image file.
            bounds (list): List of coordinates for the bounds of the image.
            **kwargs: Additional arguments for the ImageOverlay.
        """
        """Add an image to the map."""
        if bounds is None:
            bounds = [[-90, -180], [90, 180]]
        image_layer = ipyleaflet.ImageOverlay(url=image, bounds=bounds, **kwargs)
        self.add(image_layer)

    def add_geojson(self, geojson, **kwargs):
        """
        Args:
            geojson (dict): GeoJSON data.
            **kwargs: Additional arguments for the GeoJSON layer.
        """
        """Add a GeoJSON layer to the map."""
        geojson_layer = ipyleaflet.GeoJSON(data=geojson, **kwargs)
        self.add(geojson_layer)

    def add_video(self, video, bounds=None, **kwargs):
        """
        Args:
            video (str): URL to the video file.
            bounds (list): List of coordinates for the bounds of the video.
            **kwargs: Additional arguments for the VideoOverlay.
        """
        """Add a video layer to the map."""
        if bounds is None:
            bounds = [[-90, -180], [90, 180]]
        video_layer = ipyleaflet.VideoOverlay(url=video, bounds=bounds, **kwargs)
        self.add(video_layer)

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

    def add_wms(self, url, layers, **kwargs):
        """
        Args:
            url (str): URL to the WMS service.
            layers (str): Comma-separated list of layers to be added.
            **kwargs: Additional arguments for the WMS layer.
        """
        """Add a WMS layer to the map."""
        wms_layer = ipyleaflet.WMSLayer(url=url, layers=layers, **kwargs)
        self.add(wms_layer)

    def add_vector(self, vector, **kwargs):
        """
        Args:
            vector (dict): Vector data.
            **kwargs: Additional arguments for the GeoJSON layer.
        """
        """Add a vector layer to the map from Geopandas."""
        vector_layer = ipyleaflet.GeoJSON(data=vector, **kwargs)
        self.add(vector_layer)
