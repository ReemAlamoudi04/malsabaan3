"""Streamlit POC with server-side request storage and protected administration."""
from pathlib import Path
import re
import secrets
import time
import logging
import traceback
import streamlit as st
import streamlit.components.v1 as components
from storage import Store
from admin import show_admin

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Mohammed Al Sabaan | محمد السبعان", page_icon=str(ROOT / "website/assets/logo-mark.png"), layout="wide", initial_sidebar_state="collapsed")

def secret(key, default=''):
    try:
        return str(st.secrets.get(key, default))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default

@st.cache_resource
def storage():
    return Store(path=str(ROOT / 'data/preview.sqlite3'))

try:
    store = storage()
    phone = re.sub(r'[+\s()-]', '', secret('WHATSAPP_NUMBER'))
    if st.query_params.get('admin') == '1':
        show_admin(store, secret('ADMIN_PASSWORD'), phone)
        st.stop()
    contact = store.settings(phone)
except Exception as exc:
    # Log the exception type and code locations, without exception messages or
    # local variables that could contain consultation details or credentials.
    logging.getLogger(__name__).error(
        'Dashboard/service failure [%s]\n%s',
        type(exc).__name__, ''.join(traceback.format_tb(exc.__traceback__)),
    )
    # Do not expose database paths, records or credentials in the public app.
    st.error('The service is temporarily unavailable. Please try again shortly.')
    st.stop()

if not re.fullmatch(r'\d{8,15}', contact['whatsapp']):
    st.error('Set WHATSAPP_NUMBER in Streamlit Secrets before sharing this preview.')
    st.stop()

st.markdown('''<style>
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {display:none!important}
[data-testid="stMainBlockContainer"]{padding:0!important;max-width:100%!important}
[data-testid="stMain"]{overflow-y:auto!important;overflow-x:hidden!important}
[data-testid="stVerticalBlock"]{gap:0!important}
iframe[title$=".alsabaan_website"],iframe[title="alsabaan_website"]{width:100%!important;height:100dvh!important;border:0!important;display:block}
[data-testid="stCustomComponentV1"]{height:100dvh!important}
body{background:#183756}
</style>''', unsafe_allow_html=True)

if 'event_nonce' not in st.session_state:
    st.session_state.event_nonce = secrets.token_urlsafe(24)
website = components.declare_component('alsabaan_website', path=str(ROOT / 'website'))
event = website(contact=contact, nonce=st.session_state.event_nonce, receipt=st.session_state.get('receipt'), key='firm-website', default=None)
if isinstance(event, dict) and event.get('id') != st.session_state.get('last_event'):
    ident = event.get('id')
    if not isinstance(ident, str) or len(ident) > 40 or event.get('nonce') != st.session_state.event_nonce:
        st.stop()
    receipt = {'id': ident, 'ok': False}
    try:
        if event.get('kind') == 'visit':
            store.visit(event, secret('ANALYTICS_SALT', 'alsabaan-demo-anonymous-counts'))
        elif event.get('kind') == 'request':
            recent = [t for t in st.session_state.get('request_times', []) if time.time()-t < 600]
            if len(recent) >= 20:
                raise ValueError('Too many requests; please try again later.')
            store.request(event)
            st.session_state.request_times = recent + [time.time()]
        else:
            raise ValueError('Unsupported event')
        receipt['ok'] = True
    except Exception:
        receipt['error'] = 'We could not save the request. Check your details or try again shortly.'
    st.session_state.last_event = ident
    st.session_state.receipt = receipt
    st.rerun()
