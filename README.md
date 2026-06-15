# AOTS

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

## Running AOTS locally

To run AOTS locally, using the simple sqlite database and the included server:

### 1. Setup the database

```
python manage.py makemigrations users
python manage.py makemigrations stars
python manage.py makemigrations observations
python manage.py makemigrations analysis
python manage.py makemigrations dash
python manage.py migrate
```

In case you want a fresh start, run:

```
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
```

and drop the database or remove the db.sqlite3 file.

### 2. Create a admin user

```
python manage.py createsuperuser
>>> Username: admin
>>> Email address: admin@example.com
>>> Password: **********
>>> Password (again): *********
>>> Superuser created successfully.
```

### 3. Start the development server

Set `DJANGO_ENV=development` in `AOTS/.env` (or export it in your shell).
Production deployments should use `DJANGO_ENV=production`.

```
python manage.py runserver
```


## Setup postgres database for production

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

## Running AOTS in production using a postgres database

Instructions modified
from: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04

### 1. Create an .env file

To protect secrets like the postgres database password or the Django security key they are embedded in AOTS via
environment variables. The environment variables are defined in the .env file in the AOTS directory. As an example we
provide .env.example.

```
cp AOTS/.env.example  AOTS/.env
```

### 2. Adjust the .env file

In .env the secret Django security key, the postgres database password, the server IP and URL, as well as the name of
the computer used in production needs to be specified.

```
SECRET_KEY=generate_and_add_your_secret_security_key_here
DJANGO_ENV=production
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

`DEVICE` is optional if `DJANGO_ENV=production` is set (legacy fallback: hostname match).
`CELERY_BROKER_URL` is optional for normal operation; Redis/Celery are **infrastructure
preparation** for later background work (see
[Redis and background tasks (Celery)](#redis-and-background-tasks-celery) and [TODO.md](TODO.md)).

Instructions on how to generate a secret key can be found
here: https://tech.serhatteker.com/post/2020-01/django-create-secret-key/

### 3. Setup the database

```
python manage.py migrate
```

In case you want a fresh start, drop the database or remove the db.sqlite3 file.

### 4. Create a admin user

```
python manage.py createsuperuser
>>> Username: admin
>>> Email address: admin@example.com
>>> Password: **********
>>> Password (again): *********
>>> Superuser created successfully.
```

You should use a different username instead of admin to increase security.

### 5. Collect static files

```
python manage.py collectstatic
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

    location /static/ {
        root /home/aots/www/aots/AOTS;
    }

    location /media/ {
      root /home/aots/www/aots/AOTS;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/aots/www/aots/run/gunicorn.sock;
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


## API authentication (bulk upload/download)

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

### Glossary: Analysis vs parameter source

| Concept | Model | Examples |
| --- | --- | --- |
| HDF5 analysis result | `Analysis` | RV solution, SED fit |
| External / catalog provenance | `ParameterSource` (`kind=catalog`) | Gaia DR3, manual entry |
| Project average container | `ParameterSource` (`kind=average`, `name='AVG'`) | per-project AVG row |

Parameters from HDF5 uploads link via `Parameter.analysis`. Catalog, script, and averaged parameters link via `Parameter.parameter_source` (including derived parameters on the project AVG source).

### Analysis app architecture

Use-cases live in `analysis/services/`; models hold schema and simple display helpers; `analysis/auxil/` holds stateless HDF5 and plotting I/O.

| Layer | Modules | Responsibility |
| --- | --- | --- |
| API / legacy views | `analysis/api/`, `analysis/views.py` | HTTP, permissions, serialization |
| Services | `analysis_ingestion`, `analysis_plotting`, `analysis_display`, `parameter_io`, `parameter_averaging`, `parameter_derivation`, `parameter_sources`, `analysis_history`, `analysis_upload` | Upload pipeline, plots, averages, derived params |

**Parameter writes** go through `analysis/services/parameter_io.py` (create/update/delete measurements, derived records, batch sync). Direct `Parameter.objects.create()` / `.save()` in the Django shell or ad-hoc scripts does **not** sync project averages or derived parameters — use `parameter_io` helpers instead.
| Models | `Analysis`, `ParameterSource`, `Parameter`, `DerivedParameter` | ORM schema, `__str__`, reference URLs |
| Auxil | `read_analyses`, `plot_analyses`, `plot_parameters`, `fileio` | Pure functions on files and arrays |

**Upload flow:** `ingest_analysis_file` validates HDF5, matches the star, creates `Parameter` rows, then `create_derived_parameters` when the analysis category defines derived fields.

**Deploy (migrations 0016–0020):** after `migrate`, run `python manage.py relocate_analysis_files` on staging/production (with media backup) to move existing files from `datasets/` to `analyses/`. Optional: `cleanup_orphan_analysis_sources` on PostgreSQL to remove leftover MTI parent `ParameterSource` rows.

See [docs/api_datatables_contract.md](docs/api_datatables_contract.md) for list API field contracts.

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

### Celery Beat (bulk ZIP TTL cleanup, optional)

Removes expired files from `media/bulk_downloads/` daily. Example unit:

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

Manual cleanup of ZIPs older than BULK_DOWNLOAD_TTL_SECONDS (default 24h):
```
python manage.py cleanup_bulk_downloads
```

Alternatively run cleanup from cron (e.g. daily).

Tune in `.env`:

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