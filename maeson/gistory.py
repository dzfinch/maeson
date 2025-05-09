import json
import ipywidgets as widgets
import traceback
from IPython.display import display, FileLink
import copy, json, asyncio
from ipyleaflet import (
    Map,
    GeoJSON,
    TileLayer,
    ImageOverlay,
    TileLayer,
    GeoJSON,
    ImageOverlay,
    VideoOverlay,
    DrawControl,
    Rectangle,
)
from ipywidgets import (
    HBox,
    VBox,
    Button,
    ToggleButton,
    Textarea,
    FloatText,
    FloatSlider,
    IntSlider,
    Text,
    IntText,
    Checkbox,
    Output,
    Layout,
    HTML,
    jslink,
)


class Scene:
    def __init__(
        self,
        center,
        zoom,
        layers=None,
        title=None,
        order=1,
        basemap=None,
        custom_code: str = "",
    ):
        self.center = center
        self.zoom = zoom
        self.layers = layers or []
        self.title = title
        self.order = order
        self.basemap = basemap
        self.custom_code = custom_code


class Story:
    def __init__(self, scenes):
        """
        A sequence of scenes forming a narrative.
        """
        self.scenes = scenes
        self.index = 0

    def _current_scene(self):
        return self.scenes[self.index]

    def _next_scene(self):
        if self.index < len(self.scenes) - 1:
            self.index += 1
        return self._current_scene()

    def _previous_scene(self):
        if self.index > 0:
            self.index -= 1
        return self._current_scene()


class StoryController:
    def __init__(self, story, map_obj: Map):
        """
        Connects a Story object to a map and widget-based UI.
        """
        self.story = story
        self.map = map_obj
        self.current_layers = []

        self.next_button = widgets.Button(description="Next")
        self.back_button = widgets.Button(description="Back")
        self.next_button.on_click(self._next_scene)
        self.back_button.on_click(self._previous_scene)

        self.controls = widgets.HBox([self.back_button, self.next_button])
        self.interface = widgets.VBox([self.map, self.controls])

        self._update_scene()

    def _update_scene(self):
        scene = self.story._current_scene()
        # 1) Reset view
        self.map.center = scene.center
        self.map.zoom = scene.zoom

        # 2) Clear out any previous overlays
        self._clear_overlays()
        self.current_layers.clear()

        # 3) Re‑add each layer using your Map methods
        for ld in scene.layers:
            t = ld["type"]
            name = ld.get("name")

            try:
                if t == "geojson":
                    if "data" in ld:
                        layer = GeoJSON(data=ld["data"], name=name)
                        self.map.add_layer(layer)
                    else:
                        layer = self.map.add_geojson(ld["path"], name=name)

                elif t == "tile":
                    layer = self.map.add_tile(url=ld["url"], name=name)

                elif t == "image":
                    layer = self.map.add_image(
                        url=ld["path"],
                        bounds=tuple(tuple(c) for c in ld["bounds"]),
                        name=name,
                    )

                elif t == "video":
                    layer = self.map.add_video(
                        url=ld["path"],
                        bounds=tuple(tuple(c) for c in ld["bounds"]),
                        name=name,
                    )

                elif t == "raster":
                    layer = self.map.add_raster(
                        ld["path"], name=name, zoom_to_layer=False
                    )

                elif t == "wms":
                    layer = self.map.add_wms_layer(url=ld["url"], name=name)

                elif t == "earthengine":
                    # your Map.add_earthengine takes ee_object + vis_params
                    layer = self.map.add_earthengine(
                        ee_object=ld["ee_id"],
                        vis_params=ld.get("vis_params", {}),
                        name=name,
                    )

                else:
                    print(f"Unsupported layer type: {t}")
                    continue

                self.current_layers.append(layer)

            except Exception as e:
                print(f"❌ Failed to add {t} layer “{name}”: {e}")

        # 4) Finally, run any custom code
        if scene.custom_code.strip():
            try:
                exec(scene.custom_code, {}, {"map": self.map})
            except Exception as e:
                print(f"⚠️ Error in scene code: {e}")

    def _clear_overlays(self):
        # 1) Remove map overlays
        for lyr in list(self.map.layers)[1:]:
            self.map.remove_layer(lyr)

    def _next_scene(self, _=None):
        self.story._next_scene()
        self._update_scene()

    def _previous_scene(self, _=None):
        self.story._previous_scene()
        self._update_scene()

    def display(self):
        from IPython.display import display

        display(self.interface)


