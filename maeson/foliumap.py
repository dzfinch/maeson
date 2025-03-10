import folium 

class Map(folium.Map):
    def __init__(self, center=[0,0], location=None, width='100%', height='100%', zoom = 2, **kwargs):
        super().__init__(location=location, width=width, height=height, zoom_start=zoom, **kwargs)
        self.width = width
        self.height = height   

        