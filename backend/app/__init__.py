from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import inspect, text
import os

load_dotenv()

login_manager = LoginManager()
db = SQLAlchemy()


def get_db():
    return db.session


def _ensure_runtime_schema():
    """Apply small, idempotent schema updates for existing deployments."""
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if 'cable_receiving' not in table_names:
        return

    columns = {column['name'] for column in inspector.get_columns('cable_receiving')}
    if 'storage_location' not in columns:
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE cable_receiving ADD COLUMN storage_location VARCHAR(255)"))


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///ticketing.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DATABASE_URL']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['AUTH_TOKEN_TTL_SECONDS'] = int(os.getenv('AUTH_TOKEN_TTL_SECONDS', '86400'))

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

    CORS(app)
    login_manager.init_app(app)
    db.init_app(app)

    # Register blueprints
    from app.routes import api
    app.register_blueprint(api, url_prefix='/api')

    with app.app_context():
        db.create_all()
        _ensure_runtime_schema()
        print('✅ SQL database initialized successfully')

    return app