class SceneBuilder:
    def __init__(self, maeson_map: Map):
        # Core state
        self.map = maeson_map
        self.layers = []
        self.story = []
        self.log_history = []
        self._active_overlay = None

        # Wire map events
        self._initialize_map_observers()

        # Build out all widget groups
        self._initialize_map_controls()
        self._initialize_layer_controls()
        self._initialize_scene_controls()
        self._initialize_logging_widgets()
        self._initialize_code_editor()
        self._initialize_toggle_buttons()

        # Assemble final UI
        self._build_main_ui()

    def display(self):
        display(self.main_container)

    def _initialize_map_observers(self):
        """Watch map center, zoom, and layers for two‑way sync & auto‑zoom."""
        self.map.observe(self._on_map_center_change, names="center")
        self.map.observe(self._on_map_zoom_change, names="zoom")
        self.map.observe(self._on_map_layers_change, names="layers")

    def _initialize_map_controls(self):
        """Latitude/Longitude/Zoom widget row + Zoom‑to‑layers button."""
        self.lat = FloatText(description="Lat", value=0)
        self.lon = FloatText(description="Lon", value=0)
        self.zoom = IntSlider(description="Zoom", min=1, max=18, value=2)

        # Sync zoom slider ←→ map
        jslink((self.zoom, "value"), (self.map, "zoom"))
        # Sync textboxes → map
        self.lat.observe(lambda c: self._update_map_center(lat=c["new"]), names="value")
        self.lon.observe(lambda c: self._update_map_center(lon=c["new"]), names="value")

        # Zoom‑to‑all‑layers button
        self.zoom_to_layers_button = Button(
            description="",
            icon="arrows-alt",
            tooltip="Zoom to all layers",
            layout=Layout(width="32px"),
        )
        self.zoom_to_layers_button.on_click(self._zoom_to_layers)

        self.coords_controls = HBox(
            [self.lat, self.lon, self.zoom, self.zoom_to_layers_button],
            layout=Layout(gap="6px"),
        )

    def _initialize_layer_controls(self):
        """Initialize widgets for layer management, including live‐bounds sliders."""
        # 1) URL / path entry
        self.layer_src = Text(description="URL/path")

        self._clear_layers_button = Button(
            description="Clear Layers",
            button_style="danger",
            tooltip="Remove all added layers from map",
        )
        self._clear_layers_button.on_click(self._clear_layers)

        # 2) Hidden text store (so any old eval(self.bounds.value) still works)
        self.bounds = Text(layout=Layout(display="none"))

        # 3) Four sliders for South, West, North, East
        self.bound_sliders = {
            "south": FloatSlider(min=-90, max=90, step=0.1, description="South"),
            "west": FloatSlider(min=-180, max=180, step=0.1, description="West"),
            "north": FloatSlider(min=-90, max=90, step=0.1, description="North"),
            "east": FloatSlider(min=-180, max=180, step=0.1, description="East"),
        }
        # Set default values to -30, -30, 30, 30
        self.bound_sliders["south"].value = -30
        self.bound_sliders["west"].value = -30
        self.bound_sliders["north"].value = 30
        self.bound_sliders["east"].value = 30

        # 4) Pack sliders into a hidden VBox
        self.bounds_container = VBox(
            [
                HBox([self.bound_sliders["south"], self.bound_sliders["west"]]),
                HBox([self.bound_sliders["north"], self.bound_sliders["east"]]),
            ],
            layout=Layout(display="none", gap="6px"),
        )

        # 5) Whenever a slider moves, sync it into the hidden .bounds.value
        def _sync_bounds_to_text(change):
            b = (
                (self.bound_sliders["south"].value, self.bound_sliders["west"].value),
                (self.bound_sliders["north"].value, self.bound_sliders["east"].value),
            )
            self.bounds.value = repr(b)

        for slider in self.bound_sliders.values():
            slider.observe(_sync_bounds_to_text, names="value")
            slider.observe(self._update_overlay_bounds, names="value")

        # 6) Show/hide sliders based on URL type
        def _on_src_change(change):
            url = change["new"].strip().lower()
            is_img = url.endswith((".png", ".jpg", ".jpeg", ".gif", ".tiff"))
            is_vid = url.endswith((".mp4", ".webm"))
            if is_img or is_vid:
                self.bounds_container.layout.display = "block"
            else:
                self.bounds_container.layout.display = "none"

        self.layer_src.observe(_on_src_change, names="value")

        # 7) Finally, assemble the layer‐controls panel
        self.layer_controls = VBox(
            [
                HBox(
                    [self.layer_src, self._clear_layers_button],
                    layout=Layout(gap="6px"),
                ),
                self.bounds_container,
                self.bounds,
            ],
            layout=Layout(gap="6px"),
        )

    def _initialize_scene_controls(self):
        """Title, order, sort toggle and action buttons (Save, Preview, etc.)."""
        self.title = Text(description="Title", placeholder="Scene Title")
        self.order_input = IntText(description="Order", value=1, min=1)
        self.sort_chrono = Checkbox(description="Sort Chrono", value=False)
        self.org_controls = HBox([self.title, self.order_input, self.sort_chrono])

        # Dropdown of saved scenes
        self.scene_selector = widgets.Dropdown(
            options=[], description="Scenes", layout=Layout(width="250px")
        )
        self.scene_selector.observe(self._on_scene_select, names="value")

        # Action buttons
        self.save_button = self._create_button(
            "💾 Save", "primary", self._save_scene, tooltip="Save current scene"
        )
        self.preview_button = self._create_button(
            "🔍 Preview",
            "info",
            self._preview_scene,
            tooltip="Visualize scene parameters",
        )
        self.copy_button = self._create_button(
            "📋 Copy", "warning", self._copy_scene, tooltip="Duplicate current scene"
        )
        self.delete_button = self._create_button(
            "🗑️ Delete", "danger", self._delete_scene, tooltip="Delete current scene"
        )
        self.export_button = self._create_button(
            "📤 Export",
            "warning",
            self._export_story,
            tooltip="Export Scenes as Story JSON",
        )
        self.present_button = self._create_button(
            "▶️ Present",
            "success",
            self._enter_present_mode,
            tooltip="Switch to SceneController",
        )
        self.edit_button = self._create_button(
            "✏️ Edit",
            "warning",
            self._exit_present_mode,
            tooltip="Return to SceneBuilder",
        )
        self.export_button.style.button_color = "#FFD700"
        self.export_button.add_class("export-btn")

        self.scene_controls = HBox(
            [
                self.scene_selector,
                self.save_button,
                self.preview_button,
                self.copy_button,
                self.delete_button,
                self.export_button,
                self.present_button,
            ],
            layout=Layout(gap="8px"),
        )

    def _initialize_logging_widgets(self):
        """Output console + toggle button for log visibility."""
        self.output = Output(
            layout=Layout(
                border="1px solid gray",
                padding="6px",
                max_height="150px",
                overflow="auto",
            )
        )
        self.toggle_log_button = ToggleButton(
            value=False,
            description="Show Log",
            icon="eye-slash",
            tooltip="Show/hide log console",
        )
        self.toggle_log_button.observe(self._toggle_log_output, names="value")
        self.output.layout.display = "none"  # start hidden

    def _initialize_code_editor(self):
        """Textarea + Run button for custom Python snippets."""
        self.custom_code = Textarea(
            value=(
                """import ee
ee.Initialize()\n
# Example: add an Earth Engine image to the map
# map.add_earthengine(
#    ee_object=img,
#    vis_params={"min":0,"max":3000},
#    name="My EE Layer"
#)
"""
            ),
            layout=Layout(width="100%", height="150px"),
        )
        self.code_container = VBox(
            [HTML("<b>Custom Python:</b>"), self.custom_code],
            layout=Layout(display="none", gap="6px"),
        )

    def _initialize_toggle_buttons(self):
        """Bundle Log + Code toggles into one row."""
        self.toggle_code_button = ToggleButton(
            value=False,
            description="Show Code",
            icon="code",
            tooltip="Show/hide Python shell",
        )
        self.toggle_code_button.observe(self._toggle_code, names="value")
        self.toggle_row = HBox(
            [self.toggle_log_button, self.toggle_code_button], layout=Layout(gap="6px")
        )

    def _build_main_ui(self):
        """Assemble map + controls + toggles + console + code editor."""
        map_widget = getattr(self.map, "map", self.map)
        self.builder_ui = VBox(
            [
                map_widget,
                self.scene_controls,
                self.org_controls,
                self.coords_controls,
                self.layer_controls,
                self.toggle_row,
                self.output,
                self.code_container,
            ],
            layout=Layout(gap="10px"),
        )
        self.main_container = VBox([self.builder_ui])

    def _create_button(self, desc, style, callback, tooltip=None):
        """Helper: make a bold‑font Button with a style and handler."""
        btn = Button(description=desc, button_style=style, tooltip=tooltip)
        btn.style.font_weight = "bold"
        btn.on_click(callback)
        return btn

    def _add_layer(self, _=None, commit=True):
        path = self.layer_src.value.strip()
        lt = detect_layer_type(path)
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
            return self._log(f"❌ Could not detect layer type for: {path}")

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
        self._log(f"✅ Added {lt} layer: {name}")

    def _save_scene(self, _=None):
        # 1) Read metadata
        scene_title = self.title.value.strip() or f"Scene {len(self.story)+1}"
        scene_order = self.order_input.value
        code = self.custom_code.value or ""

        # 2) Prepare layer list, including drawn ROIs if any
        layers = self.layers.copy()
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

        # 3) Build a new Scene object
        new_scene = Scene(
            center=(self.lat.value, self.lon.value),
            zoom=self.zoom.value,
            layers=layers,
            title=scene_title,
            order=scene_order,
            basemap=getattr(self, "basemap_dropdown", None)
            and self.basemap_dropdown.value,
            custom_code=code,
        )

        # 4) Update in place if title exists, else append
        for idx, sc in enumerate(self.story):
            if sc.title == scene_title:
                self.story[idx] = new_scene
                action = "Updated"
                break
        else:
            self.story.append(new_scene)
            action = "Saved"

        # 5) Sort & refresh UI
        self.story.sort(key=lambda s: s.order)
        self._refresh_scene_list()

        # 6) Clear the map overlays (keep only base)
        for lyr in list(self.map.layers)[1:]:
            self.map.remove_layer(lyr)

        # 7) Clear internal state and form fields
        self.layers.clear()
        if hasattr(self, "drawn_features"):
            self.drawn_features.clear()

        self.title.value = ""
        self.order_input.value = len(self.story) + 1
        self.layer_src.value = ""
        self.bounds.value = ""
        self.custom_code.value = ""

        # 8) Log what happened
        self._log(f"✅ {action} scene “{scene_title}” at position {scene_order}")

    def _preview_scene(self, _=None):
        """
        1) Run any custom‐Python snippet the user wrote.
        2) Validate the URL/path or skip if there’s nothing to add.
        3) Auto‐detect layer type & build a consistent layer_def.
        4) Append the new layer_def to self.layers.
        5) Clear existing overlays (only keep the base).
        6) Re‐apply every layer_def via _apply_layer_def,
        enabling on‐map bounds editing for images/videos.
        7) Fit the map to all overlay bounds.
        8) Log a success message.
        """
        # 1) execute custom code (may add layers via code)
        self._run_custom_code(None)

        # 2) check for a new URL/path if no layers exist yet
        src = self.layer_src.value.strip()
        if not src and not self.layers:
            return self._log("❌ No URL/path entered")

        # 3) detect type
        lt = detect_layer_type(src) if src else None
        if src and lt == "unknown":
            return self._log(f"❌ Could not detect layer type for: {src}")

        # 4) build layer_def only if src provided
        if src:
            name = f"{lt.upper()}-{len(self.layers)}"
            layer_def = {"type": lt, "name": name}

            # path vs url
            if lt in ("geojson", "raster", "wms", "tile", "image", "video"):
                layer_def["path"] = src
            else:
                layer_def["url"] = src

            # bounds for image/video
            if lt in ("image", "video"):
                layer_def["bounds"] = self._get_slider_bounds()

            # (we’re no longer handling EE here—EE layers come via custom code)
            self.layers.append(layer_def)

        # 6) re‐draw every layer
        applied = []
        for ld in self.layers:
            try:
                layer = self._apply_layer_def(ld)
                if layer and hasattr(layer, "bounds"):
                    applied.append(layer)
                    # if image/video, enable on‐map editing
                    if ld["type"] in ("image", "video"):
                        self._active_overlay = layer
                        sw, ne = layer.bounds
                        # init sliders
                        self.bound_sliders["south"].value = sw[0]
                        self.bound_sliders["west"].value = sw[1]
                        self.bound_sliders["north"].value = ne[0]
                        self.bound_sliders["east"].value = ne[1]
                        self.bounds_container.layout.display = "block"
            except Exception as e:
                self._log(f"❌ Failed to apply {ld.get('name')}: {e}")

        # 7) zoom to all overlays
        if applied:
            self._zoom_to_layers(None)

        # 8) final log
        self._log(f"✅ Previewed scene with {len(self.layers)} layer(s)")

    def _copy_scene(self, _=None):
        """
        Duplicate the currently selected Scene, insert it immediately after,
        and bump all later scenes’ order numbers by +1.
        """
        idx = self.scene_selector.index
        if idx < 0:
            return  # nothing selected

        original = self.story[idx]
        new_order = original.order + 1

        # 1) Shift any existing scenes at or after new_order down by 1
        for s in self.story:
            if s.order >= new_order:
                s.order += 1

        # 2) Deep‐copy the layer definitions & custom code
        new_layers = copy.deepcopy(original.layers)
        new_custom = getattr(original, "custom_code", "")

        # 3) Build the new Scene
        new_scene = Scene(
            center=original.center,
            zoom=original.zoom,
            layers=new_layers,
            title=f"{original.title} - Copy",
            order=new_order,
            basemap=getattr(original, "basemap", None),
            custom_code=new_custom,
        )

        # 4) Insert, resort, refresh UI
        self.story.append(new_scene)
        self.story.sort(key=lambda s: s.order)
        self._refresh_scene_list()

        # 5) Feedback to the user
        self._log(
            f"✅ Copied “{original.title}” to “{new_scene.title}” at position {new_order}"
        )

    def _delete_scene(self, _):
        i = self.scene_selector.index
        if i < 0:
            return
        self.story.pop(i)
        self._refresh_scene_list()
        self._log(f"Deleted scene {i}.")

    def _export_story(self, _=None):
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
                    "layers": s.layers,
                }
            )
        # Write to file
        fn = "story.json"
        with open(fn, "w") as f:
            json.dump(out, f, indent=2)
        # Log and show link
        self._log(f"✅ Story exported to {fn}")
        display(FileLink(fn))

    def _load_scene(self, _=None):
        self._clear_layers
        # Figure out which scene is selected
        idx = self.scene_selector.index
        if idx < 0:
            return
        scene = self.story[idx]

        # Update your form fields
        self.title.value = scene.title or ""
        self.order_input.value = scene.order

        # Reset your builder state
        self.layers = [ld.copy() for ld in scene.layers]
        if hasattr(self, "drawn_features"):
            self.drawn_features = [
                feat
                for ld in scene.layers
                if ld["type"] == "geojson" and "data" in ld
                for feat in ld["data"]["features"]
            ]

        # Re‑apply only this scene’s layers
        for ld in self.layers:
            try:
                self._apply_layer_def(ld)
            except Exception as e:
                self._log(f"❌ Failed to load layer {ld.get('name')}: {e}")

        self.map.center = scene.center
        self.map.zoom = scene.zoom

        # Give the user feedback
        self._log(f"🔄 Loaded scene “{scene.title}” ({len(self.layers)} layers)")

    def _update_scene(self, _):
        i = self.scene_selector.index
        if i < 0:
            return
        scene = Scene(
            center=(self.lat.value, self.lon.value),
            zoom=self.zoom.value,
            layers=self.layers.copy(),
            title=self.title.value.strip() or f"Scene {i+1}",
            order=self.order_input.value,
        )
        self.story[i] = scene
        self._refresh_scene_list()
        self._log(f"Updated scene {i}.")

    def _refresh_scene_list(self):
        options = []
        for i, s in enumerate(self.story):
            label = f"{s.order}: {s.title or f'Scene {i+1}'}"
            options.append((label, i))
        self.scene_selector.options = options

    def _toggle_log_output(self, change):
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

    def _render_log(self):
        """
        Clear and print every message in log_history.
        """
        with self.output:
            self.output.clear_output(wait=True)
            for msg in self.log_history:
                print(msg)

    def _log(self, message):
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

    def _toggle_code(self, change):
        if change["new"]:
            self.toggle_code_button.description = "Hide Code"
            self.code_container.layout.display = "block"
        else:
            self.toggle_code_button.description = "Show Code"
            self.code_container.layout.display = "none"

    def _run_custom_code(self, _):
        """
        Exec the user’s Python snippet with `map` in scope,
        intercept add_earthengine calls and record them.
        """
        code = self.custom_code.value
        real_add_ee = self.map.add_earthengine

        def _recording_add_ee(*args, **kwargs):
            layer = real_add_ee(*args, **kwargs)

            ee_obj = kwargs.get("ee_object") or (args[0] if args else None)
            vis = kwargs.get("vis_params", {})
            name = kwargs.get("name") or f"EE-{len(self.layers)}"

            self.layers.append(
                {
                    "type": "earthengine",
                    "ee_id": ee_obj,
                    "vis_params": vis,
                    "name": name,
                }
            )
            return layer

        self.map.add_earthengine = _recording_add_ee

        try:
            exec(code, {}, {"map": self.map})
            self._log("✅ Custom code executed")
        except Exception as e:
            import traceback

            tb = traceback.format_exc().splitlines()[-1]
            self._log(f"❌ Code error: {tb}")
        finally:
            self.map.add_earthengine = real_add_ee

    def _on_scene_select(self, change):
        """Automatically load & preview whenever the dropdown changes."""
        if change["new"] is None:
            return
        # reuse your existing handlers
        self._load_scene(None)
        self._preview_scene(None)

    def _apply_layer_def(self, ld):
        """
        Load a single saved layer_def dict directly onto the map.
        """
        t = ld["type"]
        name = ld.get("name", None)

        self._log(f"→ Applying {t} layer: {name or ld['path']}")

        if t == "tile":
            self.map.add_tile(url=ld["path"], name=name)
        if ld["type"] == "geojson":
            if "data" in ld:
                layer = GeoJSON(data=ld["data"], name=ld.get("name"))
            else:
                layer = GeoJSON(data=open(ld["path"]).read(), name=ld.get("name"))
            self.map._add_layer(layer)
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
            self._log(f"❌ Unknown layer type: {t}")

    def _zoom_to_layers(self, _):
        """
        Pan & zoom the map so that the union of all overlay layer bounds is in view.
        """
        # collect only real, non‐None bounds
        bboxes = [
            layer.bounds
            for layer in self.map.layers[1:]
            if hasattr(layer, "bounds") and layer.bounds is not None
        ]
        if not bboxes:
            return self._log("⚠️ No overlay layers to zoom to.")

        # flatten all corner points
        pts = [pt for bb in bboxes for pt in bb]
        lats = [p[0] for p in pts]
        lons = [p[1] for p in pts]

        sw = (min(lats), min(lons))
        ne = (max(lats), max(lons))

        self.map.fit_bounds([sw, ne])
        self._log("🔍 Zoomed to fit all layers.")

    def _load_def_into_ui(self, layer_def):
        """
        Copy a saved layer definition back into the builder widgets
        so that _preview_scene can pick it up.
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

    def _enter_present_mode(self, _=None):
        scenes = sorted(self.story, key=lambda s: s.order)
        story_obj = Story(scenes)
        teller = StoryController(story_obj, self.map)

        # show the Edit button above the presenter interface
        header = widgets.HBox(
            [self.edit_button], layout=widgets.Layout(justify_content="flex-end")
        )
        self.main_container.children = [header, teller.interface]

    def _exit_present_mode(self, _=None):
        # Simply restore the builder UI as the sole child
        self.main_container.children = [self.builder_ui]

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

    def _on_map_layers_change(self, change):
        """
        Whenever map.layers grows, schedule a zoom‑to‑layers on the
        notebook’s asyncio loop (so fit_bounds works correctly).
        """
        old = change["old"]
        new = change["new"]

        # only act when layers have been added
        if len(new) <= len(old):
            return

        try:
            loop = asyncio.get_event_loop()
            loop.call_later(0.1, lambda: self._zoom_to_layers(None))
        except RuntimeError:
            # if there’s no running loop, just fire immediately
            self._zoom_to_layers(None)

    def _enable_bounds_editing(self, overlay):
        """
        Let the user drag/resize a rectangle on the map to reset
        overlay.bounds interactively.
        """
        # 1) If there’s an old DrawControl, remove it
        if hasattr(self, "bound_draw_control"):
            self.map.remove_control(self.bound_draw_control)

        # 2) Make a DrawControl that only lets you draw/modify one rectangle
        dc = DrawControl(
            rectangle={"shapeOptions": {"color": "#00FF00", "weight": 2}},
            polygon=False,
            circle=False,
            circlemarker=False,
            marker=False,
            polyline=False,
        )

        # 3) Define a helper to clear any previous helper‐rectangle
        def _clear_prev_rect():
            for layer in list(self.map.layers):
                if isinstance(layer, Rectangle) and layer.name == "_bound_editor":
                    self.map.remove_layer(layer)

        # 4) When they draw or edit, update the overlay
        def _on_draw(target, action, geo_json):
            if action in ("created", "edited"):
                _clear_prev_rect()
                coords = geo_json["geometry"]["coordinates"][0]
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                sw = (min(lats), min(lons))
                ne = (max(lats), max(lons))

                # show a draggable helper so they see the new box
                helper = Rectangle(
                    bounds=[sw, ne], name="_bound_editor", draggable=True
                )
                self.map.add_layer(helper)

                # finally, re‑assign the real overlay’s bounds
                overlay.bounds = (sw, ne)

        dc.on_draw(_on_draw)

        # 5) **Add** the DrawControl to the map and keep a reference
        self.bound_draw_control = dc
        self.map.add_control(dc)

    def _clear_layers(self, _=None):
        """Remove every overlay (keep only base) and reset the layer list."""
        # 1) Remove map overlays
        for lyr in list(self.map.layers)[1:]:
            self.map.remove_layer(lyr)

        # 2) Forget our internal defs & active overlay
        self.layers.clear()
        self._active_overlay = None

        # 3) Hide bounds editor (if it was visible)
        self.bounds_container.layout.display = "none"

        # 4) Log it
        self._log("🗑️ Cleared all layers")

    def _on_src_change(self, change):
        """
        Display the bounds sliders if the new URL is an image/video,
        otherwise hide them.
        """
        url = change["new"].strip().lower()
        is_img = url.endswith((".png", ".jpg", ".jpeg", ".gif", ".tiff"))
        is_vid = url.endswith((".mp4", ".webm"))
        if is_img or is_vid:
            # unhide and initialize sliders if needed
            self.bounds_container.layout.display = "block"
            # optionally set defaults here, e.g. full‐world extent
            self.bound_sliders["south"].value = -30
            self.bound_sliders["west"].value = -30
            self.bound_sliders["north"].value = 30
            self.bound_sliders["east"].value = 30
            # set bounds text to match sliders
            self.bounds.value = repr(self._get_slider_bounds())

        else:
            self.bounds_container.layout.display = "none"

    def _get_slider_bounds(self):
        s = self.bound_sliders
        return (
            (s["south"].value, s["west"].value),
            (s["north"].value, s["east"].value),
        )

    def _update_overlay_bounds(self, change):
        if self._active_overlay is None:
            return

        sw = (self.bound_sliders["south"].value, self.bound_sliders["west"].value)
        ne = (self.bound_sliders["north"].value, self.bound_sliders["east"].value)
        # this immediately resizes the overlay on the map
        self._active_overlay.bounds = (sw, ne)


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
