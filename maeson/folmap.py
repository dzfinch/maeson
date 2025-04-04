"""Folium Module"""

import folium
from folium import plugins


class Map(folium.Map):
    """
    class that extends folium.Map.
    This class is used to create a map with additional functionalities.
    """

    def __init__(self, center=(0, 0), zoom=2, **kwargs):
        super().__init__(location=center, zoom_start=zoom, **kwargs)

    def add_basemap(self, name: str, **kwargs):
        """
        Add a basemap to the map using Esri maps.
        Args:
            name (str): Name of the basemap.
            **kwargs: Additional arguments to pass to the folium.TileLayer.
        """
        basemaps = {
            "Road": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "Topo": "https://server.arcgisonline.com/ArcGIS/rest/services/Topographic/MapServer/tile/{z}/{y}/{x}",
            "Terrain": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
        }
        if name in basemaps:
            folium.TileLayer(
                tiles=basemaps[name],
                attr='&copy; <a href="http://www.esri.com/">Esri</a>',
                **kwargs,
            ).add_to(self)
        else:
            raise ValueError(f"Basemap '{name}' not found.")

    def add_geojson(self, data, name="GeoJSON Layer", **kwargs):
        """Adds a GeoJSON layer to the map.

        Args:
            data (str or dict): The GeoJSON data. Can be a file path (str) or a dictionary.
            name (str): Name of the layer to display in the LayerControl. Defaults to "GeoJSON Layer".
            **kwargs: Additional keyword arguments for the folium.GeoJson layer.
        """
        import geopandas as gpd

        if isinstance(data, str):
            gdf = gpd.read_file(data)
            geojson = gdf.__geo_interface__
        elif isinstance(data, dict):
            geojson = data

        geojson_layer = folium.GeoJson(data=geojson, name=name, **kwargs)
        geojson_layer.add_to(self)

    def add_shp(self, data, **kwargs):
        """Adds a shapefile to the map.

        Args:
            data (str): The file path to the shapefile.
            **kwargs: Additional keyword arguments for the GeoJSON layer.
        """
        import geopandas as gpd

        gdf = gpd.read_file(data)
        gdf = gdf.to_crs(epsg=4326)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, **kwargs)

    def add_gdf(self, gdf, name="GDF Layer", **kwargs):
        """Adds a GeoDataFrame to the map.

        Args:
            gdf (geopandas.GeoDataFrame): The GeoDataFrame to add.
            **kwargs: Additional keyword arguments for the GeoJSON layer.
        """
        gdf = gdf.to_crs(epsg=4326)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, name, **kwargs)

    def add_vector(self, data, name="Vector Layer", **kwargs):
        """Adds vector data to the map.

        Args:
            data (str, geopandas.GeoDataFrame, or dict): The vector data. Can be a file path, GeoDataFrame, or GeoJSON dictionary.
            name (str): Name of the layer to display in the LayerControl. Defaults to "Vector Layer".
            **kwargs: Additional keyword arguments for the GeoJSON layer.

        Raises:
            ValueError: If the data type is invalid.
        """
        import geopandas as gpd

        if isinstance(data, str):
            gdf = gpd.read_file(data)
            self.add_gdf(gdf, name=name, **kwargs)
        elif isinstance(data, gpd.GeoDataFrame):
            self.add_gdf(data, name=name, **kwargs)
        elif isinstance(data, dict):
            self.add_geojson(data, name=name, **kwargs)
        else:
            raise ValueError("Invalid data type")

    def add_layer_control(self):
        """Adds a layer control widget to the map."""
        folium.LayerControl().add_to(self)

    def add_raster(self, data: str, layer_name: str, **kwargs):
        """
        Add a raster layer to the map.
        Args:
            data (str): Path to the raster file.
            layer_name (str): Name of the layer.
            **kwargs: Additional arguments to pass to the folium.ImageOverlay.
        """
        folium.ImageOverlay(data, name=layer_name, **kwargs).add_to(self)

    def add_split_map(self, left="openstreetmap", right="cartodbpositron", **kwargs):

        layer_right = folium.TileLayer(left, **kwargs)
        layer_left = folium.TileLayer(right, **kwargs)

        sbs = folium.plugins.SideBySideLayers(
            layer_left=layer_left, layer_right=layer_right
        )

        # Allow for raster TIFs to be added to left or right
        if isinstance(left, str) and left.endswith(".tif"):
            layer_left = folium.ImageOverlay(left, **kwargs)
        if isinstance(right, str) and right.endswith(".tif"):
            layer_right = folium.ImageOverlay(right, **kwargs)

        layer_left.add_to(self)
        layer_right.add_to(self)
        sbs.add_to(self)
