# TestLoyality

A Flask-based loyalty platform for managing members, tiers, activities, campaigns, rewards, and analytics.

## Prerequisites

- Python 3.10 or higher

## Getting Started

1. **Clone the repository**

   ```bash
   git clone https://github.com/jason-hyliu/TestLoyality.git
   cd TestLoyality
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python app.py
   ```

   The server starts at `http://localhost:5000`. The database (`loyalty.db`) and seed data are created automatically on first run.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `FLASK_DEBUG` | Set to `1` to enable debug mode | `0` |
| `SECRET_KEY` | Secret key for the Flask application | `dev-secret-key` |

## Running Tests

```bash
pytest
```