# AUDIT_REPORT.md - Forest Structural Connectivity (MSPA) Pipeline

## Executive Summary
A comprehensive audit of the CoRE Stack Forest Structural Connectivity pipeline indicates that while the core Morphological Spatial Pattern Analysis (MSPA) algorithm is correctly ported to Google Earth Engine via both JavaScript and Python wrappers, the surrounding backend architecture has significant gaps preventing production readiness. The system successfully extracts Class 6 (Trees) and queues non-blocking asynchronous exports; however, critical flaws exist in idempotency logic (potentially exhausting Earth Engine quotas), error handling during GeoServer publishing (silent failures masking incomplete runs), and security (missing DRF authentication and exposing Earth Engine assets statically to the public). Fixes mapped in this report must be addressed prior to closing the Phase 2 milestone.

## What’s Working
- **Algorithmic Correctness**: The MSPA implementation correctly ignores conflicting LULC classes (such as plantations, crops, and shrubs) and limits computations to Class 6 (Trees).
- **Asynchronous Execution Pattern**: `compute_mspa_task` leverages `delay()` to push jobs to GEE without synchronously blocking the celery worker waiting for Google's processing to finish.
- **Polling Reliability**: The `monitor_exports_task` implements an active polling mechanism for Earth Engine task statuses, successfully resuming state management and saving job bounds when external computation finishes.
- **ORM Data Tracking**: `PipelineRun` and `GEEExportJob` maintain clear relational tracking of state between API and external processors.

## Critical Issues (must fix before merge)

### 1. Weak Idempotency Controls Exhausting GEE Quota
- **File**: `src/forest_connectivity/api.py` (Line 35)
- **Problem**: The system only prevents duplicate executions if an identical run exists in the `done` state (`PipelineRun.objects.filter(state='done', ...)`).
- **Why it’s a risk**: If a user submits duplicate requests while the first task is `pending`, `computing`, or `exporting`, the API queues parallel Celery tasks. This spawns duplicate heavyweight Earth Engine exports, heavily taxing the Google quotas and raising the risk of hitting limit caps.
- **Recommended fix**: Remove `state='done'` from the filter. Return the existing `task_id` for any run matching the parameters unless its state is explicitly `failed`.

### 2. Silent Failures During GeoServer Synchronization
- **File**: `src/forest_connectivity/geoserver_utils.py` (Lines 42, 65)
- **Problem**: The methods `sync_raster_to_geoserver` and `sync_vector_to_geoserver` rely on a broad `except Exception as e:` block. If communication with GeoServer fails, they log an error but swallow the exception. Consequently, `monitor_exports_task` blindly proceeds to set `run.state = 'done'`.
- **Why it’s a risk**: Users receive a completed status with WMS/WFS links (`geoserver_layers` object), but those links will 404 since the layers failed to mount in GeoServer.
- **Recommended fix**: Return a semantic `boolean` from the sync utilities (or re-raise the exception). In `tasks.py`, block the transition to `done` and fail the `PipelineRun` if GeoServer ingestion fails.

### 3. Missing Infrastructure Bootstrapping (.env and Migrations)
- **File**: `docker-compose.yml` (Line 27), Repo Root
- **Problem**: `command: python manage.py runserver 0.0.0.0:8000` is missing database migrations. Furthermore, the documented `.env.example` file is missing entirely from the repository.
- **Why it’s a risk**: Fresh pulls of the repository will crash the API container upon SQL attempts due to missing schemas. Onboarding developers will lack an exact blueprint of variables required (like `GEE_SERVICE_ACCOUNT`).
- **Recommended fix**: Create a `docker/entrypoint.sh` script containing `python manage.py migrate` followed by the Gunicorn/Django boot command. Add `.env.example` back into version control.

### 4. Public Exposure of Protected Earth Engine Assets
- **File**: `src/forest_connectivity/gee_utils.py` (Line 149)
- **Problem**: `make_asset_public` uses `{"all_users_can_read": True}`.
- **Why it’s a risk**: Modifies Earth Engine assets to be universally downloadable by anyone with the link, bypassing organizational access boundaries and potentially exposing proprietary or sensitive block-level analytical data.
- **Recommended fix**: Avoid creating public assets. Instead, use a strict IAM ACL policy restricting reads specifically to the GeoServer service account email `{"users": ["geoserver-sa@core-stack.iam.gserviceaccount.com"]}`.

