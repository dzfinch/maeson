# Usage

To use maeson in a project:

## Installation

To install or upgrade the `maeson` package, uncomment and run:

```bash
pip install --upgrade maeson
```

## Quickstart with SceneBuilder

The `maeson.gistory.SceneBuilder` provides an interactive presentation interface for geographic data, accommodating all expertise levels. It supports GeoJSON vectors, raster files, images, videos, and Google Earth Engine datasets.

```python
import maeson
from maeson.gistory import SceneBuilder

# 1. Create an interactive map
m = maeson.Map(center=(0, 0), zoom=2)

# 2. Attach the SceneBuilder to the map
builder = SceneBuilder(m)

# 3. Launch the UI
builder.display()
```

## Example Layers

Use the following URLs and values to explore different layer types:

### 1. Raster Layer

* **URL/Path**: `https://github.com/opengeos/datasets/releases/download/samgeo/tree_image.tif`

### 2. Vector Layer

* **URL/Path**: `https://github.com/opengeos/datasets/releases/download/vector/TN_Counties.geojson`

### 3. Image Layer

* **URL/Path**: `https://i.imgur.com/06Q1fSz.png`
* **Bounds**: `((13, -130), (32, -100))`

### 4. Video Layer

* **URL/Path**: `https://github.com/opengeos/datasets/releases/download/videos/aral_sea_blended.mp4`
* **Status**: Currently broken; bounds slider will populate but video may not render.

### 5. Google Earth Engine Layers

Open the code editor (E) and uncomment the desired block, then click **Preview**.

```python
# Example: Sentinel-2 True Color (Jun 2021)
import ee
ee.Initialize()
sentinel = (
    ee.ImageCollection("COPERNICUS/S2_SR")
      .filterDate("2021-06-01", "2021-06-30")
      .filterBounds(ee.Geometry.Point(-122.4, 37.8))
)
map.add_earthengine(
    ee_object=sentinel,
    vis_params={"bands": ["B4", "B3", "B2"], "min": 0, "max": 3000},
    name="Sentinel-2 True Color (Jun 2021)"
)

# Example: Annual mean MODIS NDVI (2021)
ndvi = (
    ee.ImageCollection("MODIS/006/MOD13A1")
      .select("NDVI")
      .filterDate("2021-01-01", "2021-12-31")
      .mean()
)
map.add_earthengine(
    ee_object=ndvi,
    vis_params={"min": 0, "max": 9000, "palette": ["white", "yellow", "green"]},
    name="MODIS NDVI 2021"
)
```

---

With these steps, you can quickly spin up interactive geographic presentations using `maeson` and `SceneBuilder`.
