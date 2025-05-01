# gistory

**gistory** is a lightweight Python module for building **interactive geographic storytelling** in Jupyter notebooks. It provides a simple API to define map-based "scenes" and navigate through them with smooth transitions, dynamic layer loading, and interactive widgets.

---

## Features

- **Scene definition**: Specify map center, zoom level, caption, and overlay layers (tile, GeoJSON, raster, image).
- **Story sequencing**: Organize multiple `Scene` objects into a `Story` that can be navigated sequentially.
- **Interactive controls**: `StoryController` renders Next/Back buttons, captions, and map updates in Jupyter.
- **Layer handling**: Leverage built-in `maeson.Map` methods (`add_tile`, `add_geojson`, `add_raster`, `add_image`, `add_wms`, `add_earthengine`) for clean integration.
- **Scene authoring**: `SceneBuilder` widget allows users to construct, preview, edit, and export scenes interactively.
- **Export & import**: Save and load entire stories to/from JSON for later reuse or sharing.

---

## Installation

```bash
pip install maeson  # includes gistory submodule
# or if standalone:
pip install gistory
```

Ensure you have Jupyter, ipyleaflet, and ipywidgets enabled:

```bash
pip install jupyterlab ipyleaflet ipywidgets
jupyter nbextension enable --py --sys-prefix ipyleaflet
jupyter nbextension enable --py --sys-prefix widgetsnbextension
```

---

## Quick Start

```python
from maeson.gistory import Scene, Story, StoryController
from ipyleaflet import Map

# 1. Prepare a base map
m = Map(center=(0, 0), zoom=2)

# 2. Define scenes
scenes = [
    Scene(
        center=(37.7749, -122.4194), zoom=10,
        caption="San Francisco",
        layers=[
            {"type": "tile", "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"},
            {"type": "geojson", "path": "data/sf.geojson", "name": "SF Zones"}
        ],
        title="SF Overview",
        order=1
    ),
    Scene(
        center=(48.8566, 2.3522), zoom=12,
        caption="Paris Historical Map",
        layers=[
            {"type": "tile", "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"},
            {"type": "image", "url": "https://upload.wikimedia.org/wikipedia/commons/d/d2/Plan_de_Paris_1857.png", "bounds": [[48.835, 2.26], [48.885, 2.40]]}
        ],
        title="Paris 1857",
        order=2
    )
]

# 3. Build story and controller
story = Story(scenes)
controller = StoryController(story, m)
controller.display()
```

---

## API Reference

### `class Scene`

```python
class Scene:
    def __init__(
        self,
        center: Tuple[float, float],
        zoom: int,
        caption: str = "",
        layers: List[dict] = None,
        title: str = None,
        order: int = 1
    )
```

- **center**: `(lat, lon)` map center.
- **zoom**: integer zoom level.
- **caption**: text displayed below the map.
- **layers**: list of layer definitions (see below).
- **title**: scene title for selectors and exports.
- **order**: integer slide order.


### `class Story`

```python
class Story:
    def __init__(self, scenes: List[Scene])
    def current_scene(self) -> Scene
    def next_scene(self) -> Scene
    def previous_scene(self) -> Scene
```

Manages a sequence of `Scene` objects and provides navigation indices.


### `class StoryController`

```python
class StoryController:
    def __init__(self, story: Story, map_obj: ipyleaflet.Map)
    def display(self)
```

- Renders interactive Next/Back buttons, map view updates, and captions.
- Automatically clears and reloads per-scene layers.


### `class SceneBuilder`

**Interactive widget** for building scenes in Jupyter:

- **Fields**: title, order, center (lat/lon), zoom, caption, layer type, source URL/path, bounds.
- **Buttons**: Add Layer, Save Scene, Preview, Load, Update, Delete, Export Story, Toggle Log.
- **Features**:
  - Auto-detect layer type from URL/path.
  - Live map preview of each scene.
  - Full history vs most-recent log.
  - Export/import JSON.


---

## Layer Definitions

Each layer is a dict specifying:

- **type**: one of `tile`, `geojson`, `image`, `raster`, `wms`, `earthengine`.
- **url** or **path**: source location.
- **name**: optional display name.
- **bounds**: for image overlays (`[[south, west], [north, east]]`).
- **vis_params**: for Earth Engine layers.

Example:
```json
{
  "type": "tile",
  "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  "name": "OSM"
}
```

---

## Contributing

Feel free to open issues or pull requests on GitHub. New layer types and UI enhancements are welcome!
