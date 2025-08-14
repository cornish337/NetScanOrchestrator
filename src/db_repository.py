import sqlite3
from typing import Optional, List, Dict, Any


class DBRepository:
    """Simple repository for storing scan hosts in SQLite."""

    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection
        self._create_tables()

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    # CRUD operations
    def add_host(self, ip: str, status: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO hosts (ip, status) VALUES (?, ?)", (ip, status))
        self.conn.commit()
        return cursor.lastrowid

    def get_host_by_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, ip, status FROM hosts WHERE ip = ?", (ip,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "ip": row[1], "status": row[2]}
        return None

    def update_host_status(self, ip: str, status: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE hosts SET status = ? WHERE ip = ?", (status, ip))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_host(self, ip: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM hosts WHERE ip = ?", (ip,))
        self.conn.commit()
        return cursor.rowcount > 0

    # Helper queries
    def get_hosts_by_status(self, status: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, ip, status FROM hosts WHERE status = ?", (status,))
        rows = cursor.fetchall()
        return [{"id": r[0], "ip": r[1], "status": r[2]} for r in rows]

    def list_hosts(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, ip, status FROM hosts")
        rows = cursor.fetchall()
        return [{"id": r[0], "ip": r[1], "status": r[2]} for r in rows]
