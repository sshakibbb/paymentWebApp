This is a web app made for internal use by various political campaigns around the Greater Toronto Area to manage volunteer shifts, hours, and honourarium. This project is led by Saihaan Syed and maintained by him and Shakib Ahmed. We used Flask to develop the the apps backend, Flask-SQLAlchemy as the ORM tool, and Jinja2 for the HTML. The app is deployed onto a private linode linux nginx server with gunicorn as the WSGI, and the MySQL database is on private linode MYSQL server.

## Contributors
- Saihaan Syed @Sai-Sy  
- Shakib Ahmed @sshakibbb  
  
## Code Copyright  
Yet to established  
  
## Technologies  
This is a flask app ran on a private server  
  
# Design and Style Patterns
### Naming Scheme
### Declaring Variables and Objects
    1. snake_case for spaces in EVERYTHIING not camelCase or kebab-case  
    2. UNLESS it's a class name, then use PascalCase
    3. Python type hinting is not very pythonic and adds more boiler plate code clutter, but it make working with heavily attributed objects much easier. USE THEM!
### Ingesting User Data
    Always .strip() any inputted strings

## Setting up for production  
Production Notes:  
```/paymentwebapp/production_notes```  
  
View section: Production Prep  
  
### Setting up configuration file  
- In class ```DevConfig```, update path for .env file  
- Ensure Git ignores local changes to the config file using the following command:  
    ```git update-index --assume-unchanged <path>``` where ```<path>``` represents the path to config.py  
  
## Useful Server Commands  
restart nginx:  `sudo systemctl restart nginx`  
restart gunicorn: `sudo supervisorctl reload`  
nginx config: `sudo nano /etc/nginx/sites-enabled/paymentwebapp`  
gunicorn config: `sudo nano /etc/supervisor/conf.d/paymentwebapp.conf`  
start venv: `~paymentwebapp$ sourve venv/bin/activate`
nginx logs: `sudo tail -n 5 -f /var/log/nginx/access.log`  
gunicorn and app logs: `sudo tail -n 5 -f /var/log/paymentwebapp/paymentwebapp.err.log`  
  
## Running Notes  
- Wipe Database using:  
```python  
mycursor.execute(f'DROP DATABASE {name};')  
mycursor.execute(f'CREATE DATABASE {name};')  
```
- Then run the app  
- Then create the database by running ```database_create_all_script()```  

## Migrations  
  
### Setting Up 
- CD into payment web app  
- Bash: ```export FLASK_APP=website``` 
- CMD: ```set FLASK_APP=website```  
    ```flask db init```
  
### Migrate  
```flask db migrate -m 'Message'```  
```flask db upgrade```  
  
## Url Prefix  
https://dlukes.github.io/flask-wsgi-url-prefix.html  
  
### Dependencies  
```
pip install python-dotenv  
pip install pymysql  
pip install flask  
pip install flask-wtf  
pip install Flask-Migrate  
pip install flask_login  
  
pip install sqlalchemy  
```
