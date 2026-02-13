#!/usr/bin/env python3
"""Seed the database with demo users for testing"""

from app import create_app
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

demo_users = [
    {
        'username': 'LZL01-ICS-LW',
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
        'username': 'bob_inventory',
        'email': 'bob@coreweave.com',
        'phone': '+12025555678',
        'password': 'demo123',
        'role': 'user'
    }
]

with app.app_context():
    print("🌱 Seeding database with demo users...")

    for user_data in demo_users:
        # Check if user already exists
        existing = User.find_by_username_or_email(user_data['username'], user_data['email'])
        if existing:
            print(f"  ⏭️  {user_data['username']} already exists, skipping")
            continue

        # Create new user
        User.create(
            username=user_data['username'],
            email=user_data['email'],
            phone=user_data['phone'],
            password_hash=generate_password_hash(user_data['password']),
            role=user_data['role']
        )
        print(f"  ✅ Created {user_data['username']} ({user_data['email']})")
    print("\n✨ Done! Demo users created.")
    print("\nLogin credentials (all use password: demo123):")
    for user_data in demo_users:
        print(f"  - {user_data['username']}")
