import json
from ipyleaflet import GeoJSON, TileLayer
import ipywidgets as widgets


class Scene:
    def __init__(self, center, zoom, caption="", layers=None):
        """
        A single story scene with map view settings and data layers.
        """
        self.center = center  # Tuple (lat, lon)
        self.zoom = zoom      # Int zoom level
        self.caption = caption
        self.layers = layers or []  # List of dicts with 'type', 'path', etc.


class Story:
    def __init__(self, scenes):
        """
        A sequence of scenes forming a narrative.
        """
        self.scenes = scenes
        self.index = 0

    def current_scene(self):
        return self.scenes[self.index]

    def next_scene(self):
        if self.index < len(self.scenes) - 1:
            self.index += 1
        return self.current_scene()

    def previous_scene(self):
        if self.index > 0:
            self.index -= 1
        return self.current_scene()


class StoryController:
    def __init__(self, story, map_obj):
        """
        Connects a Story object to a map and widget-based UI.
        """
        self.story = story
        self.map = map_obj
        self.caption = widgets.Label()
        self.current_layers = []

        self.next_button = widgets.Button(description="Next")
        self.back_button = widgets.Button(description="Back")
        self.next_button.on_click(self.next_scene)
        self.back_button.on_click(self.previous_scene)

        self.controls = widgets.HBox([self.back_button, self.next_button])
        self.interface = widgets.VBox([self.map, self.caption, self.controls])

        self.update_scene()

    def update_scene(self):
        scene = self.story.current_scene()
        self.map.center = scene.center
        self.map.zoom = scene.zoom
        self.caption.value = scene.caption

        # Clear previous layers
        for layer in self.current_layers:
            self.map.remove_layer(layer)
        self.current_layers.clear()

        # Add new layers
        for layer_def in scene.layers:
            if layer_def["type"] == "geojson":
                with open(layer_def["path"]) as f:
                    data = json.load(f)
                layer = GeoJSON(data=data, name=layer_def.get("name", "GeoJSON"))
            elif layer_def["type"] == "tile":
                layer = TileLayer(url=layer_def["url"], name=layer_def.get("name", "Tiles"))
            else:
                continue  # unknown type

            self.map.add_layer(layer)
            self.current_layers.append(layer)

    def next_scene(self, _=None):
        self.story.next_scene()
        self.update_scene()

    def previous_scene(self, _=None):
        self.story.previous_scene()
        self.update_scene()

    def display(self):
        from IPython.display import display
        display(self.interface)
