# MAESon

MAESon is a lightweight, Python-based geospatial presentation library designed for researchers, educators, and analysts of all skill levels. It enables the quick creation of interactive maps, scene-building interfaces, and multimedia geospatial storytelling tools.

## Installation

```bash
pip install maeson
```

## Key Features

* **Interactive Maps**: Create and customize maps with `maeson.Map`, supporting pan, zoom, and layer controls.
* **Scene Builder**: Use `SceneBuilder` from the `gistory` module to assemble map scenes with vectors, rasters, images, and videos.
* **Data Format Support**: Load GeoJSON vectors, raster files (e.g., GeoTIFF, PNG), and multimedia assets.
* **Earth Engine Integration**: Preview and interact with Google Earth Engine data catalog entries.
* **Extensible UI**: Built on ipyleaflet and ipywidgets, offering a flexible interface for custom widgets and controls.

## Quickstart Example

```python
from maeson import Map
from maeson.gistory import SceneBuilder

# 1. Create an interactive map
m = Map(center=(0, 0), zoom=3)

# 2. Attach the SceneBuilder
builder = SceneBuilder(m)

# 3. Display the builder and load data
builder.display()
```

## Usage

1. **Raster Layer**: Paste a raster URL into the UI, then click **Preview**.
2. **Vector Layer**: Paste a GeoJSON URL or path, then click **Preview**.
3. **Image/Video Layer**: Paste a media URL, adjust bounds, and preview.

## Documentation & Examples

Interactive Jupyter notebooks demonstrating module usage are available in the repository under the `examples/` directory. Each notebook includes a Colab badge for one-click access.

## Contributing

Contributions are welcome! Please open issues or pull requests on the [GitHub repository](https://github.com/yourusername/maeson).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
