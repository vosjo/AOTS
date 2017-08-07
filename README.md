 
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

### 3. Clone BiMoT from github
```
git clone https://github.com/Alegria01/BiMoT.git
```

### 4. Install the requirements
```
cd BiMoT
pip install -r requirements.txt
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

### 3. start the development server
```
python manage.py runserver
```
