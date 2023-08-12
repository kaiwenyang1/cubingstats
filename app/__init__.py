from flask import Flask
from flask_mysqldb import MySQL
import os

app = Flask(__name__)

# Configuration details for MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USERNAME')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = 'wca'

mysql = MySQL(app)

from app import views
