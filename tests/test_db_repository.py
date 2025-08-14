import os
import sys
import sqlite3
import unittest

# Ensure src is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.db_repository import DBRepository


class TestDBRepository(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.repo = DBRepository(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_table_creation(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hosts'")
        self.assertIsNotNone(cursor.fetchone())

    def test_crud_operations(self):
        self.repo.add_host('1.1.1.1', 'up')
        host = self.repo.get_host_by_ip('1.1.1.1')
        self.assertIsNotNone(host)
        self.assertEqual(host['status'], 'up')

        updated = self.repo.update_host_status('1.1.1.1', 'down')
        self.assertTrue(updated)
        host = self.repo.get_host_by_ip('1.1.1.1')
        self.assertEqual(host['status'], 'down')

        deleted = self.repo.delete_host('1.1.1.1')
        self.assertTrue(deleted)
        self.assertIsNone(self.repo.get_host_by_ip('1.1.1.1'))

    def test_helper_query_get_hosts_by_status(self):
        self.repo.add_host('1.1.1.1', 'up')
        self.repo.add_host('2.2.2.2', 'down')
        self.repo.add_host('3.3.3.3', 'up')

        up_hosts = self.repo.get_hosts_by_status('up')
        ips = sorted([h['ip'] for h in up_hosts])
        self.assertEqual(ips, ['1.1.1.1', '3.3.3.3'])


if __name__ == '__main__':
    unittest.main()
