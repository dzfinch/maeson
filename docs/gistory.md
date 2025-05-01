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

::: maeson.gistory

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
