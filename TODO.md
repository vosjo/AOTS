# Backlog

## Bulk downloads: replace synchronous ZIP with Celery

### Problem (today)

- **API:** `GET` `bulkDownloadSpectra` (`observations/api/views.py`) copies FITS files into a temp
  directory, builds a ZIP in the **same HTTP request**, and streams it back. Large selections tie up
  a Gunicorn worker and can hit the configured request timeout (600s).
- **UI:** List views (`site_static/js/spectra_list.js`, `rawspecfiles_list.js`, …) fetch many
  files in the browser and pack them with JSZip — heavy on the client and the server for many
  parallel downloads.

Permissions and project checks must stay as strict as they are now.

### Target

1. **Enqueue** a download job (project + star/spectrum selection, same headers/params as today).
2. **Celery worker** builds the ZIP under `MEDIA_ROOT` or a dedicated temp area, updates task
   progress if useful.
3. **Client polls** `GET /api/observations/tasks/<task_id>/` (already used for `?async=1`
   processing) until `SUCCESS`, then downloads via a short-lived file URL or a dedicated
   `GET …/download/<task_id>/` that streams the artifact and deletes temp files.

Optional later: same pattern for very large **bulk uploads** (`bulkUploadSpectra`).

### Prerequisites (mostly done)

- Redis + `CELERY_BROKER_URL` in `.env`
- `celery -A AOTS worker` (see README)
- `run_task` / task status API in `AOTS/task_helpers.py` and observations API

### Implementation sketch

| Step | Work |
|------|------|
| 1 | New Celery task `build_bulk_spectra_zip` in `observations/tasks.py` (reuse selection logic from `bulkDownloadSpectra`). |
| 2 | New endpoints: start job (`202` + `task_id`), poll status, download result; enforce `check_project_access` / `get_allowed_objects_to_view_for_user`. |
| 3 | Retire or thin the synchronous `bulkDownloadSpectra` path (keep sync fallback behind a flag only if needed for API clients). |
| 4 | Frontend: replace JSZip bulk actions with “prepare download → poll → save file” (progress in UI). |
| 5 | Ops: TTL/cleanup for temp ZIPs; worker memory limits; document Redis as **required** for bulk download in production. |

### Out of scope (for this item)

- Changing DataTables list behaviour unrelated to download.
- Migrating single-file downloads that are already fast.
