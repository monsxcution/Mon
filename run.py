from app import create_app
from app.database import init_database

# --- APPLICATION ---
app = create_app()

if __name__ == "__main__":
    init_database()  # Initialize the database before running the app
    app.run(host="0.0.0.0", port=5001, debug=True)
