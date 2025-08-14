import os
import os
import subprocess
import sys
import tempfile
import sqlite3
import unittest


class TestResplitCLI(unittest.TestCase):
    def setUp(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        tmp_db = tempfile.NamedTemporaryFile(delete=False)
        tmp_db.close()
        self.db_path = tmp_db.name
        # Create temp file with multiple IPs
        tmp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        tmp_file.write('192.168.0.1\n192.168.0.2\n')
        tmp_file.close()
        self.input_file = tmp_file.name

    def tearDown(self):
        for path in [self.db_path, self.input_file]:
            if os.path.exists(path):
                os.unlink(path)

    def run_cli(self, *args):
        cmd = [
            sys.executable,
            '-m',
            'src.cli.main',
            '--db-path',
            self.db_path,
            *map(str, args),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"Command {' '.join(cmd)} failed with {result.stderr}")
        return result.stdout.strip()

    def test_resplit_creates_child_batches(self):
        # ingest and plan
        self.run_cli('ingest', self.input_file)
        run_id = int(self.run_cli('plan').split()[-1])
        # initial split to create single batch containing both targets
        self.run_cli('split', run_id, '--chunk-size', '2')
        # fetch parent batch id
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('SELECT id, parent_batch_id, strategy FROM batches')
        parent = cur.fetchone()
        self.assertIsNotNone(parent)
        parent_id, parent_parent_id, parent_strategy = parent
        self.assertIsNone(parent_parent_id)
        self.assertEqual(parent_strategy, 'initial')
        conn.close()
        # resplit parent batch into child batches of size 1
        self.run_cli('resplit', parent_id, '--chunk-size', '1')
        # verify child batches
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('SELECT id, parent_batch_id, strategy FROM batches WHERE parent_batch_id = ?', (parent_id,))
        children = cur.fetchall()
        self.assertEqual(len(children), 2)
        for child in children:
            self.assertEqual(child[1], parent_id)
            self.assertEqual(child[2], 'resplit')
        conn.close()


if __name__ == '__main__':
    unittest.main()
