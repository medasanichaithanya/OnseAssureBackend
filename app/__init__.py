# app/__init__.py

from flask import Flask
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, COLLECTION_NAME  # Import MONGO_URI from config.py
from flask_cors import CORS

app = Flask(__name__)

# Configure the app with settings from config.py
app.config['MONGO_URI'] = MONGO_URI
app.config['DB_NAME'] = DB_NAME
app.config['COLLECTION_NAME'] = COLLECTION_NAME

# Set up the MongoDB connection
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

# Initialize and configure CORS
cors = CORS(app, resources={r"*": {"origins": "http://localhost:5173"}})


# Import the routes
from app import routes
