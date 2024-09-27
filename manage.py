from app import app  # Import your app instance
from models import db  # Import your db instance

# Create a script for setting up the database
with app.app_context():
    db.create_all()
    print("Database tables created!")
