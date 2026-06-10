# Frontend parity checklist

Gate for Phase 5a sign-off. Each item must pass in the Vue SPA at `/app/…`.

## Global

- [ ] Session login/logout, password change
- [ ] Public read vs authenticated write permissions
- [ ] CSRF on mutations
- [ ] API keys + DRF token (profile)
- [ ] Project list and switcher
- [ ] Documentation page
- [ ] Carry-over (stars → spectra/LC)
- [ ] Celery bulk download with progress
- [ ] Classic ↔ New UI toggle

## Dashboard

- [ ] Stats counters
- [ ] HRD plot + all form parameters
- [ ] Starmap preview + fullscreen modal
- [ ] Changelog feed
- [ ] Observation requests removed (intentional)

## Systems

- [ ] Stars: filters, selection, delete, carry-over
- [ ] Star detail: SED, note, tags, edit page
- [ ] Tags: CRUD

## Observations

- [ ] Spectra: filters, bulk DL processed/raw, delete
- [ ] Spectrum detail: rebin, normalize, note
- [ ] Spectra upload
- [ ] Specfiles, rawspecfiles, light curves lists + actions
- [ ] Light curve detail
- [ ] Observatories edit

## Analysis

- [ ] Datasets: filters, bulk DL, detail plots
- [ ] Methods: delete with warning
- [ ] Parameter plotter: form + statistics

## Profile

- [ ] DRF token regenerate
- [ ] API key pair generate
