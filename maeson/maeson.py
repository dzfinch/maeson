"""Main module."""

import ipyleaflet

class Map(ipyleaflet.Map):
    def __init__(self, center=[20,0], zoom=2, **kwargs):
        super(Map, self).__init__(center=center, zoom=zoom, **kwargs)
        
    def add_basemap(self, basemap='Esri.WorldImagery'):
        
        url = eval(f'ipyleaflet.basemaps.{basemap}').build_url()
        basemap_layer = ipyleaflet.TileLayer(url=url, name=basemap)
        self.add(basemap_layer)