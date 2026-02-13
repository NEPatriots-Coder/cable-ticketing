from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from pymongo import ASCENDING, MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

login_manager = LoginManager()
mongo_client = None
mongo_db = None


def get_db():
    if mongo_db is None:
        raise RuntimeError("MongoDB is not initialized")
    return mongo_db

def create_app():
    global mongo_client, mongo_db

    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    app.config['MONGO_DB_NAME'] = os.getenv('MONGO_DB_NAME', 'ticketing')

    # Twilio Configuration
    app.config['TWILIO_ACCOUNT_SID'] = os.getenv('TWILIO_ACCOUNT_SID')
    app.config['TWILIO_AUTH_TOKEN'] = os.getenv('TWILIO_AUTH_TOKEN')
    app.config['TWILIO_PHONE_NUMBER'] = os.getenv('TWILIO_PHONE_NUMBER')

    # Email Configuration (Resend or SendGrid)
    app.config['RESEND_API_KEY'] = os.getenv('RESEND_API_KEY')
    app.config['SENDGRID_API_KEY'] = os.getenv('SENDGRID_API_KEY')
    app.config['SENDGRID_FROM_EMAIL'] = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@cabletickets.com')

    # AWS Configuration (for SNS SMS)
    app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
    app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
    app.config['AWS_REGION'] = os.getenv('AWS_REGION', 'us-east-1')

    # App URL for notification links
    app.config['APP_URL'] = os.getenv('APP_URL', 'http://localhost:3000')

    # Initialize MongoDB connection and indexes
    mongo_client = MongoClient(app.config['MONGO_URI'])
    mongo_db = mongo_client[app.config['MONGO_DB_NAME']]
    mongo_db.users.create_index([("id", ASCENDING)], unique=True)
    mongo_db.users.create_index([("username", ASCENDING)], unique=True)
    mongo_db.users.create_index([("email", ASCENDING)], unique=True)
    mongo_db.tickets.create_index([("id", ASCENDING)], unique=True)
    mongo_db.tickets.create_index([("approval_token", ASCENDING)], unique=True)
    mongo_db.notifications.create_index([("id", ASCENDING)], unique=True)
    mongo_db.notifications.create_index([("ticket_id", ASCENDING)])
    mongo_db.notifications.create_index([("recipient_user_id", ASCENDING)])

    CORS(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes import api
    app.register_blueprint(api, url_prefix='/api')

    with app.app_context():
        print("✅ MongoDB initialized successfully")

    return app
