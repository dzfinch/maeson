"""Main module."""

import ipyleaflet


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
        
    def add_layer(self, layer) -> None:
        """
        Args:
            layer (ipyleaflet.Layer): Layer to be added to the map.
            **kwargs: Additional arguments for the layer.
        Returns:
            None
        Raises:
            ValueError: If the layer is not an instance of ipyleaflet.Layer.
        """ 
        """Add a layer to the map."""
        if isinstance(layer, ipyleaflet.Layer):
            self.add(layer)
        else:
            raise ValueError("Layer must be an instance of ipyleaflet.Layer")
        
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
    
    def zoom_to(self, bounds):
        """
        Args:
            bounds (list): List of coordinates for the bounds to zoom to.
        1. [[lat1, lon1], [lat2, lon2]] for a rectangular area.
        2. [[lat, lon]] for a single point.
        """
        """Zoom to the given bounds."""
        if len(bounds) == 1:
            # Single point
            bounds = [[bounds[0][0] - 0.01, bounds[0][1] - 0.01],
                      [bounds[0][0] + 0.01, bounds[0][1] + 0.01]]
        elif len(bounds) == 2:
            # Rectangular area
            bounds = [[bounds[0][0] - 0.01, bounds[0][1] - 0.01],
                      [bounds[1][0] + 0.01, bounds[1][1] + 0.01]]
        else:
            raise ValueError("Bounds must be a list of coordinates.")
        self.fit_bounds(bounds)
        
    def add_wms(self, url, layers, format=format, transparent=transparent, **kwargs):
        """
        Args:
            url (str): URL to the WMS server.
            layers (str): Comma-separated list of layer names.
            **kwargs: Additional arguments for the WMS layer.
        """
        """Add a WMS layer to the map."""
        if not url.startswith("http"):
            raise ValueError("URL must start with http or https.")
        if not layers:
            raise ValueError("Layers must be a comma-separated string.")
        if not format:
            format = "image/png"
        if not transparent:
            transparent = True
        wms_layer = ipyleaflet.WMSLayer(url=url, layers=layers, **kwargs)
        self.add(wms_layer)

