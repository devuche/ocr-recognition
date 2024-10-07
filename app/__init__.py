from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from flask_cors import CORS
from flask_socketio import SocketIO
from flasgger import Swagger
# from .models import User

load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY')
# Set the SQLALCHEMY_DATABASE_URI configuration before initializing SQLAlchemy
username = os.environ.get('DBUSER')
password = os.environ.get('PASSWORD')
server = os.environ.get('SERVER')
database = os.environ.get('DATABASE')
port = os.environ.get('DBPORT')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://{username}:{password}@{server}:{port}/{database}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SWAGGER'] = {
    'title': 'Optical Character Recognition API',
    'description': 'Welcome to the Optical Character Recognition collection. This collection provides a comprehensive set of endpoints designed for upload, retrieval and summarization of documents. Powered by advanced natural language processing capabilities of GPT-4 and azure document intelligence, the API features an intelligent bot that enhances and summarizes user uploaded documents. Presented by Uchenna Nnamani, a software engineer with a passion for AI and machine learning.',
    'uiversion': 3,
    'version': '1.0.0'
}

# Initialize SQLAlchemy with the configured app
db = SQLAlchemy(app)
#CORS
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")
swagger = Swagger(app)

# Setup logging
file_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
file_handler.setLevel(logging.DEBUG)

# Create a handler that logs messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Set the format for logging
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def create_app():
    # Additional app setup
    from .views import views
    app.register_blueprint(views, url_prefix='/')

    create_database(app)

    return app

def create_database(app):
    with app.app_context():
        db.create_all()