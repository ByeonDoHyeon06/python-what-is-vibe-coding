from __future__ import annotations

import os
import sqlite3
from sqlite3 import Row
from typing import Iterable, Optional


class SQLiteDataStore:
    """Lightweight SQLite helper for persisting domain entities."""

    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                external_auth_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
                name TEXT PRIMARY KEY,
                vcpu INTEGER NOT NULL,
                memory_mb INTEGER NOT NULL,
                disk_gb INTEGER NOT NULL,
                location TEXT NOT NULL,
                proxmox_host_id TEXT,
                proxmox_node TEXT,
                description TEXT,
                template_vmid INTEGER,
                disk_storage TEXT,
                clone_mode TEXT DEFAULT 'full',
                price REAL,
                default_expire_days INTEGER
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS upgrades (
                name TEXT PRIMARY KEY,
                add_vcpu INTEGER DEFAULT 0,
                add_memory_mb INTEGER DEFAULT 0,
                add_disk_gb INTEGER DEFAULT 0,
                price REAL,
                description TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS proxmox_hosts (
                id TEXT PRIMARY KEY,
                api_url TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                realm TEXT NOT NULL,
                node TEXT,
                location TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS servers (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                plan TEXT NOT NULL,
                location TEXT NOT NULL,
                proxmox_host_id TEXT,
                proxmox_node TEXT,
                vcpu INTEGER,
                memory_mb INTEGER,
                disk_gb INTEGER,
                disk_storage TEXT,
                expire_in_days INTEGER,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                external_id TEXT,
                last_notified_at TEXT
            )
            """
        )
        self._ensure_column(
            cur,
            table="servers",
            column="expire_in_days",
            ddl="INTEGER",
        )
        self._ensure_column(
            cur,
            table="plans",
            column="clone_mode",
            ddl="TEXT DEFAULT 'full'",
        )
        self._ensure_column(cur, table="plans", column="price", ddl="REAL")
        self._ensure_column(
            cur,
            table="plans",
            column="default_expire_days",
            ddl="INTEGER",
        )
        self._ensure_column(cur, table="servers", column="disk_storage", ddl="TEXT")
        self._ensure_column(
            cur, table="servers", column="last_notified_at", ddl="TEXT"
        )
        self.conn.commit()

    @staticmethod
    def _ensure_column(cur: sqlite3.Cursor, table: str, column: str, ddl: str) -> None:
        cur.execute(f"PRAGMA table_info({table})")
        columns = {row[1] for row in cur.fetchall()}
        if column not in columns:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    def execute(self, query: str, params: Iterable | tuple = ()) -> None:
        self.conn.execute(query, params)
        self.conn.commit()

    def fetch_one(self, query: str, params: Iterable | tuple = ()) -> Optional[Row]:
        cur = self.conn.execute(query, params)
        return cur.fetchone()

    def fetch_all(self, query: str, params: Iterable | tuple = ()) -> list[Row]:
        cur = self.conn.execute(query, params)
        return cur.fetchall()
