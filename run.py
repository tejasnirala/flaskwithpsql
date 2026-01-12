"""Application entry point."""

import os

from app import create_app

# Get configuration from environment or default to development
config_name = os.environ.get("FLASK_ENV", "development").strip().lower()
app = create_app(config_name)


if __name__ == "__main__":
    # Run the development server
    app.run(host="0.0.0.0", port=int(os.environ.get("FLASK_PORT", 5500)), debug=True)
