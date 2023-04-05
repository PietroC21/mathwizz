
from dotenv import find_dotenv, load_dotenv
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import find_dotenv, load_dotenv
from os import environ as env

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

DATABASE_URI=os.environ.get('DATABASE_URI')
db = SQLAlchemy()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
