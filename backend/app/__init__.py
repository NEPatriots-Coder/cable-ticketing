from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ticketing.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes import api
    app.register_blueprint(api, url_prefix='/api')

    # Create tables
    with app.app_context():
        db.create_all()

    return app
