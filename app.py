"""Entry point for the Loyalty Platform application."""
import os
from loyalty_platform import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
