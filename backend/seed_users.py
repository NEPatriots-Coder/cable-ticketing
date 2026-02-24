#!/usr/bin/env python3
"""Seed the database with demo users for testing.

Existing demo users are updated in place so credentials remain deterministic.
"""

from app import create_app
from app.models import User
from app import db
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

app = create_app()

# Set to False if you only want to create missing users.
RESET_EXISTING = True

demo_users = [
    {
        'username': 'Lamar',
        'email': 'lwells@coreweave.com',
        'phone': '+17018663892',
        'password': 'demo123',
        'role': 'admin'
    },
    {
        'username': 'jmartinez',
        'email': 'jmartinez1@coreweave.com',
        'phone': '+17022188961',
        'password': 'demo123',
        'role': 'user'
    },
    {
        'username': 'johns',
        'email': 'jsauer@coreweave.com',
        'phone': '+19734192505',
        'password': 'demo123',
        'role': 'user'
    },
    {
        'username': 'myriad_user',
        'email': 'myriad_user@coreweave.com',
        'phone': '+12025555679',
        'password': 'cable123',
        'role': 'user'
    },
    {
        'username': 'tech_request',
        'email': 'dcttech_request@coreweave.com',
        'phone': '+12025555680',
        'password': 'Optic123',
        'role': 'user'
    },
]

with app.app_context():
    print("🌱 Seeding database with demo users...")

    for user_data in demo_users:
        # Check if user already exists by username first, then by email.
        # This avoids duplicate demo users when username/email drifted.
        existing = User.find_by_username(user_data['username']) or User.find_by_username_or_email(
            user_data['username'],
            user_data['email'],
        )
        if existing:
            if not RESET_EXISTING:
                print(f"  ⏭️  {user_data['username']} already exists, skipping")
                continue

            try:
                existing.username = user_data["username"]
                existing.email = user_data["email"]
                existing.phone = user_data["phone"]
                existing.role = user_data["role"]
                existing.password_hash = generate_password_hash(user_data["password"])
                db.session.commit()
            except IntegrityError as exc:
                db.session.rollback()
                print(f"  ❌ Failed to update {user_data['username']}: {exc}")
                continue
            print(f"  🔁 Updated {user_data['username']} ({user_data['email']})")
            continue

        # Create new user
        try:
            User.create(
                username=user_data['username'],
                email=user_data['email'],
                phone=user_data['phone'],
                password_hash=generate_password_hash(user_data['password']),
                role=user_data['role']
            )
        except IntegrityError as exc:
            db.session.rollback()
            print(f"  ❌ Failed to create {user_data['username']}: {exc}")
            continue
        print(f"  ✅ Created {user_data['username']} ({user_data['email']})")
    print("\n✨ Done! Demo users created.")
    print("\nLogin credentials:")
    for user_data in demo_users:
        print(f"  - {user_data['username']} / {user_data['password']}")
