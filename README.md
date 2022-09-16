# Project name
Gateway Unipos Test
## Author 
Nursulton Kholmatov


## Description
This project is a test version of the "Gateway Unipos" Service


The project is connected to HUMO and UzCard systems


## Installation
```
python3 -m pip install virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py runserver
```


## requirements
* Python 3.9.10
* mysql database
* nginx