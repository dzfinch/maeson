import json
from ipyleaflet import GeoJSON, TileLayer
import ipywidgets as widgets
import ipywidgets as widgets
from IPython.display import display, FileLink
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
        # 1) Core state
        self.map = maeson_map
        self.layers = []  # holds layer definitions
        self.story = []  # holds saved Scene objects
        self.log_history = []  # for console logging

        # 2) Map view & metadata fields
        self.lat = widgets.FloatText(description="Lat", value=0)
        self.lon = widgets.FloatText(description="Lon", value=0)
        self.zoom = widgets.IntSlider(description="Zoom", min=1, max=18, value=2)
        self.caption = widgets.Text(description="Caption")

        self.title = widgets.Text(description="Title", placeholder="Scene Title")
        self.order_input = widgets.IntText(description="Order", value=1, min=1)
        self.sort_chrono = widgets.Checkbox(
            description="Sort Chronologically", value=False
        )

        # 3) Layer entry widgets
        self.layer_src = widgets.Text(description="URL/path")
        self.bounds = widgets.Text(
            description="Bounds (Optional)", placeholder="((S_min,W_min),(N_max,E_max))"
        )
        self.ee_id = widgets.Text(
            description="EE ID", placeholder="e.g. USGS/SRTMGL1_003"
        )
        self.ee_vis = widgets.Textarea(
            description="vis_params", placeholder='{"min":0}'
        )

        # 4) Scene list controls
        self.scene_selector = widgets.Dropdown(
            options=[], description="Scenes", layout=widgets.Layout(width="300px")
        )
        self.scene_selector.observe(self._on_scene_select, names="value")

        # 5) Action buttons: Preview, Save, Update, Delete, Export, Present
        self.preview_button = widgets.Button(description="Preview")
        self.save_scene_button = widgets.Button(description="💾 Save Scene")
        self.update_button = widgets.Button(description="Update")
        self.delete_button = widgets.Button(description="Delete")
        self.export_button = widgets.Button(description="Export Story", icon="save")
        self.present_button = widgets.Button(
            description="▶️ Present", button_style="success"
        )

        self.layer_src.layout = widgets.Layout(width="50%")
        self.caption.layout = widgets.Layout(width="30%")
        self.bounds.layout = widgets.Layout(width="20%")

        # wire up callbacks
        self.preview_button.on_click(self.preview_scene)
        self.save_scene_button.on_click(self.save_scene)
        self.update_button.on_click(self.update_scene)
        self.delete_button.on_click(self.delete_scene)
        self.export_button.on_click(self.export_story)
        self.present_button.on_click(self._enter_present_mode)
        self.edit_button = widgets.Button(
            description="✏️ Edit", tooltip="Return to editor", button_style="info"
        )
        self.edit_button.on_click(self._exit_present_mode)

        self.scene_controls = widgets.HBox(
            [
                self.scene_selector,
                self.save_scene_button,
                self.preview_button,
                self.update_button,
                self.delete_button,
                self.export_button,
                self.present_button,
            ],
            layout=widgets.Layout(gap="10px"),
        )

        # 6) Logging widgets
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
            value=True, description="Hide Log", icon="eye-slash"
        )
        self.toggle_log_button.observe(self.toggle_log_output, names="value")

        # 7) Build the authoring UI
        self.builder_ui = widgets.VBox(
            [
                self.scene_controls,
                widgets.HBox([self.title, self.order_input, self.sort_chrono]),
                widgets.HBox([self.lat, self.lon, self.zoom]),
                # COMPACT LAYER ENTRY ROW:
                widgets.HBox(
                    [self.layer_src, self.caption, self.bounds],
                    layout=widgets.Layout(gap="10px"),
                ),
                widgets.HBox([self.ee_id, self.ee_vis]),
                self.toggle_log_button,
                self.output,
            ]
        )

        self.main_container = widgets.VBox([self.builder_ui])

    def display(self):
        from IPython.display import display

        display(self.main_container)

    def add_layer(self, _=None, commit=True):
        path = self.layer_src.value.strip()
        lt = self.detect_layer_type(path)
        name = f"{lt.upper()}-{len(self.layers)}"

        if lt == "tile":
            self.map.add_tile(url=path, name=name)
        elif lt == "geojson":
            self.map.add_geojson(path=path, name=name)
        elif lt == "image":
            bounds = eval(self.bounds.value)
            self.map.add_image(url=path, bounds=bounds, name=name)
        elif lt == "raster":
            self.map.add_raster(path)
        elif lt == "wms":
            self.map.add_wms_layer(url=path, name=name)
        elif lt == "video":
            self.map.add_video(path, name=name)
        elif lt == "earthengine":
            ee_id = self.ee_id.value.strip()
            vis = json.loads(self.ee_vis.value or "{}")
            self.map.add_earthengine(ee_id=ee_id, vis_params=vis, name=name)
        else:
            return self.log(f"❌ Could not detect layer type for: {path}")

        # only append if commit
        if commit:
            self.layers.append(
                {
                    "type": lt,
                    "path": path,
                    "name": name,
                    "bounds": eval(self.bounds.value) if lt == "image" else None,
                    "ee_id": self.ee_id.value.strip() if lt == "earthengine" else None,
                    "vis_params": (
                        json.loads(self.ee_vis.value or "{}")
                        if lt == "earthengine"
                        else None
                    ),
                }
            )
        self.log(f"✅ Added {lt} layer: {name}")

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
        # 1) Read the raw URL/path
        src = self.layer_src.value.strip()
        if not src:
            return self.log("❌ No URL/path entered")

        # 2) Auto-detect the layer type
        lt = self.detect_layer_type(src)
        if lt == "unknown":
            return self.log(f"❌ Could not detect layer type for: {src}")

        # 3) Build a new layer_def
        name = f"{lt.upper()}-{len(self.layers)}"
        layer_def = {"type": lt, "path": src, "name": name}

        # 4) Add any extra params
        if lt == "image":
            # bounds is required for images
            try:
                layer_def["bounds"] = eval(self.bounds.value)
            except:
                return self.log("❌ Invalid bounds syntax")
        elif lt == "earthengine":
            # EE needs id + vis_params
            ee_id = self.ee_id.value.strip()
            try:
                vis = json.loads(self.ee_vis.value or "{}")
            except:
                return self.log("❌ Invalid EE vis_params JSON")
            layer_def["ee_id"] = ee_id
            layer_def["vis_params"] = vis

        # 5) Commit into your scene’s layer list
        self.layers.append(layer_def)

        # 6) Reset map view
        self.map.center = (self.lat.value, self.lon.value)
        self.map.zoom = self.zoom.value

        # 7) Clear existing overlays (keeping only base)
        for lyr in list(self.map.layers)[1:]:
            self.map.remove_layer(lyr)

        # 8) Replay _all_ saved layers via your helper
        for ld in self.layers:
            try:
                self._apply_layer_def(ld)
            except Exception as e:
                self.log(f"❌ Failed to apply {ld['name']}: {e}")

        # 9) Log success
        self.log(f"✅ Previewed scene with {len(self.layers)} layers (detected types)")

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

    def _load_def_into_ui(self, layer_def):
        """
        Copy a saved layer definition back into the builder widgets
        so that preview_scene can pick it up.
        """
        # URL or local path:
        self.layer_src.value = layer_def.get("path") or layer_def.get("url", "")

        # If it’s an image overlay, restore the bounds text:
        if layer_def["type"] == "image":
            self.bounds.value = repr(layer_def["bounds"])

        # If it’s an Earth Engine layer, restore ID and vis params:
        if layer_def["type"] == "earthengine":
            self.ee_id.value = layer_def.get("ee_id", "")
            self.ee_vis.value = json.dumps(layer_def.get("vis_params", {}))

    def _apply_layer_def(self, ld):
        """
        Load a single saved layer_def dict directly onto the map.
        """
        t = ld["type"]
        name = ld.get("name", None)

        self.log(f"→ Applying {t} layer: {name or ld['path']}")

        if t == "tile":
            self.map.add_tile(url=ld["path"], name=name)

        elif t == "geojson":
            self.map.add_geojson(path=ld["path"], name=name)

        elif t == "image":
            self.map.add_image(url=ld["path"], bounds=ld["bounds"], name=name)

        elif t == "raster":
            self.map.add_raster(ld["path"], name=name)

        elif t == "wms":
            self.map.add_wms_layer(url=ld["path"], name=name)

        elif t == "video":
            self.map.add_video(path=ld["path"], name=name)

        elif t == "earthengine":
            import ee

            vis = ld.get("vis_params", {})
            self.map.add_earthengine(ee_id=ld["ee_id"], vis_params=vis, name=name)

        else:
            self.log(f"❌ Unknown layer type: {t}")

    def _enter_present_mode(self, _=None):
        # build your StoryController as before
        scenes = sorted(self.story, key=lambda s: s.order)
        story_obj = Story(scenes)
        controller = StoryController(story_obj, self.map)

        # show the Edit button above the presenter interface
        self.main_container.children = [
            widgets.HBox(
                [self.edit_button], layout=widgets.Layout(justify_content="flex-end")
            ),
            controller.interface,
        ]

    def _exit_present_mode(self, _=None):
        # put back your authoring UI + Present button
        self.main_container.children = self._editor_children

    def _render_log(self):
        """
        Clear and print every message in log_history.
        """
        with self.output:
            self.output.clear_output(wait=True)
            for msg in self.log_history:
                print(msg)
