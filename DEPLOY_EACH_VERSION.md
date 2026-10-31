# Deploy the two saved designs separately

Saved on 31 October 2026. Neither app has been uploaded or deployed by this task.

| Saved version | What it contains | Standalone package |
|---|---|---|
| Current | Interactive Companies/Individuals explorer, three-link full-screen menu, no duplicate mobile bar | `current-streamlit.zip` |
| Previous alternative | Separate corporate and individual photo sections, five-link full-screen menu and mobile bar | `previous-streamlit.zip` |

Both keep the existing photos, logo, navy/bronze palette, hero film, Arabic/English content, consultation flow and admin dashboard. The older original design remains separately preserved in `../design-original/` and `../website/original.html`.

## Recommended: two separate GitHub repositories

This keeps the review apps independent from each other and from any existing client-review deployment. Do not replace your existing deployment or change its selected branch/entrypoint.

1. Unzip `current-streamlit.zip`. Create a new GitHub repository, for example `malsabaan-review-current`.
2. Upload the extracted **contents**, with `app.py`, `requirements.txt`, `admin.py`, `storage.py`, `website/`, and `.streamlit/config.toml` at the repository root. Keep `website/assets/` intact. GitHub deploys the extracted files, not the ZIP.
3. Open https://share.streamlit.io and choose **Create app**. Select this new repository, its branch (usually `main`) and main file **`app.py`**.
4. In **Advanced settings**, select **Python 3.11** and add the app's own Secrets:

```toml
WHATSAPP_NUMBER = "9665XXXXXXXX"
ADMIN_PASSWORD = "replace-with-your-own-unique-12-or-more-character-password"
ANALYTICS_SALT = "replace-with-a-different-random-value-for-each-app"
```

Replace the phone placeholder with digits only, including country code. `WHATSAPP_NUMBER` is required; `ADMIN_PASSWORD` is needed only for the admin dashboard. The values above are examples, not working credentials. Never upload `.streamlit/secrets.toml` to GitHub.

5. Deploy, and save the URL Streamlit assigns. You may request an available distinct subdomain, for example `malsabaan-current-review`.
6. Repeat steps 1–5 with `previous-streamlit.zip`, a second repository (for example `malsabaan-review-previous`) and another available URL.
7. Open each app's **Settings → Sharing** and select the intended access. Separate deployment URLs do not automatically make an app private.

Every app has its own secrets, request database, office settings, admin login and URL. Use `?admin=1` on that app's URL for its dashboard. Changing one repository or deploying it does not change the other. Local SQLite storage is demonstration storage and can reset on cloud restarts/redeployment; use test enquiries for review.

## Private client-review limit

Streamlit Community Cloud currently allows **one private app at a time**. If your existing client-review app already occupies that private slot, you cannot add these as two more private apps under the same allowance. Two separate public apps are possible, but they can be public and searchable; public links are not private review links. Keep the existing private app as it is unless you deliberately choose otherwise. If both new review URLs must be private simultaneously, use a hosting setup supporting multiple private Streamlit apps; do not make client content public merely to bypass the limit.

Official current documentation:

- Deployment fields, Python and Secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Private-app limit and Sharing settings: https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app
- Multiple app entrypoints in one repository: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization

## Alternative: one repository, two deployed apps

If you upload the containing `Malsabaan` repository rather than separate package contents, create two Streamlit apps with these main-file paths:

| App | Main file path |
|---|---|
| Current | `review_versions/current/app.py` |
| Previous alternative | `review_versions/previous/app.py` |

Each snapshot includes its own requirements, component assets and Python modules. The root `.streamlit/config.toml` supplies configuration when deploying from the containing repository. Set Secrets separately for each app. Each app has its own deployment runtime and storage. The one-private-app limit still applies. Separate repositories are simpler if you want independent future edits and sharing.

## Local preview

From inside either saved version's folder:

```sh
python -m pip install -r requirements.txt
cp secrets.example.toml .streamlit/secrets.toml
# Edit .streamlit/secrets.toml locally with your own values.
python -m streamlit run app.py
```

To run both at once, run the second from its folder in another terminal with `--server.port 8502`.

The saved packages contain no real secrets, enquiry database, analytics data or Git history. `VERSION.json` records the saved version and file hashes. Keep the ZIPs as dated snapshots; edit a working copy for later changes.
