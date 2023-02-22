# AOTS

## Installing Django

This will install AOTS using a python virtualenv to avoid conflicts with other packages.

### 1. Prerequisites

Create a directory where all files and the required Python modules can be placed:

```
mkdir www
mkdir aots
cd www/aots
```
For the rest of this guide, we will assume that these directories are located in the user's home directory.

You need the python-dev package and virtualenv. Moreover you should update pip:

```
sudo apt-get install python-dev-is-python3
pip install -U pip
pip install virtualenv
```

### 2. Create the virtual environment

Create a new virtual python environment for AOTS and activate it (Bash syntax):

```
virtualenv aotsenv
source aotsenv/bin/activate
```

On Windows Computers do

```
virtualenv aotsenv
aotsenv\Scripts\Activate
```

If this fails with an error similar to: Error: unsupported locale setting do:

```
export LC_ALL=C
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

To protect secrets like the postgres database password or the Django security key they are embedded in AOTS via environment variables. The environment variables are defined in the .env file in the AOTS directory. As an example we provide .env.example.

```
cp AOTS/.env.example  AOTS/.env
```

### 2. Adjust the .env file

In .env the secret Django security key, the postgres database password, the server IP and URL, as well as the name of the computer used in production needs to be specified. If a special log directory is required or a different database user was defined during setup, this has to be specified here as well.

```
SECRET_KEY=generate_and_add_your_secret_security_key_here
DATABASE_NAME=aotsdb
DATABASE_USER=aotsuser
DATABASE_PASSWORD=your_database_password
DATABASE_HOST=localhost
DATABASE_PORT=
DEVICE=the_name_of_your_device_used_in_production
ALLOWED_HOSTS=server_url,server_ip,localhost
LOG_DIR=/home/aots/www/aots/AOTS/logs/
```

Instructions on how to generate a secret key can be found
here: https://tech.serhatteker.com/post/2020-01/django-create-secret-key/

### 3. Setup the database

```
python manage.py makemigrations users
python manage.py makemigrations stars
python manage.py makemigrations observations
python manage.py makemigrations analysis
python manage.py migrate
```

In case you want a fresh start, run:

```
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
```

and drop the database or remove the db.sqlite3 file.

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
          --access-logfile - \
          --workers 3 \
          --timeout 600 \
          --error-logfile /home/aots/www/aots/AOTS/logs/gunicorn_error.log \
          --capture-output \
          --log-level info \
          --bind unix:/home/aots/www/aots/run/gunicorn.sock \
          AOTS.wsgi:application

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

## Setup logroate

To enable log rotation create a file with the following content /etc/logrotate.d:

```
/home/aots/www/aots/AOTS/logs/*.log {
  rotate 14
  daily
  compress
  delaycompress
  nocreate
  notifempty
  missingok
  su aots www-data
}
```

Change user name, group, and the log directory as needed.

Alternatively, 'logging.handlers.RotatingFileHandler' can be selected as class for the logging handlers in
settings_production.py.

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
