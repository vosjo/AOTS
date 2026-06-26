# REST list API contract

Standard list responses use DRF page-number pagination:

```json
{
  "count": 42,
  "next": "/api/observations/spectra/?page=2&page_size=20&project=1",
  "previous": null,
  "results": [ … ]
}
```

## Query parameters

| Parameter | Description |
|-----------|-------------|
| `page` | 1-based page index |
| `page_size` | Rows per page (default 20, max 1000) |
| `ordering` | Field name; prefix `-` for descending (e.g. `-hjd`) |
| `project` | Required project PK (django-filter) |
| Filter fields | Per-endpoint; see filter classes |

## Endpoints

| Endpoint | Default ordering |
|----------|------------------|
| `/api/systems/stars/` | `name` |
| `/api/systems/tags/` | `name` |
| `/api/observations/spectra/` | `hjd` |
| `/api/observations/specfiles/` | `hjd` |
| `/api/observations/rawspecfiles/` | `hjd` |
| `/api/observations/lightcurves/` | `hjd` |
| `/api/observations/observatories/` | `name` |
| `/api/analysis/analyses/` | `name` |
| `/api/analysis/categories/` | (static registry, not paginated) |
