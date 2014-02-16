from ConfigParser import ConfigParser
from flask import Flask

import psycopg2
import os

path_root = os.path.dirname(os.path.abspath(__file__))

config = ConfigParser()
config.read('pysmium/config.ini')

app = Flask(__name__)

from pysmium.lib import db

db.init_db(config)

from pysmium.controllers import loadout
