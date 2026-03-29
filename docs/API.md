# Forest Connectivity API

The Forest Connectivity API allows you to trigger and monitor asynchronous Morphological Spatial Pattern Analysis (MSPA) workflows on Google Earth Engine.

## Authentication
Use Bearer `{TOKEN}` (Standard CoRE Stack JWT) via `Authorization` header. Note: This requirement assumes CoRE Stack gateway enforcement.

## Endpoints

### `POST /api/v1/forest-connectivity/`
Triggers a new analysis run per block. 
The system enforces validation and idempotency. If a task with the exact parameters has already run successfully, the old task ID and asset bounds are returned.

#### Request body:
```json
{
  "state": "Jharkhand",
  "district": "Ranchi",
  "block": "Kanke",
  "lulc_year": "2023_2024",
  "edge_width_m": 100, 
  "islet_area_ha": 1.0,
  "notify_email": "user@example.com"
}
```

* `edge_width_m` defaults to 100m.
* `islet_area_ha` defaults to 1.0ha.


#### Response (202 Accepted):
```json
{
  "task_id": "8482d8c3-f046-4e0d-b0cd-a044ea7231ce",
  "status_url": "/api/v1/forest-connectivity/8482d8c3-f046-4e0d-b0cd-a044ea7231ce/",
  "status": "queued"
}
```

### `GET /api/v1/forest-connectivity/<task_id>/`

Returns the current status of the pipeline (e.g. `pending`, `computing`, `exporting`, `publishing`, `done`, `failed`). Once complete, includes paths to the raster and vector assets.

#### Response (200 OK):
```json
{
  "task_id": "8482d8c3-f046-4e0d-b0cd-a044ea7231ce",
  "status": "done",
  "created_at": "2026-03-29T10:00:00Z",
  "updated_at": "2026-03-29T10:30:00Z",
  "assets": {
    "raster": "projects/corestack-datasets/assets/mspa_raster_8482d8c3...",
    "vector": "projects/corestack-datasets/assets/mspa_vector_8482d8c3..."
  },
  "geoserver_layers": {
    "wms": "http://geoserver/wms/corestack?layers=mspa_raster_8482d8c3...",
    "wfs": "http://geoserver/wfs/corestack?typeName=mspa_raster_8482d8c3..."
  }
}
```
