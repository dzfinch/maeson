# `folmap`: Enhanced Interactive Mapping with Folium

`folmap` is a lightweight Python module that extends the functionality of [`folium`](https://python-visualization.github.io/folium/) for interactive web maps. It simplifies adding common geospatial data formats like shapefiles, GeoJSON, and raster overlays, and includes helpers for split maps and Esri basemaps.

---

## 🚀 Getting Started

### 📦 Installation

Install the required dependencies:

```bash
pip install folium geopandas
```

Add `folmap.py` to your project or install it from your package repository (if published on PyPI):

```bash
pip install folmap
```

---

## 🧭 Class: `Map`

```python
from folmap import Map
```

An enhanced subclass of `folium.Map` that adds built-in support for:

- 📌 Esri basemaps
- 🧩 GeoJSON and shapefiles
- 🌿 GeoDataFrames
- 🖼️ Raster overlays
- 🔀 Side-by-side (split) basemap comparison

### Constructor

```python
Map(center=(0, 0), zoom=2, **kwargs)
```

**Arguments:**

- `center` *(tuple)*: Latitude and longitude of the map center.
- `zoom` *(int)*: Initial zoom level.
- `**kwargs`: Additional keyword arguments for `folium.Map`.

---

## 🔧 Methods

### `add_basemap(name: str, **kwargs)`

Adds an Esri basemap to the map.

**Arguments:**

- `name` *(str)*: One of the following: `"Road"`, `"Satellite"`, `"Topo"`, `"Terrain"`.
- `**kwargs`: Additional options passed to `folium.TileLayer`.

**Raises:**

- `ValueError`: If the name is not supported.

---

### `add_geojson(data, name="GeoJSON Layer", **kwargs)`

Adds GeoJSON data from a file path or dictionary.

**Arguments:**

- `data` *(str or dict)*: Path to a GeoJSON file or a Python dictionary.
- `name` *(str)*: Layer name for the legend.
- `**kwargs`: Additional keyword arguments for `folium.GeoJson`.

---

### `add_shp(data: str, **kwargs)`

Adds a shapefile layer to the map.

**Arguments:**

- `data` *(str)*: Path to a `.shp` file (shapefile).
- `**kwargs`: Passed to the underlying `add_geojson` method.

---

### `add_gdf(gdf, name="GDF Layer", **kwargs)`

Adds a `GeoDataFrame` to the map.

**Arguments:**

- `gdf` *(geopandas.GeoDataFrame)*: The spatial data.
- `name` *(str)*: Layer name.
- `**kwargs`: Optional style parameters.

---

### `add_vector(data, name="Vector Layer", **kwargs)`

Generic method for adding any vector data type.

**Arguments:**

- `data` *(str, dict, or GeoDataFrame)*: File path, GeoJSON, or GeoDataFrame.
- `name` *(str)*: Layer name.
- `**kwargs`: Passed to internal rendering methods.

**Raises:**

- `ValueError`: If the data type is unsupported.

---

### `add_layer_control()`

Adds a layer switcher widget to toggle visibility of basemaps and layers.

---

### `add_raster(data: str, layer_name: str, **kwargs)`

Adds a raster overlay image (e.g., PNG, TIFF) to the map.

**Arguments:**

- `data` *(str)*: File path or URL to the image.
- `layer_name` *(str)*: Display name for the raster layer.
- `**kwargs`: Additional options for `folium.ImageOverlay`.

---

### `add_split_map(left="openstreetmap", right="cartodbpositron", **kwargs)`

Creates a side-by-side comparison of two basemaps or raster layers.

**Arguments:**

- `left` *(str)*: Left layer name or file path.
- `right` *(str)*: Right layer name or file path.
- `**kwargs`: Additional display options for both layers.

**Supports:**

- Standard folium basemap names (`"openstreetmap"`, `"stamenterrain"`, etc.)
- Tiled image files (`.tif`, `.png`)

---

## 🧪 Example

```python
from folmap import Map

# Initialize the map
m = Map(center=(35.95, -83.92), zoom=8)

# Add a basemap
m.add_basemap("Satellite")

# Add a shapefile
m.add_shp("data/watersheds.shp", name="Watersheds")

# Add raster overlay
m.add_raster("data/ndvi_overlay.tif", layer_name="NDVI Overlay", opacity=0.6)

# Layer control and export
m.add_layer_control()
m.save("interactive_map.html")
```