## Important Issues (should fix for production)

### 5. Lack of Application Access Controls
- **File**: `src/forest_connectivity/api.py` (Line 19)
- **Problem**: `ForestConnectivityView` is unprotected. It utilizes a `BurstRateThrottle` but no `permission_classes`.
- **Why it’s a risk**: Anybody with API access can post compute jobs, risking intentional denial of service against Earth Engine. IP-based rate limiting is insufficient for distributed attacks. 
- **Recommended fix**: Inject `permission_classes = [IsAuthenticated]` (rest_framework.permissions) and ensure token verification middleware is properly configured.

### 6. Missing Route for Prometheus Metric Scraping
- **File**: `src/forest_connectivity/urls.py`
- **Problem**: Although `django_prometheus` is installed and middleware is configured in `settings.py`, the required `/metrics` url export path is missing.
- **Why it’s a risk**: DevOps observability stacks (Prometheus/Grafana) defined in `monitoring/prometheus.yml` cannot scrape metrics from the API service.
- **Recommended fix**: Add `path('', include('django_prometheus.urls'))` to `urls.py`.

### 7. Linear Task Retrying
- **File**: `src/forest_connectivity/tasks.py` (Line 10)
- **Problem**: `@shared_task(bind=True, max_retries=3, default_retry_delay=60)` defaults to static delays.
- **Why it’s a risk**: Upon systemic Earth Engine API rate limiting, linear static queues cause thundering herd effects rapidly retrying the service.
- **Recommended fix**: Change exception handling in `compute_mspa_task` to compute exponential backoff: `raise self.retry(exc=e, countdown=2 ** self.request.retries * 60)`.

## Nice‑to‑Have / Future Work

### 8. Structural Deficiencies in Test Suite
- **File**: `tests/test_connectivity.py`
- **Problem**: Existing tests exclusively cover deprecated local mock classes (`src.connectivity`). There are zero integration tests masking `views.py`, ORM models, or mocked GEE python bindings (`gee_utils.py`).
- **Why it’s a risk**: Without backend-specific CI verifications, regressions to `PipelineRun` serialization or JSON parameters will go straight to production.
- **Recommended fix**: Implement standard pytest-django testing using `APIClient` to mock requests against the `ForestConnectivityView` while utilizing `unittest.mock.patch` on Earth Engine network dependencies.

### 9. Feature Gap vs Acceptance Criteria: Phase 3 MSPA
- **File**: `gee/mspa_analyzer.js` (Lines 205-212, 399) / `gee_utils.py` (Lines 93)
- **Problem**: `Bridge` and `Branch` classes are simply mapped via `ee.Image(0)` stubs.
- **Why it’s a risk**: The requirement in Issue #228 to classify narrow connecting corridors (Bridges) or dead-ends (Branches) between distinct core patches is unfulfilled.
- **Recommended fix**: Use focal min/max iteration algorithms (Morphological thinning) natively on GEE to calculate non-core skeletal pathways and filter them based on their physical connection to disjoint core fragments.

## Action Plan (prioritized tasks with estimated effort)

1. **Fix Idempotency & DB Migrations** *(Effort: 3 Hours)*  
   - Repair `.env.example` file and create `docker/entrypoint.sh`. Update API filter exclusions.
2. **Close Security Loopholes** *(Effort: 4 Hours)*  
   - Stop exporting assets as `public_read`, refine IAM service account scoping for GeoServer, and apply DRF Authentication guards to the API.
3. **Handle Silent GeoServer Failures** *(Effort: 2 Hours)*  
   - Propagate exceptions from `geoserver_utils.py` sync requests and abort the Celery run.
4. **Wire up Observability** *(Effort: 1 Hour)*  
   - Export Prometheus `/metrics` route and implement exponential backoff on Celery retries.
5. **Phase 3 Algorithm Overhaul & Integration Tests** *(Effort: 2 Days)*  
   - Build out morphological skeleton detection for `Bridge` and `Branch` classifications. Mock test DRF views.
