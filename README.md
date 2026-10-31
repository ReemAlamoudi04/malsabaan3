# Mohammed Al Sabaan — previous design

Previous alternative: separate corporate/individual photo sections; full-screen five-link menu.

This is a standalone saved review app. Upload this folder’s CONTENTS to a separate GitHub repository and deploy `app.py` on Streamlit Community Cloud. Use Python 3.11 and add your own `WHATSAPP_NUMBER` in app Secrets. Optional `ADMIN_PASSWORD` (12+ characters) enables `?admin=1`. No real secrets, client records or analytics database are included.

Run locally from this folder: `python -m streamlit run app.py`. Copy secrets.example.toml to .streamlit/secrets.toml locally and replace the placeholders. Do not commit that file.

Each deployment uses its own local data/preview.sqlite3; cloud restarts can erase demo storage. Use test data for review. See DEPLOY_EACH_VERSION.md for full instructions and current private-app limits.
