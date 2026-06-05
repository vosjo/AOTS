# DataTables API field contract

List endpoints use `?format=datatables`. The UI may request extra fields via `keep=`.

| Endpoint | Visible columns (JS) | `keep=` fields | List serializer |
|----------|----------------------|----------------|-----------------|
| `/api/systems/stars/` | name, ra, dec, classification, vmag, nphot, datasets, tags, observing_status | nspec, nlc, ra_hms, dec_dms, observing_status_display | `StarListSerializer` |
| `/api/observations/spectra/` | hjd, star, instrument, resolution, airmass, exptime | pk, specfiles, telescope, href | `SpectrumListSerializer` |
| `/api/observations/specfiles/` | hjd, instrument, filetype, filename, added_on, star, spectrum, pk | — | `SpecFileListSerializer` |
| `/api/observations/rawspecfiles/` | obs_date, instrument, filetype, exptime, filename, added_on, specfile, systems | pk | `RawSpecFileSerializer` |
| `/api/observations/lightcurves/` | (see lightcurves_list.js) | pk, telescope, href | `LightCurveSerializer` |
| `/api/analysis/datasets/` | — | pk, href, file_url | `DataSetListSerializer` |
| `/api/observations/observatories/` | — | short_name, url | `ObservatorySerializer` |

When changing serializers, run contract tests in `observations/tests/test_datatables_contract.py`.
