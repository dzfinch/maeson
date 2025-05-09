# Maeson: Making Awesome Earth Science presentatiONs

[![image](https://img.shields.io/pypi/v/maeson.svg)](https://pypi.python.org/pypi/maeson)

Welcome to **Maeson**, the all-in-one geospatial toolkit for creating, editing, and sharing dynamic Earth science narratives directly within your Jupyter environment. Maeson simplifies complex geospatial workflows by uniting data processing, visualization, and interactive storytelling into a single, cohesive package.

## Key Features

* 🚀 **Rapid Scene Creation**: Define map extents, set zoom levels, and add diverse layers (GeoJSON, raster, tile, WMS, imagery, video, and Earth Engine) with just a few lines of Python.
* 🔄 **Live Previews**: Instantly render and update layers in-place. Tweak layer parameters or custom scripts and see changes reflected on the map in real time.
* 🔧 **Custom Code Integration**: Write arbitrary Python snippets (e.g., Earth Engine calls, heatmaps, analytics) in the embedded code editor, execute them on your map, and save them alongside each scene.
* 📑 **Structured Storytelling**: Organize multiple scenes into an ordered sequence, annotate with titles and metadata, and export your narrative as JSON for later reuse or publication.
* 📊 **Presentation Mode**: Switch seamlessly from authoring to playback. Advance through your scenes with Next/Back controls, focusing your audience on the evolving map story.
* 🎨 **Interactive Bounds Editing**: Adjust image and video overlays by dragging or via sliders—no need to recode bounds manually.

## Getting Started

```python
import maeson
from maeson import Map, StoryBuilder, StoryTeller

# 1. Initialize your map
m = Map(center=(37.77, -122.42), zoom=10)

# 2. Launch the story builder
builder = StoryBuilder(m)
builder.display()

# 3. Add layers, set titles, and preview interactively
# 4. Save scenes and switch to presentation mode
```

## Example Workflow

1. **Load data**: Use `m.add_geojson()`, `m.add_raster()`, or custom Earth Engine calls in the code editor.
2. **Preview**: Click Preview to render layers and auto-zoom to extents.
3. **Save**: Title and save your scene—Maeson persists both the map state and any custom code.
4. **Copy & Clear**: Duplicate or clear layers between scenes for iterative storytelling.
5. **Present**: Hit Present to enter an uncluttered playback interface.

## Extensibility

Maeson’s modular design lets you:

* Hook into additional mapping libraries (e.g., Leafmap, MapLibre)
* Integrate new layer types or data sources
* Customize UI components to match your workflow

---

> **Maeson**: Making Awesome Earth Science Presentations — your one-stop solution for geospatial storytelling.

