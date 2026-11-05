"""Validated storage for requests, anonymous browser visits and office settings."""
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
import base64
import binascii
import hashlib
import hmac
import json
import re
import sqlite3
import uuid
from urllib.parse import urlparse

DEFAULTS = {"whatsapp": "", "address_ar": "الرياض، المملكة العربية السعودية", "address_en": "Riyadh, Saudi Arabia", "latitude": 25.0048611, "longitude": 46.6021667, "maps_url": "https://maps.app.goo.gl/cBHxwKfLqGYcoLCr8", "hours_ar": "الأحد – الخميس، ٩ صباحًا – ٥ مساءً", "hours_en": "Sunday–Thursday, 9am–5pm"}

MAX_ATTACHMENTS = 3
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
ZIP_SIGNATURE = b'PK\x03\x04'
ATTACHMENT_SIGNATURES = {
    'pdf': (b'%PDF-',),
    'png': (b'\x89PNG\r\n\x1a\n',),
    'jpg': (b'\xff\xd8\xff',),
    'jpeg': (b'\xff\xd8\xff',),
    'doc': (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',),
    'docx': (ZIP_SIGNATURE,),
}

def now():
    return datetime.now(timezone.utc).isoformat()

def valid_id(value):
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Invalid request identifier")

def text(value, limit, required=False):
    if not isinstance(value, str):
        raise ValueError("Invalid text field")
    value = value.strip()
    if len(value) > limit or (required and not value):
        raise ValueError("Missing or oversized field")
    return value

def attachment(item):
    if not isinstance(item, dict):
        raise ValueError('Invalid attachment')
    name = re.sub(r'[\x00-\x1f\x7f/\\\\]', '_', text(item.get('name', ''), 200, True))
    extension = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if extension not in ATTACHMENT_SIGNATURES:
        raise ValueError('Unsupported attachment type')
    encoded = item.get('data')
    if not isinstance(encoded, str) or len(encoded) > (MAX_ATTACHMENT_BYTES + 2) // 3 * 4:
        raise ValueError('Attachment too large')
    try:
        content = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError('Invalid attachment')
    if not content or len(content) > MAX_ATTACHMENT_BYTES:
        raise ValueError('Attachment too large')
    if not content.startswith(ATTACHMENT_SIGNATURES[extension]):
        raise ValueError('Attachment content does not match its type')
    return name, content

def validate_settings(data):
    result = {k: data.get(k, v) for k, v in DEFAULTS.items()}
    result['whatsapp'] = re.sub(r'[+\s()-]', '', str(result['whatsapp']))
    if not re.fullmatch(r'\d{8,15}', result['whatsapp']):
        raise ValueError('Enter a phone number including its country code.')
    for field in ['address_ar', 'address_en', 'hours_ar', 'hours_en']:
        result[field] = text(result[field], 300, True)
    for field, bound in [('latitude', 90), ('longitude', 180)]:
        result[field] = float(result[field])
        if not -bound <= result[field] <= bound:
            raise ValueError('Invalid map coordinates.')
    result['maps_url'] = text(result['maps_url'], 1000)
    parsed = urlparse(result['maps_url'])
    if parsed.scheme != 'https' or parsed.hostname not in ['maps.app.goo.gl', 'maps.google.com', 'www.google.com', 'google.com']:
        raise ValueError('Use an HTTPS Google Maps link.')
    return result

class Store:
    def __init__(self, path='data/preview.sqlite3'):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def run(self, conn, sql, params=()):
        return conn.execute(sql, params)

    def initialize(self):
        with self.connection() as c:
            for sql in [
                'CREATE TABLE IF NOT EXISTS consultations (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN (\'open\',\'closed\')), source TEXT NOT NULL, language TEXT NOT NULL, service TEXT NOT NULL, name TEXT NOT NULL, mobile TEXT NOT NULL, email TEXT NOT NULL, details TEXT NOT NULL, notes TEXT NOT NULL DEFAULT \'\')',
                'CREATE TABLE IF NOT EXISTS visits (id TEXT PRIMARY KEY, visitor_hash TEXT NOT NULL, created_at TEXT NOT NULL)',
                'CREATE TABLE IF NOT EXISTS office_settings (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)',
                'CREATE TABLE IF NOT EXISTS login_attempts (id TEXT PRIMARY KEY, created_at TEXT NOT NULL)',
                'CREATE TABLE IF NOT EXISTS attachments (id TEXT PRIMARY KEY, consultation_id TEXT NOT NULL REFERENCES consultations(id), created_at TEXT NOT NULL, filename TEXT NOT NULL, content BLOB NOT NULL)',
                'CREATE INDEX IF NOT EXISTS attachments_consultation ON attachments(consultation_id)',
                'CREATE INDEX IF NOT EXISTS consultations_created ON consultations(created_at)',
                'CREATE INDEX IF NOT EXISTS visits_created ON visits(created_at)',
            ]:
                self.run(c, sql)
            if 'subject' not in [row['name'] for row in self.run(c, 'PRAGMA table_info(consultations)')]:
                self.run(c, "ALTER TABLE consultations ADD COLUMN subject TEXT NOT NULL DEFAULT ''")

    def settings(self, phone=''):
        with self.connection() as c:
            row = self.run(c, 'SELECT payload FROM office_settings WHERE id=1').fetchone()
        return {**DEFAULTS, 'whatsapp': phone, **(json.loads(row['payload']) if row else {})}

    def save_settings(self, data):
        payload = json.dumps(validate_settings(data), ensure_ascii=False)
        with self.connection() as c:
            self.run(c, 'INSERT INTO office_settings(id,payload) VALUES (1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload', (payload,))

    def visit(self, event, secret):
        event_id = valid_id(event['id'])
        visitor = valid_id(event['visitor'])
        digest = hmac.new(secret.encode(), visitor.encode(), hashlib.sha256).hexdigest()
        with self.connection() as c:
            self.run(c, 'INSERT INTO visits(id,visitor_hash,created_at) VALUES (?,?,?) ON CONFLICT(id) DO NOTHING', (event_id, digest, now()))

    def request(self, event):
        ident = valid_id(event['id'])
        source = event.get('source')
        if source not in ['form', 'whatsapp'] or event.get('language') not in ['ar', 'en']:
            raise ValueError('Invalid request type')
        service = text(event.get('service', ''), 200)
        name = text(event.get('name', ''), 120, source == 'form')
        mobile = text(event.get('mobile', ''), 30, source == 'form')
        email = text(event.get('email', ''), 254)
        subject = text(event.get('subject', ''), 200, source == 'form')
        details = text(event.get('details', ''), 4000, source == 'form')
        files = event.get('attachments', [])
        if not isinstance(files, list) or len(files) > MAX_ATTACHMENTS or (files and source != 'form'):
            raise ValueError('Invalid attachments')
        files = [attachment(item) for item in files]
        if source == 'form':
            if event.get('consent') is not True or len(name) < 2:
                raise ValueError('Your consent and name are required.')
            if not re.fullmatch(r'(?:0?5\d{8}|(?:\+?966)5\d{8})', mobile):
                raise ValueError('Invalid Saudi mobile number.')
            if not service or not re.fullmatch(r'[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+', email):
                raise ValueError('Invalid service or email.')
        timestamp = now()
        with self.connection() as c:
            inserted = self.run(c, 'INSERT INTO consultations(id,created_at,updated_at,status,source,language,service,name,mobile,email,subject,details,notes) VALUES (?,?,?,\'open\',?,?,?,?,?,?,?,?,\'\') ON CONFLICT(id) DO NOTHING', (ident, timestamp, timestamp, source, event['language'], service, name, mobile, email, subject, details)).rowcount
            for filename, content in files if inserted else []:
                self.run(c, 'INSERT INTO attachments(id,consultation_id,created_at,filename,content) VALUES (?,?,?,?,?)', (str(uuid.uuid4()), ident, timestamp, filename, content))
        return ident

    def attachments(self, ident):
        with self.connection() as c:
            return [dict(row) for row in self.run(c, 'SELECT id,filename,content FROM attachments WHERE consultation_id=? ORDER BY created_at,filename', (valid_id(ident),)).fetchall()]

    def requests(self):
        with self.connection() as c:
            return [dict(row) for row in self.run(c, 'SELECT * FROM consultations ORDER BY created_at DESC').fetchall()]

    def update_request(self, ident, status, notes):
        if status not in ['open', 'closed']:
            raise ValueError('Invalid status')
        with self.connection() as c:
            self.run(c, 'UPDATE consultations SET status=?,notes=?,updated_at=? WHERE id=?', (status, text(notes, 5000), now(), valid_id(ident)))

    def metrics(self):
        with self.connection() as c:
            counts = dict(self.run(c, "SELECT COUNT(*) AS total, COALESCE(SUM(CASE WHEN status='open' THEN 1 ELSE 0 END),0) AS open, COALESCE(SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END),0) AS closed FROM consultations").fetchone())
            counts.update(dict(self.run(c, 'SELECT COUNT(*) AS visits, COUNT(DISTINCT visitor_hash) AS visitors FROM visits').fetchone()))
            counts['today'] = self.run(c, 'SELECT COUNT(*) AS n FROM visits WHERE created_at>=?', ((datetime.now(timezone(timedelta(hours=3))).replace(hour=0,minute=0,second=0,microsecond=0).astimezone(timezone.utc)).isoformat(),)).fetchone()['n']
            counts['daily'] = [dict(r) for r in self.run(c, "SELECT DATE(created_at,'+3 hours') AS day,COUNT(*) AS visits FROM visits GROUP BY DATE(created_at,'+3 hours') ORDER BY day DESC LIMIT 30").fetchall()]
        return counts

    def login_allowed(self):
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        with self.connection() as c:
            self.run(c, 'DELETE FROM login_attempts WHERE created_at<?', (cutoff,))
            return self.run(c, 'SELECT COUNT(*) AS n FROM login_attempts').fetchone()['n'] < 10

    def login_failed(self):
        with self.connection() as c:
            self.run(c, 'INSERT INTO login_attempts(id,created_at) VALUES (?,?)', (str(uuid.uuid4()),now()))

    def login_succeeded(self):
        with self.connection() as c:
            self.run(c, 'DELETE FROM login_attempts')
