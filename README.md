# AOTS

AOTS is a **Django** backend (REST API, media, Celery tasks) with a **Vue 3 SPA** as the user interface. Production serves the built SPA from Django static files; nginx proxies all application routes to Gunicorn and serves `/static/` and `/media/` directly.

## Installing Django

This will install AOTS using a python virtual environment to avoid conflicts with other packages.

### 1. Prerequisites

Create a directory where all files and the required Python modules can be placed:

```
mkdir www
mkdir aots
cd www/aots
```

For the rest of this guide, we will assume that these directories are located in the user's home directory.

You need the python-dev package. Moreover you should update pip:

```
sudo apt install python-dev-is-python3
pip install -U pip
```

For the Vue frontend (local dev and production builds), install **Node.js 22** (or current LTS) and npm. On Debian/Ubuntu you can use [NodeSource](https://github.com/nodesource/distributions) or install Node in CI the same way as [.github/workflows/ci.yml](.github/workflows/ci.yml).

### 2. Create the virtual environment

Create a new virtual python environment for AOTS and activate it (Bash syntax):

```
python -m venv aotsenv
source aotsenv/bin/activate
```

On Windows Computers do

```
python -m venv aotsenv
aotsenv\Scripts\Activate
```

### 3. Clone AOTS from github

```
git clone https://github.com/vosjo/AOTS.git
```

### 4. Install the requirements

```
cd AOTS
pip install -r requirements.txt
```

### 5. Install frontend dependencies

Requires **Node.js 20+** (CI and `.nvmrc` use **22**). Ubuntu’s default `nodejs` package (18.x) is too old for Tailwind CSS 4 and will fail with a missing `@tailwindcss/oxide` native binding.

```
cd frontend
npm ci
cd ..
```

## Running AOTS locally

Local development uses the Django dev server plus the Vite dev server (hot reload). Production uses a static frontend build — see [Running AOTS in production](#running-aots-in-production-using-a-postgres-database).

### 1. Setup the database

```
python manage.py migrate
```

### 2. Create a admin user

```
python manage.py createsuperuser
>>> Username: admin
>>> Email address: admin@example.com
>>> Password: **********
>>> Password (again): *********
>>> Superuser created successfully.
```

### 3. Configure environment

Copy `AOTS/.env.example` to `AOTS/.env` if you have not already. For local SPA development:

```
DJANGO_ENV=development
VITE_DEV=True
CELERY_TASK_ALWAYS_EAGER=True
```

Set `VITE_DEV=False` only when testing a production-like static build locally.

### 4. Start Django and the frontend

Terminal 1 — Django (project root `AOTS/`):

```
python manage.py runserver
```

Terminal 2 — Vite:

```
cd frontend
npm run dev
```

Open `http://127.0.0.1:8000/w/projects/`. For a static smoke test without Vite:

```
cd frontend && npm run build && cd ..
python manage.py collectstatic --noinput
# VITE_DEV=False in .env, then runserver only
```

## Running AOTS in production using a postgres database

### 1. Setup postgres database

This is only necessary if you want to run in production.

Install the postgres database:

```
sudo apt install postgresql
```

Start postgres command line:

```
sudo -u postgres psql
```

Create the database, user and connect them:

```
CREATE DATABASE aotsdb;
CREATE USER aotsuser WITH PASSWORD 'password';
ALTER ROLE aotsuser SET client_encoding TO 'utf8';
ALTER ROLE aotsuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE aotsuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE aotsdb TO aotsuser;
```

List all databases:

```
\l
```

Connect to our database and list all tables:

```
\c aotsdb
\dt
```

To drop the database and recreate it when you want to completely reset everything (the user does not get deleted in this
process):

```
DROP DATABASE aotsdb;
CREATE DATABASE aotsdb;
GRANT ALL PRIVILEGES ON DATABASE aotsdb TO aotsuser;
```

Exit the psql:

```
\q
```

### 2. Create an .env file

To protect secrets like the postgres database password or the Django security key they are embedded in AOTS via
environment variables. The environment variables are defined in the .env file in the AOTS directory. As an example we
provide .env.example.

```
cp AOTS/.env.example  AOTS/.env
```

### 3. Adjust the .env file

In .env the secret Django security key, the postgres database password, the server IP and URL, as well as the name of
the computer used in production needs to be specified.

```
SECRET_KEY=generate_and_add_your_secret_security_key_here
DJANGO_ENV=production
VITE_DEV=False
DATABASE_NAME=aotsdb
DATABASE_USER=aotsuser
DATABASE_PASSWORD=your_database_password
DATABASE_HOST=localhost
DATABASE_PORT=
DEVICE=the_name_of_your_device_used_in_production
ALLOWED_HOSTS=server_url,server_ip,localhost
CSRF_TRUSTED_ORIGINS=https://your_server_url
CELERY_BROKER_URL=redis://localhost:6379/0
```

Production uses the **Vue SPA only**: Django serves the app on `/w/`, `/accounts/`, `/admin/`, etc. `VITE_DEV` must be `False` so the shell loads `/static/dist/…`, not the Vite dev server. Django’s built-in admin UI is at `/django-admin/` if needed.

`DEVICE` is optional if `DJANGO_ENV=production` is set (legacy fallback: hostname match).
`CELERY_BROKER_URL` is required for bulk downloads and other background jobs (see
[Redis and background tasks (Celery)](#redis-and-background-tasks-celery)).

Instructions on how to generate a secret key can be found
here: https://tech.serhatteker.com/post/2020-01/django-create-secret-key/

### 4. Setup the database

```
python manage.py migrate
```

In case you want a fresh start, drop the database or remove the db.sqlite3 file.

### 5. Create a admin user

```
python manage.py createsuperuser
>>> Username: admin
>>> Email address: admin@example.com
>>> Password: **********
>>> Password (again): *********
>>> Superuser created successfully.
```

You should use a different username instead of admin to increase security.

### 6. Build frontend and collect static files

Build the Vue SPA into `site_static/dist/`, then copy all static assets (Bokeh, Font Awesome, SPA bundle, …) into `static/` for nginx:

```
cd frontend
npm ci
npm run build
cd ..
python manage.py collectstatic --noinput
```

Repeat **`npm run build`** and **`collectstatic`** on every deploy that changes the frontend. Node.js is only required at build time, not on the server at runtime (unless you build there).

### 7. Upgrading an existing installation

After `git pull` or a new release tarball:

```
pip install -r requirements.txt
python manage.py migrate
cd frontend && npm ci && npm run build && cd ..
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn_aots
sudo systemctl restart celery_aots celery_beat_aots   # if used
```

## Setup gunicorn

### 1. Create socket unit

```
sudo nano /etc/systemd/system/gunicorn_aots.socket
```

Add the following content to this file (adjust the path as needed):

```
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/home/aots/www/aots/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

### 2. Define the service file

```
sudo nano /etc/systemd/system/gunicorn_aots.service
```

Add the following content to this file:

```
[Unit]
Description=AOTS gunicorn daemon
Requires=gunicorn_aots.socket
After=network.target


[Service]
User=aots
Group=www-data
WorkingDirectory=/home/aots/www/aots/AOTS
ExecStart=/home/aots/www/aots/aotsenv/bin/gunicorn \
          --workers 3 \
          --timeout 600 \
          --access-logfile - \
          --error-logfile - \
          --capture-output \
          --log-level info \
          --bind unix:/home/aots/www/aots/run/gunicorn.sock \
          AOTS.wsgi:application
          
StandardOutput=journal
StandardError=journal
SyslogIdentifier=gunicorn_aots

[Install]
WantedBy=multi-user.target
```

Adjusts the directories and the user name as needed.

### 3. Start gunicorn and set it up to start at boot

```
sudo systemctl start gunicorn_aots.socket
sudo systemctl enable gunicorn_aots.socket
```

Check status of gunicorn with and the log files with:

```
sudo systemctl status gunicorn_aots.socket
sudo journalctl -u gunicorn_aots.socket
```

Check that a gunicorn.sock file is created:

```
ls /home/aots/www/aots/run/
>>> gunicorn.sock
```

When changes are made to the gunicorn.service file run:

```
sudo systemctl daemon-reload
sudo systemctl restart gunicorn_aots
```

Check status:

```
sudo systemctl status gunicorn_aots
```

## Configure NGNIX

Django returns the HTML shell for `/w/…`, `/api/…`, `/accounts/…`, etc.; nginx proxies those requests to Gunicorn. Built SPA assets live under `/static/dist/` and are served from the `static/` directory below.

```
sudo nano /etc/nginx/sites-available/aots
```

```
server {
    listen 80;
    server_name a15.astro.physik.uni-potsdam.de;

    location /favicon.ico {
        alias /home/aots/www/aots/AOTS/static/favicon.ico;
        access_log off;
        log_not_found off;
    }

    # collectstatic output (includes frontend/dist → static/dist/)
    location /static/ {
        root /home/aots/www/aots/AOTS;
    }

    location /media/ {
        root /home/aots/www/aots/AOTS;
    }

    # Django + SPA shell + REST API (Vue client-side routes must reach Gunicorn)
    location / {
        if (-f /var/www/aots/maintenance.on) {
            return 503;
        }
        include proxy_params;
        proxy_pass http://unix:/home/aots/www/aots/run/gunicorn.sock;
    }

    error_page 503 @maintenance;
    location @maintenance {
        root /var/www/aots;
        rewrite ^ /maintenance.html break;
        add_header Retry-After 300 always;
    }

}
```

Now, we can enable the file by linking it to the sites-enabled directory:

```
sudo ln -s /etc/nginx/sites-available/aots /etc/nginx/sites-enabled
```

Set the maximum body size for uploads by clients in the ngnix configuration file:

```
sudo nano /etc/nginx/nginx.conf
```

Add the following text in the http configuration block:

```
# set client body size to 10M #
client_max_body_size 10M;
```

Test for syntax errors:

```
sudo nginx -t
```

When there are no errors restart ngnix:

```
sudo systemctl restart nginx
```

Finally, we need to open up our firewall to normal traffic on port 80

```
sudo ufw allow 'Nginx Full'
```

## Maintenance mode (deployments)

During upgrades, nginx can serve a static maintenance page instead of proxying to Gunicorn.
The HTML file lives in the repo at `deploy/maintenance.html`.

**One-time setup on the server:**

```
sudo mkdir -p /var/www/aots
sudo cp deploy/maintenance.html /var/www/aots/maintenance.html
```

The nginx `location /` block above already checks for a flag file and returns HTTP 503 with that page.
After editing `/etc/nginx/sites-available/aots`, run `sudo nginx -t` and `sudo systemctl reload nginx`.

**Enable maintenance** (before `git pull`, migrations, frontend build, or Gunicorn restart):

```
sudo touch /var/www/aots/maintenance.on
```

**Disable maintenance** (after Gunicorn is back and you have smoke-tested):

```
sudo rm /var/www/aots/maintenance.on
```

Typical rollout with maintenance:

```
sudo touch /var/www/aots/maintenance.on
# … pip install, migrate, npm run build, collectstatic …
sudo systemctl restart gunicorn_aots
sudo systemctl restart celery_aots celery_beat_aots   # if used
curl -I -H "Host: a15.astro.physik.uni-potsdam.de" http://127.0.0.1/w/projects/
sudo rm /var/www/aots/maintenance.on
```

While maintenance is on, `/static/` and `/media/` are still served by nginx; only proxied routes (SPA, API, login) show the maintenance page.


## API authentication and bulk I/O

| Client | Authentication |
|--------|----------------|
| Browser (logged in) | Django **session cookie** after normal login |
| Scripts / automation | Headers `HTTP_PUBLICAPIKEY` and `HTTP_SECRETAPIKEY` (no extra session required) |

Bulk endpoints accept **either** session or API key. Headers: `Projectid`, `Staridlist`
(semicolon-separated PKs or star names; for `rawspecfiles`, raw-file PKs).

| Action | Endpoint |
|--------|----------|
| Start download (Celery) | `POST /api/observations/bulk-download/start/?kind=<kind>` |
| Poll task | `GET /api/observations/tasks/<task_id>/` |
| Download ZIP | `GET /api/observations/bulk-download/<task_id>/file/` |
| Upload + process async | `POST /api/observations/api-spec-upload/?async=1` |

Download `kind` query parameter:

| `kind` | Use case | `Staridlist` contains |
|--------|----------|------------------------|
| `processed` (default) | Processed spectra FITS from spectra list | Spectrum PKs or star names |
| `raw` | Raw calibration/exposure files for selected spectra | Spectrum PKs or star names |
| `rawspecfiles` | Raw file list page | RawSpecFile PKs |
| `lightcurves` | Light curve list page | LightCurve PKs |
| `analyses` | Analysis list page | Analysis PKs |

### Other API entry points

| Feature | Endpoint / command |
| --- | --- |
| Gaia DR3 (single star) | `POST /api/systems/stars/<pk>/gaia/fetch/` |
| Gaia DR3 (bulk, async) | `POST /api/systems/stars/gaia/fetch-bulk/?async=1` + header `Projectid` |
| Consensus policies | `/w/<project>/settings/consensus/` or `/api/analysis/consensus-policies/<slug>/` |
| Dashboard starmap | `/w/<project>/dash/` — interactive Bokeh map; PNG via plot save tool |
| Superuser admin (SPA) | `/admin/` (`/api/admin/`, requires `is_superuser`; Django `/admin/` remains as fallback) |

Domain models, service layers, I/O conventions, and one-time migration notes:
[docs/architecture.md](docs/architecture.md).

List API field contracts: [docs/api_list_contract.md](docs/api_list_contract.md).

## Redis and background tasks (Celery)

The codebase includes **Celery** and **Redis** configuration (`AOTS/celery.py`, `CELERY_*` in
settings). Redis is the message broker and result backend.

**Bulk downloads** in the UI (spectra, raw files, light curves, analyses) always use Celery
(`POST /api/observations/bulk-download/start/`). Opt-in FITS/spectrum **processing** uses
`?async=1` on process endpoints.

Without Redis and a Celery worker, bulk downloads from list pages will not work
(unless `CELERY_TASK_ALWAYS_EAGER=True` for local development).

### When is Redis required?

| Mode | Redis | Celery worker |
|------|-------|---------------|
| Sync process URLs (no `?async=1`) | No | No |
| Opt-in async processing (`?async=1` on process URLs) | Yes | Yes |
| Bulk ZIP downloads (spectra/raw lists, bulk API) | Yes | Yes |
| Tests / CI (`CELERY_TASK_ALWAYS_EAGER=True`) | No | No |

Examples of optional async endpoints:

- `POST /api/observations/specfiles/<pk>/process/?async=1`
- `POST /api/observations/spectra/<pk>/process/?async=1`
- `GET /api/observations/tasks/<task_id>/` — poll task status

Without Redis, keep using process URLs **without** `?async=1`. For bulk downloads during local
development, set `CELERY_TASK_ALWAYS_EAGER=True` so tasks run inside Django/Gunicorn.

### Install Redis (Linux)

The Python package `redis` in `requirements.txt` is only the client. You also need a
**Redis server** for async mode:

```
sudo apt install redis-server
sudo systemctl enable --now redis-server
redis-cli ping
```

Expected response: `PONG`.

### Configuration (`.env`)

Copy and extend `AOTS/.env` from `AOTS/.env.example`. Relevant variables:

```
CELERY_BROKER_URL=redis://localhost:6379/0
# Optional; defaults to CELERY_BROKER_URL if omitted:
# CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

For a password-protected Redis instance (recommended in production):

```
CELERY_BROKER_URL=redis://:your_redis_password@localhost:6379/0
```

**Development without Redis:** run tasks in-process (no separate worker):

```
CELERY_TASK_ALWAYS_EAGER=True
```

Settings are loaded from `AOTS/settings/base.py` (`CELERY_*` variables).

### Start a Celery worker

Use the same virtualenv and `.env` as Django. From the project root (`AOTS/`):

```
export DJANGO_ENV=development   # or production
celery -A AOTS worker -l info
```

In another terminal, start Django as usual (`runserver` or Gunicorn). The worker must be able to
reach the same Redis URL as Django.

### Production notes

- Run Redis on `localhost` only (or a private network); do not expose it to the internet.
- Set `requirepass` in `/etc/redis/redis.conf` and use it in `CELERY_BROKER_URL`.
- Run the Celery worker as a **systemd service** alongside Gunicorn (same user, same
  `WorkingDirectory` and environment file).
- The existing Gunicorn timeout (600s) applies to **synchronous** requests; async jobs can run
  longer in the worker without blocking HTTP workers.

Example systemd unit (adjust paths and user):

```
sudo nano /etc/systemd/system/celery_aots.service
```

```
[Unit]
Description=AOTS Celery worker
After=network.target redis-server.service

[Service]
User=aots
Group=www-data
WorkingDirectory=/home/aots/www/aots/AOTS
EnvironmentFile=/home/aots/www/aots/AOTS/AOTS/.env
ExecStart=/home/aots/www/aots/aotsenv/bin/celery -A AOTS worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl daemon-reload
sudo systemctl enable --now celery_aots
sudo systemctl status celery_aots
```

### Celery Beat (scheduled maintenance)

When Celery Beat is enabled (`AOTS/celery.py`), these jobs run daily:

| Job | Default schedule | Purpose |
| --- | --- | --- |
| `cleanup-bulk-download-artifacts` | 03:30 | Remove expired ZIPs from `media/bulk_downloads/` |

Manual alternative:

```
python manage.py cleanup_bulk_downloads
```

Example Beat systemd unit:

```
sudo nano /etc/systemd/system/celery_beat_aots.service
```

```
[Unit]
Description=AOTS Celery beat
After=network.target redis-server.service

[Service]
User=aots
Group=www-data
WorkingDirectory=/home/aots/www/aots/AOTS
EnvironmentFile=/home/aots/www/aots/AOTS/AOTS/.env
ExecStart=/home/aots/www/aots/aotsenv/bin/celery -A AOTS beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl daemon-reload
sudo systemctl enable --now celery_beat_aots
```

Tune bulk-download TTL in `.env`:

```
BULK_DOWNLOAD_TTL_SECONDS=86400
BULK_DOWNLOAD_DELETE_AFTER_SEND=True
```

### Troubleshooting

| Problem | Likely cause |
|---------|----------------|
| `Connection refused` when using `?async=1` | Redis not running or wrong `CELERY_BROKER_URL` |
| Task stays `PENDING` | Celery worker not started |
| Works in tests but not locally | `CELERY_TASK_ALWAYS_EAGER=True` in test config only |
| `pip install redis` alone is not enough | Redis **server** not installed |