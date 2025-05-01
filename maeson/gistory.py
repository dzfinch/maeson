import json
from ipyleaflet import GeoJSON, TileLayer
import ipywidgets as widgets
import ipywidgets as widgets
from IPython.display import display
from ipyleaflet import Map, GeoJSON, TileLayer, ImageOverlay
from ipyleaflet import TileLayer, GeoJSON, ImageOverlay
import json


class Scene:
    def __init__(self, center, zoom, caption="", layers=None, title=None, order=1):
        self.center = center
        self.zoom = zoom
        self.caption = caption
        self.layers = layers or []
        self.title = title
        self.order = order


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
                layer = TileLayer(
                    url=layer_def["url"], name=layer_def.get("name", "Tiles")
                )

            elif layer_def["type"] == "image":
                try:
                    bounds = layer_def[
                        "bounds"
                    ]  # Must be [[south, west], [north, east]]
                    url = layer_def["url"]
                    layer = ImageOverlay(
                        url=url,
                        bounds=bounds,
                        name=layer_def.get("name", "Image Overlay"),
                    )
                except Exception as e:
                    print(f"Error loading image layer: {e}")
                    continue

            else:
                print(f"Unsupported layer type: {layer_def['type']}")
                continue

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


class SceneBuilder:
    def __init__(self, maeson_map):
        self.map = maeson_map
        self.layers = []

        # Widgets
        self.lat = widgets.FloatText(description="Lat", value=0)
        self.lon = widgets.FloatText(description="Lon", value=0)
        self.zoom = widgets.IntSlider(description="Zoom", min=1, max=18, value=2)
        self.caption = widgets.Text(description="Caption")

        # Scene metadata
        self.title = widgets.Text(description="Title", placeholder="My Scene Title")
        self.order_input = widgets.IntText(description="Order", value=1, min=1)

        # Chrono‐sort toggle
        self.sort_chrono = widgets.Checkbox(
            value=False, description="Sort Chronologically", indent=False
        )

        self.layer_type = widgets.Dropdown(
            options=[
                "tile",
                "geojson",
                "image",
                "raster",
                "wms",
                "video",
                "earthengine",
            ],
            description="Layer type",
        )
        self.layer_src = widgets.Text(description="URL/path")
        self.bounds = widgets.Text(
            description="Bounds (optional)",
            placeholder="[[S_min, W_min], [N_max, E_max]]",
        )

        self.add_layer_button = widgets.Button(description="➕ Add Layer")
        self.save_scene_button = widgets.Button(description="💾 Save Scene")

        self.output = widgets.Output()
        self.story = []

        self.add_layer_button.on_click(self.add_layer)
        self.save_scene_button.on_click(self.save_scene)

        self.scene_selector = widgets.Dropdown(
            options=[], description="Scenes", layout=widgets.Layout(width="300px")
        )
        self.scene_selector.observe(self._on_scene_select, names="value")
        self.preview_button = widgets.Button(description="Preview")
        self.update_button = widgets.Button(description="Update")
        self.delete_button = widgets.Button(description="Delete")
        self.preview_button.on_click(self.preview_scene)
        self.update_button.on_click(self.update_scene)
        self.delete_button.on_click(self.delete_scene)

        self.scene_controls = widgets.HBox(
            [
                self.scene_selector,
                self.preview_button,
                self.update_button,
                self.delete_button,
            ]
        )

        ## Log Controls
        self.log_history = []

        self.output = widgets.Output(
            layout=widgets.Layout(
                display="block",
                border="1px solid gray",
                padding="6px",
                max_height="150px",
                overflow="auto",
            )
        )
        self.toggle_log_button = widgets.ToggleButton(
            value=True,
            description="Hide Log",
            tooltip="Show/hide log console",
            icon="eye-slash",
        )
        self.toggle_log_button.observe(self.toggle_log_output, names="value")

        # Toggle log button
        self.toggle_log_button = widgets.ToggleButton(
            value=True,
            description="Hide Log",
            tooltip="Show/hide log console",
            icon="eye-slash",
        )

        self.toggle_log_button.observe(self.toggle_log_output, names="value")

        # Export button
        self.export_button = widgets.Button(
            description="Export Story",
            tooltip="Save all scenes to story.json",
            icon="save",
        )
        self.export_button.on_click(self.export_story)

        # Output box formatting
        self.output.layout = widgets.Layout(display="block")

        # User Interface Layout
        self.ui = widgets.VBox(
            [
                self.scene_controls,
                widgets.HBox([self.title, self.order_input]),
                widgets.HBox([self.lat, self.lon, self.zoom]),
                self.caption,
                widgets.HBox([self.layer_type, self.layer_src]),
                self.bounds,
                widgets.HBox(
                    [self.add_layer_button, self.save_scene_button, self.export_button]
                ),
                self.toggle_log_button,
                self.output,
            ]
        )

    def add_layer(self, _=None):
        layer_type = self.layer_type.value
        name = f"{layer_type.upper()}-{len(self.layers)}"
        path = self.layer_src.value
        self.layer_src = widgets.Text(description="URL/path")
        self.layer_src.observe(self.auto_detect_layer_type, names="value")

        if layer_type == "tile":
            self.map.add_tile(url=path, name=name)

        elif layer_type == "geojson":
            self.map.add_geojson(path, name=name)

        elif layer_type == "image":
            try:
                bounds = eval(self.bounds.value)
                self.map.add_image(path, bounds=bounds, name=name)
            except Exception as e:
                with self.output:
                    print(f"Error adding image layer: {e}")

        elif layer_type == "raster":
            self.map.add_raster(path, name=name)

        elif layer_type == "wms":
            self.map.add_wms_layer(url=path, name=name)

        elif layer_type == "video":
            self.map.add_video(path, name=name)

        elif layer_type == "earthengine":
            import ee

            try:
                ee_id = self.ee_id.value.strip()
                vis = json.loads(self.ee_vis.value) if self.ee_vis.value else {}
                self.map.add_earthengine(ee_id, vis_params=vis, name=name)
            except Exception as e:
                with self.output:
                    print(f"EE error: {e}")
        else:
            with self.output:
                print(f"Unsupported layer type: {layer_type}")
            return

        self.layers.append(
            {
                "type": layer_type,
                "path": path,
                "name": name,
                "bounds": eval(self.bounds.value) if layer_type == "image" else None,
            }
        )

        self.log(f"✅ Added {layer_type} layer: {name}")

    def detect_layer_type(path):
        path = path.lower()

        if (
            path.startswith("projects/")
            or path.count("/") >= 2
            and not path.startswith("http")
        ):
            return "earthengine"
        if all(k in path for k in ["{z}", "{x}", "{y}"]):
            return "tile"
        if "service=wms" in path or "request=getmap" in path:
            return "wms"
        if path.endswith(".geojson") or path.endswith(".json"):
            return "geojson"
        if path.endswith(".tif") or path.endswith(".tiff"):
            return "raster"
        if path.endswith(".png") or path.endswith(".jpg") or path.endswith(".jpeg"):
            return "image"
        if "amazonaws.com" in path and path.endswith(".tif"):
            return "raster"
        return "unknown"

    def save_scene(self, _=None):
        # 1) Read metadata
        scene_title = self.title.value.strip() or f"Scene {len(self.story)+1}"
        scene_order = self.order_input.value

        # 2) Build the Scene
        scene = Scene(
            center=(self.lat.value, self.lon.value),
            zoom=self.zoom.value,
            caption=self.caption.value,
            layers=self.layers.copy(),
            title=scene_title,
            order=scene_order,
        )

        # 3) Append & immediately sort by order
        self.story.append(scene)
        self.story.sort(key=lambda s: s.order)

        # 4) Refresh selector and clear form
        self.refresh_scene_list()
        self.layers.clear()
        self.title.value = ""
        self.order_input.value = len(self.story) + 1
        self.log(f"✅ Saved scene “{scene_title}” at position {scene_order}")

    def display(self):
        display(self.ui)

    def refresh_scene_list(self):
        options = []
        for i, s in enumerate(self.story):
            label = f"{s.order}: {s.title or f'Scene {i+1}'}"
            options.append((label, i))
        self.scene_selector.options = options

    def load_scene(self, _):
        i = self.scene_selector.index
        if i < 0:
            return
        scene = self.story[i]
        self.lat.value, self.lon.value = scene.center
        self.zoom.value = scene.zoom
        self.caption.value = scene.caption
        self.layers = scene.layers.copy()
        self.log(f"Loaded scene {i}.")

    def update_scene(self, _):
        i = self.scene_selector.index
        if i < 0:
            return
        scene = Scene(
            center=(self.lat.value, self.lon.value),
            zoom=self.zoom.value,
            caption=self.caption.value,
            layers=self.layers.copy(),
            title=self.title.value.strip() or f"Scene {i+1}",
            order=self.order_input.value,
        )
        self.story[i] = scene
        self.refresh_scene_list()
        self.log(f"Updated scene {i}.")

    def delete_scene(self, _):
        i = self.scene_selector.index
        if i < 0:
            return
        self.story.pop(i)
        self.refresh_scene_list()
        self.log(f"Deleted scene {i}.")

    def preview_scene(self, _=None):
        # Set map center and zoom
        self.map.center = (self.lat.value, self.lon.value)
        self.map.zoom = self.zoom.value

        # Clear existing non-base layers
        layers_to_remove = self.map.layers[1:]  # Preserve base layer
        for layer in layers_to_remove:
            self.map.remove_layer(layer)

        # Re-add layers defined in self.layers
        for layer_def in self.layers:
            layer_type = layer_def.get("type")
            path = layer_def.get("path") or layer_def.get("url")
            name = layer_def.get("name", f"{layer_type}-layer")

            if layer_type == "tile":
                layer = TileLayer(url=path, name=name)
                self.map.add_layer(layer)

            elif layer_type == "geojson":
                try:
                    with open(path) as f:
                        data = json.load(f)
                    layer = GeoJSON(data=data, name=name)
                    self.map.add_layer(layer)
                except Exception as e:
                    with self.output:
                        print(f"Error loading GeoJSON: {e}")

            elif layer_type == "image":
                try:
                    bounds = layer_def.get("bounds")
                    if not bounds:
                        bounds = eval(self.bounds.value)
                    layer = ImageOverlay(url=path, bounds=bounds, name=name)
                    self.map.add_layer(layer)
                except Exception as e:
                    with self.output:
                        print(f"Error loading ImageOverlay: {e}")

        self.log("Previewed scene on map.")

    def auto_detect_layer_type(self, change):
        path = change["new"]
        detected = self.detect_layer_type(path)
        if detected in [option for option, _ in self.layer_type.options]:
            self.layer_type.value = detected

    def log(self, message):
        """
        Append a message and then render:
        • full history if toggle is on
        • just the last message if toggle is off
        """
        # 1) store
        self.log_history.append(message)
        # 2) render based on mode
        if self.toggle_log_button.value:
            self._render_log()
        else:
            with self.output:
                self.output.clear_output(wait=True)
                print(self.log_history[-1])

    def _render_log(self):
        """
        Clear and print every message in log_history.
        """
        with self.output:
            self.output.clear_output(wait=True)
            for msg in self.log_history:
                print(msg)

    def toggle_log_output(self, change):
        """
        When the toggle flips:
        • if True → switch to full history view
        • if False → switch to most-recent-only view
        """
        if change["new"]:
            # now in “full history” mode
            self.toggle_log_button.description = "Show Recent"
            self.toggle_log_button.icon = "eye-slash"
            self._render_log()
        else:
            # now in “recent-only” mode
            self.toggle_log_button.description = "Show All"
            self.toggle_log_button.icon = "eye"
            with self.output:
                self.output.clear_output(wait=True)
                if self.log_history:
                    print(self.log_history[-1])

    def _on_scene_select(self, change):
        """Automatically load & preview whenever the dropdown changes."""
        if change["new"] is None:
            return
        # reuse your existing handlers
        self.load_scene(None)
        self.preview_scene(None)

    def export_story(self, _=None):
        """
        Dump all scenes to story.json and display a download link.
        """
        # Build serializable list of dicts
        out = []
        for s in self.story:
            out.append(
                {
                    "title": s.title,
                    "order": s.order,
                    "center": list(s.center),
                    "zoom": s.zoom,
                    "caption": s.caption,
                    "layers": s.layers,
                }
            )
        # Write to file
        fn = "story.json"
        with open(fn, "w") as f:
            json.dump(out, f, indent=2)
        # Log and show link
        self.log(f"✅ Story exported to {fn}")
        display(FileLink(fn))
