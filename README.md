 
# BiMoT

## Instalation instructions

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
python manage.py makemigrations
python manage.py migrate
```

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
python manage collectstatic
```

### 3. start the development server
```
python manage.py runserver
```

## setup gunicorn

```
sudo nano /etc/systemd/system/gunicorn.service
```

```
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/home/joris/webapps/BiMoT
ExecStart=/home/joris/webapps/bimotenv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/joris/webapps/BiMoT/BiMoT.sock BiMoT.wsgi:application --log-level debug

[Install]
WantedBy=multi-user.target
```

start gunicorn and set it up to start at boot
```
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

check status of gunicorn with and the log files with:
```
sudo systemctl status gunicorn
sudo journalctl -u gunicorn
```
check that a BiMoT.sock file is created:
```
ls ~/webapps/BiMoT
>>> BiMoT.sock
```

When changes are made to the gunicorn.service file run:
```
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

## Configure NGNIX

```
sudo vi /etc/nginx/sites-available/BiMoT
```

```
server {
    listen 80;
    server_name 46.101.118.100;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/joris/webapps/BiMoT;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/joris/webapps/BiMoT/BiMoT.sock;
        #proxy_pass http://unix:/run/gunicorn.sock;
    }

}
```

Now, we can enable the file by linking it to the sites-enabled directory:
```
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled
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