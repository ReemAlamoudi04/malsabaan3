"""Password rotation must survive reopening storage and disable the old password."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage import Store


class AdminPasswordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / 'test.sqlite3')
        self.store = Store(self.path)
        self.bootstrap = 'initial-test-password'

    def test_bootstrap_requires_valid_secret(self):
        self.assertFalse(self.store.has_admin_password(''))
        self.assertFalse(self.store.verify_admin_password('', ''))
        self.assertTrue(self.store.verify_admin_password(self.bootstrap, self.bootstrap))
        self.assertFalse(self.store.verify_admin_password('wrong', self.bootstrap))

    def test_rotation_replaces_bootstrap_and_invalidates_sessions(self):
        before = self.store.admin_credential_version(self.bootstrap)
        self.store.change_admin_password(self.bootstrap, 'replacement-test-password', self.bootstrap)
        reopened = Store(self.path)
        self.assertNotEqual(before, reopened.admin_credential_version(self.bootstrap))
        self.assertFalse(reopened.verify_admin_password(self.bootstrap, self.bootstrap))
        self.assertTrue(reopened.verify_admin_password('replacement-test-password', self.bootstrap))
        self.assertTrue(reopened.verify_admin_password('replacement-test-password', ''))
        with reopened.connection() as c:
            row = c.execute('SELECT * FROM admin_credentials').fetchone()
            self.assertNotIn('replacement-test-password', str(dict(row)))

    def test_invalid_change_preserves_password_and_version(self):
        before = self.store.admin_credential_version(self.bootstrap)
        for current, new in [('wrong', 'replacement-test-password'), (self.bootstrap, 'short')]:
            with self.assertRaises(ValueError):
                self.store.change_admin_password(current, new, self.bootstrap)
        self.assertEqual(before, self.store.admin_credential_version(self.bootstrap))
        self.assertTrue(self.store.verify_admin_password(self.bootstrap, self.bootstrap))


if __name__ == '__main__':
    unittest.main()
