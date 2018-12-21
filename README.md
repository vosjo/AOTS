 
# BiMoT

## Setup postgres

start postgres comand line
```
sudo -u postgres psql
```

connect to our database and list all tables:
```
\c bimotdb
\dt
```

## Instaling Django

This will install BiMoT using a python virtualenv to avoid conflicts with other packages.

### 1. Prerequisits

You need the python-dev package and virtualenv
```
sudo apt-get install python-dev
pip install virtualenv
```

### 2. Create the virtual environment

Create a new virtual python environment for BiMoT and activate it
```
virtualenv bimotenv
source bimotenv/bin/activate
```

if this fails with an error similar to: Error: unsupported locale setting
do:
```
export LC_ALL=C
```

### 3. Clone BiMoT from github
```
git clone https://github.com/Alegria01/BiMoT.git
```

### 4. Install the requirements
```
cd BiMoT
pip install -r requirements.txt
pip install django gunicorn psycopg2
```

## Running BiMoT

To run BiMoT localy, using the simple sqlite database and the included server:

### 1. setup the database
```
python manage.py makemigrations stars
python manage.py makemigrations spectra
python manage.py makemigrations analysis
python manage.py migrate
```

In case you want a fresh start, run:

```
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
```
and drop the database or remove the db.sqlite3 file

### 2. create a admin user
```
python manage.py createsuperuser
>>> Username: admin
>>> Email address: admin@example.com
>>> Password: **********
>>> Password (again): *********
>>> Superuser created successfully.
```

### 3. collect static files
```
python manage.py collectstatic
```

### 3. start the development server
```
python manage.py runserver
```

## setup gunicorn

### create socket

```
sudo nano /etc/systemd/system/gunicorn_aots.socket
```

```
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/home/aots/www/bimot/BiMoT/BiMoT/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

```
sudo nano /etc/systemd/system/gunicorn_aots.service
```

```
[Unit]
Description=AOTS gunicorn daemon
Requires=gunicorn_aots.socket
After=network.target


[Service]
User=aots
Group=www-data
WorkingDirectory=/home/aots/www/bimot/BiMoT
ExecStart=/home/aots/www/bimot/bimotenv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/home/aots/www/bimot/BiMoT/BiMoT/run/gunicorn.sock \
          BiMoT.wsgi:application

[Install]
WantedBy=multi-user.target
```

start gunicorn and set it up to start at boot
```
sudo systemctl start gunicorn_aots.socket
sudo systemctl enable gunicorn_aots.socket
```

check status of gunicorn with and the log files with:
```
sudo systemctl status gunicorn_aots.socket
sudo journalctl -u gunicorn_aots.socket
```
check that a gunicorn.sock file is created:
```
ls /home/aots/www/bimot/BiMoT/BiMoT/run/
>>> gunicorn.sock
```

When changes are made to the gunicorn.service file run:
```
sudo systemctl daemon-reload
sudo systemctl restart gunicorn_aots
```

check status
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

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/aots/www/bimot/BiMoT;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/aots/www/bimot/BiMoT/BiMoT/run/gunicorn.sock;
    }

}
```

Now, we can enable the file by linking it to the sites-enabled directory:
```
sudo ln -s /etc/nginx/sites-available/aots /etc/nginx/sites-enabled
```

test for syntax errors:
```
sudo nginx -t
```

when there are no errors restart ngnix
```
sudo systemctl restart nginx
```

Finally, we need to open up our firewall to normal traffic on port 80
```
sudo ufw allow 'Nginx Full'
```
