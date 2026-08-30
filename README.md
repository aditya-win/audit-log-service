# Audit Log Service

A tamper-evident audit log service prototype.

## Development

```bash
# Setup virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run server
uvicorn app.main:app --reload
```