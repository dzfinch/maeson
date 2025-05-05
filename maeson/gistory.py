import json
import ipywidgets as widgets
import traceback
from IPython.display import display, FileLink
from ipyleaflet import (
    Map,
    GeoJSON,
    TileLayer,
    ImageOverlay,
    TileLayer,
    GeoJSON,
    ImageOverlay,
    VideoOverlay,
)
from ipywidgets import (
    Layout,
    HBox,
    VBox,
    Button,
    Label,
    Text,
    IntSlider,
    FloatText,
    Dropdown,
    Output,
    ToggleButton,
    jslink,
    HTML,
    Textarea,
)


class Scene:
    def __init__(
        self,
        center,
        zoom,
        caption="",
        layers=None,
        title=None,
        order=1,
        basemap=None,
        custom_code: str = "",
    ):
        self.center = center
        self.zoom = zoom
        self.caption = caption
        self.layers = layers or []
        self.title = title
        self.order = order
        self.basemap = basemap
        self.custom_code = custom_code  # ← new field


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

        if getattr(scene, "custom_code", "").strip():
            try:
                exec(
                    scene.custom_code,
                    {},  # no builtins unless you want
                    {"map": self.map},  # give them `map`
                )
            except Exception as e:
                # swallow or log; you could surface this in the UI
                print(f"Error in scene code: {e}")

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
        # Core state
        self.map = maeson_map
        self.layers = []  # holds layer definitions
        self.story = []  # holds saved Scene objects
        self.log_history = []  # for console logging

        # Map view & metadata fields
        self.lat = widgets.FloatText(description="Lat", value=0)
        self.lon = widgets.FloatText(description="Lon", value=0)
        self.zoom = widgets.IntSlider(description="Zoom", min=1, max=18, value=2)
        self.caption = widgets.Text(description="Caption")

        # Zoom slider directly to map.zoom
        jslink((self.zoom, "value"), (self.map, "zoom"))

        # For center, we’ll do observers:
        self.lat.observe(
            lambda change: self._update_map_center(lat=change["new"]), names="value"
        )
        self.lon.observe(
            lambda change: self._update_map_center(lon=change["new"]), names="value"
        )

        # Link map to widgets

        self.map.observe(self._on_map_center_change, names="center")
        self.map.observe(self._on_map_zoom_change, names="zoom")

        self.title = widgets.Text(description="Title", placeholder="Scene Title")
        self.order_input = widgets.IntText(description="Order", value=1, min=1)
        self.sort_chrono = widgets.Checkbox(
            description="Sort Chronologically", value=False
        )

        # Layer entry widgets
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

        # Scene list controls
        self.scene_selector = widgets.Dropdown(
            options=[], description="Scenes", layout=widgets.Layout(width="300px")
        )
        self.scene_selector.observe(self._on_scene_select, names="value")

        # Action buttons: Preview, Save, Update, Delete, Export, Present
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

        # Logging widgets
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

        # Custom code editor widgets
        self.custom_code = widgets.Textarea(
            value=(
                "# Enter Python code here using the variable `map`.\n"
                "# e.g. map.add_heatmap(data='points.csv', latitude='lat', longitude='lon')"
            ),
            placeholder="Write Python snippet…",
            layout=Layout(width="100%", height="150px"),
        )
        self.run_code_button = widgets.Button(
            description="Run Code",
            button_style="info",
            tooltip="Execute the code above",
        )
        self.run_code_button.on_click(self._run_custom_code)
        self.code_container = VBox(
            [
                HTML("<b>Custom Python:</b>"),
                self.custom_code,
                self.run_code_button,
            ],
            layout=Layout(display="block", gap="6px"),
        )

        # Toggle buttons
        self.toggle_log_button = ToggleButton(
            value=True, description="Hide Log", icon="list", tooltip="Show/hide log"
        )
        self.toggle_log_button.observe(self.toggle_log_output, names="value")
        self.toggle_code_button = ToggleButton(
            value=True,
            description="Hide Code",
            icon="code",
            tooltip="Show/hide Python shell",
        )
        self.toggle_code_button.observe(self._toggle_code, names="value")

        self.toggle_row = HBox(
            [self.toggle_log_button, self.toggle_code_button], layout=Layout(gap="10px")
        )

        # Map widget
        map_widget = getattr(self.map, "map", self.map)

        # Authoring UI
        self.builder_ui = VBox(
            [
                map_widget,
                self.scene_controls,
                HBox([self.title, self.order_input, self.sort_chrono]),
                HBox([self.lat, self.lon, self.zoom]),
                HBox(
                    [self.layer_src, self.caption, self.bounds],
                    layout=Layout(gap="10px"),
                ),
                self.toggle_row,  # both toggles here
                self.output,
                self.code_container,  # code editor below
            ],
            layout=Layout(gap="10px"),
        )

        # 7) Main container
        self.main_container = VBox([self.builder_ui])

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

    def save_scene(self, _=None):
        # 1) Read metadata
        scene_title = self.title.value.strip() or f"Scene {len(self.story)+1}"
        scene_order = self.order_input.value
        code = self.custom_code.value or ""

        # 2) Prepare the layer list (copy of what’s been added so far)
        layers = self.layers.copy()

        # 3) If the user has drawn any ROIs, include them as GeoJSON
        if hasattr(self, "drawn_features") and self.drawn_features:
            layers.append(
                {
                    "type": "geojson",
                    "data": {
                        "type": "FeatureCollection",
                        "features": list(self.drawn_features),
                    },
                    "name": "ROIs",
                }
            )

        # 4) Build the Scene, passing that 'layers' var
        scene = Scene(
            center=(self.lat.value, self.lon.value),
            zoom=self.zoom.value,
            caption=self.caption.value,
            layers=layers,
            title=scene_title,
            order=scene_order,
            basemap=getattr(self, "basemap_dropdown", None)
            and self.basemap_dropdown.value,
            custom_code=code,
        )

        # 5) Append & sort
        self.story.append(scene)
        self.story.sort(key=lambda s: s.order)

        # 6) Refresh UI & clear state
        self.refresh_scene_list()
        self.layers.clear()
        if hasattr(self, "drawn_features"):
            self.drawn_features.clear()
        self.title.value = ""
        self.order_input.value = len(self.story) + 1
        self.custom_code.value = ""

        # 7) Log success
        self.log(f"✅ Saved scene “{scene_title}” with {len(layers)} layer(s)")

    def refresh_scene_list(self):
        options = []
        for i, s in enumerate(self.story):
            label = f"{s.order}: {s.title or f'Scene {i+1}'}"
            options.append((label, i))
        self.scene_selector.options = options

    def load_scene(self, _=None):
        # 1) Find the selected scene
        i = self.scene_selector.index
        if i < 0:
            return

        scene = self.story[i]

        # 2) Populate the form fields
        self.lat.value, self.lon.value = scene.center
        self.zoom.value = scene.zoom
        self.caption.value = scene.caption
        self.title.value = scene.title or ""
        self.order_input.value = scene.order
        self.custom_code.value = scene.custom_code

        # 3) Reset our internal layer list to this scene’s layers
        #    (so we don’t accumulate layers from previous edits)
        self.layers = [ld.copy() for ld in scene.layers]

        # 4) Clear existing non‑base layers from the map
        for lyr in list(self.map.layers)[1:]:
            self.map.remove_layer(lyr)

        # 5) Replay just this scene’s layers onto the map
        for ld in self.layers:
            try:
                self._apply_layer_def(ld)
            except Exception as e:
                self.log(f"❌ Failed to apply {ld.get('name')}: {e}")

        # 6) Feedback
        self.log(f"Loaded scene {i}: “{scene.title}”")

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
        # 1) Read & validate the source
        src = self.layer_src.value.strip()
        if not src:
            return self.log("❌ No URL/path entered")

        # 2) Let detect_layer_type tell us what it is
        lt = detect_layer_type(src)
        if lt == "unknown":
            return self.log(f"❌ Could not detect layer type for: {src}")

        # 3) Build the new layer_def
        name = f"{lt.upper()}-{len(self.layers)}"
        layer_def = {"type": lt, "name": name}

        # geojson & raster need a path, others use url
        if lt in ("geojson", "raster"):
            layer_def["path"] = src
        else:
            layer_def["url"] = src

        # 4) Extras: bounds for images, EE params for earthengine
        if lt == "image":
            try:
                layer_def["bounds"] = eval(self.bounds.value)
            except:
                return self.log("❌ Invalid bounds syntax")
        elif lt == "earthengine":
            ee_id = self.ee_id.value.strip()
            try:
                vis = json.loads(self.ee_vis.value or "{}")
            except:
                return self.log("❌ Invalid EE vis_params JSON")
            layer_def["ee_id"] = ee_id
            layer_def["vis_params"] = vis
        elif lt == "video":
            # require bounds
            try:
                layer_def["bounds"] = eval(self.bounds.value)
            except:
                return self.log("❌ Invalid bounds for video")
        elif lt == "tile":
            # require bounds
            try:
                layer_def["bounds"] = eval(self.bounds.value)
            except:
                return self.log("❌ Invalid bounds for tile")

        # 5) Commit into the scene’s layer list
        self.layers.append(layer_def)

        # 6) Reset the map view
        self.map.center = (self.lat.value, self.lon.value)
        self.map.zoom = self.zoom.value

        # 7) Clear existing overlays (keep only base)
        for lyr in list(self.map.layers)[1:]:
            self.map.remove_layer(lyr)

        # 8) Replay all saved layers via your helper
        for ld in self.layers:
            try:
                self._apply_layer_def(ld)
            except Exception as e:
                self.log(f"❌ Failed to apply {ld['name']}: {e}")

        # 9) Final feedback
        self.log(f"✅ Previewed scene with {len(self.layers)} layers")

    def log(self, message):
        """
        Append a message and then render:
        • full history if toggle is ON
        • just the last message if toggle is OFF
        """
        self.log_history.append(message)
        # Always render (we’re never truly hiding)
        if self.toggle_log_button.value:
            self._render_log()
        else:
            with self.output:
                self.output.clear_output(wait=True)
                print(self.log_history[-1])

    def toggle_log_output(self, change):
        """
        Toggle between full‐history view (True) and
        most‐recent‐only view (False).
        """
        # Always keep the console visible
        self.output.layout.display = "block"

        if change["new"]:
            # Now in “full history” mode
            self.toggle_log_button.description = "Show Recent"
            self.toggle_log_button.icon = "eye-slash"
            self._render_log()
        else:
            # Now in “recent only” mode
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
        if ld["type"] == "geojson":
            if "data" in ld:
                layer = GeoJSON(data=ld["data"], name=ld.get("name"))
            else:
                layer = GeoJSON(data=open(ld["path"]).read(), name=ld.get("name"))
            self.map.add_layer(layer)
        elif t == "image":
            self.map.add_image(url=ld["path"], bounds=ld["bounds"], name=name)
        elif t == "raster":
            self.map.add_raster(ld["path"], name=name)
        elif t == "wms":
            self.map.add_wms_layer(url=ld["path"], name=name)
        elif t == "video":
            self.map.add_video(ld["path"], name=name)
        elif t == "earthengine":
            import ee

            vis = ld.get("vis_params", {})
            self.map.add_earthengine(ee_id=ld["ee_id"], vis_params=vis, name=name)
        else:
            self.log(f"❌ Unknown layer type: {t}")

    def _enter_present_mode(self, _=None):
        # 1) Build the StoryController
        scenes = sorted(self.story, key=lambda s: s.order)
        story_obj = Story(scenes)
        teller = StoryController(story_obj, self.map)

        # 2) Replace main_container with [edit_button row, presenter]
        header = widgets.HBox(
            [self.edit_button], layout=widgets.Layout(justify_content="flex-end")
        )
        self.main_container.children = [header, teller.interface]

    def _exit_present_mode(self, _=None):
        # Simply restore the builder UI as the sole child
        self.main_container.children = [self.builder_ui]

    def _render_log(self):
        """
        Clear and print every message in log_history.
        """
        with self.output:
            self.output.clear_output(wait=True)
            for msg in self.log_history:
                print(msg)

    def _update_map_center(self, lat=None, lon=None):
        """Re‑center map when one of the text fields changes."""
        old_lat, old_lon = self.map.center
        new_lat = lat if lat is not None else old_lat
        new_lon = lon if lon is not None else old_lon
        # This will in turn fire the observer below to update the other widget
        self.map.center = (new_lat, new_lon)

    def _on_map_center_change(self, change):
        """Update lat/lon fields when the map is panned."""
        lat, lon = change["new"]
        # avoid feedback loops by only setting if really different
        if self.lat.value != lat:
            self.lat.value = lat
        if self.lon.value != lon:
            self.lon.value = lon

    def _on_map_zoom_change(self, change):
        """Update zoom slider when the map is zoomed."""
        z = change["new"]
        if self.zoom.value != z:
            self.zoom.value = z

    def _run_custom_code(self, _):
        """
        Execute user‑entered Python with `map` in scope,
        and log success or error.
        """
        code = self.custom_code.value
        local_ns = {"map": self.map}
        try:
            exec(code, {}, local_ns)
            self.log("✅ Custom code executed successfully")
        except Exception as e:
            # show only the last line of the traceback
            import traceback

            tb = traceback.format_exc().splitlines()[-1]
            self.log(f"❌ Error: {tb}")

    def _toggle_code(self, change):
        if change["new"]:
            self.toggle_code_button.description = "Hide Code"
            self.code_container.layout.display = "block"
        else:
            self.toggle_code_button.description = "Show Code"
            self.code_container.layout.display = "none"


def detect_layer_type(path: str) -> str:
    p = path.lower()
    if p.startswith("projects/") or (p.count("/") >= 2 and not p.startswith("http")):
        return "earthengine"
    if "{z}" in p and "{x}" in p and "{y}" in p:
        return "tile"
    if p.endswith((".tms", ".wms", ".cgi")):
        return "wms"
    if p.endswith((".geojson", ".json")):
        return "geojson"
    if p.endswith((".tif", ".tiff")):
        return "raster"
    if p.endswith((".png", ".jpg", ".jpeg")):
        return "image"
    if p.endswith((".mp4", ".webm", ".ogg")):
        return "video"
    return "unknown"
