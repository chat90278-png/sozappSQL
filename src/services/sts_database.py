from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path

class STSDatabase:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.conn: sqlite3.Connection | None = None

    def connect(self):
        if self.conn:
            return self.conn
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close(); self.conn = None

    def create_new(self):
        self.connect(); self.init_schema()

    def init_schema(self):
        c = self.connect().cursor()
        ddl = """
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS platforms(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,display_name TEXT,is_active INTEGER DEFAULT 1,is_excluded INTEGER DEFAULT 0,logo_blob BLOB,logo_ext TEXT,sort_order INTEGER DEFAULT 0,created_at TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,yi_yd TEXT DEFAULT 'Yİ',active INTEGER DEFAULT 1,note TEXT,created_at TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS components(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,version TEXT,unit TEXT DEFAULT 'Adet',active INTEGER DEFAULT 1,usage REAL DEFAULT 1,payload_json TEXT,created_at TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS component_platforms(id INTEGER PRIMARY KEY AUTOINCREMENT,component_id INTEGER NOT NULL,platform_name TEXT NOT NULL,enabled INTEGER DEFAULT 1,UNIQUE(component_id, platform_name));
        CREATE TABLE IF NOT EXISTS tags(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,color TEXT,kind TEXT DEFAULT 'contract',created_at TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS contracts(id INTEGER PRIMARY KEY AUTOINCREMENT,platform TEXT NOT NULL,contract_no TEXT NOT NULL,user_name TEXT,yi_yd TEXT,contract_type TEXT,type_display TEXT,link_type TEXT,status TEXT,signed_date TEXT,t0_date TEXT,t0_months INTEGER,completion_date TEXT,acceptance_date TEXT,content TEXT,note TEXT,is_main INTEGER DEFAULT 1,parent_contract_id INTEGER,parent_contract_no TEXT,search_text TEXT,payload_json TEXT,created_at TEXT,updated_at TEXT,UNIQUE(platform, contract_no, contract_type));
        CREATE TABLE IF NOT EXISTS systems(id INTEGER PRIMARY KEY AUTOINCREMENT,contract_id INTEGER NOT NULL,name TEXT NOT NULL,status TEXT,completion_date TEXT,acceptance_date TEXT,note TEXT,sort_order INTEGER DEFAULT 0,payload_json TEXT);
        CREATE TABLE IF NOT EXISTS system_components(id INTEGER PRIMARY KEY AUTOINCREMENT,system_id INTEGER NOT NULL,component_name TEXT NOT NULL,qty REAL DEFAULT 0,UNIQUE(system_id, component_name));
        CREATE TABLE IF NOT EXISTS deliveries(id INTEGER PRIMARY KEY AUTOINCREMENT,contract_id INTEGER NOT NULL,system_id INTEGER,system_name TEXT NOT NULL,name TEXT NOT NULL,status TEXT,acceptance_date TEXT,note TEXT,sort_order INTEGER DEFAULT 0,payload_json TEXT);
        CREATE TABLE IF NOT EXISTS delivery_components(id INTEGER PRIMARY KEY AUTOINCREMENT,delivery_id INTEGER NOT NULL,component_name TEXT NOT NULL,planned REAL DEFAULT 0,delivered REAL DEFAULT 0,UNIQUE(delivery_id, component_name));
        CREATE TABLE IF NOT EXISTS contract_tags(id INTEGER PRIMARY KEY AUTOINCREMENT,contract_id INTEGER NOT NULL,tag_name TEXT NOT NULL,UNIQUE(contract_id, tag_name));
        CREATE TABLE IF NOT EXISTS activity_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,action TEXT,entity_type TEXT,entity_key TEXT,message TEXT,payload_json TEXT);
        CREATE INDEX IF NOT EXISTS idx_contracts_platform ON contracts(platform);
        CREATE INDEX IF NOT EXISTS idx_contracts_no ON contracts(contract_no);
        CREATE INDEX IF NOT EXISTS idx_contracts_platform_no ON contracts(platform, contract_no);
        CREATE INDEX IF NOT EXISTS idx_contracts_search ON contracts(search_text);
        CREATE INDEX IF NOT EXISTS idx_systems_contract ON systems(contract_id);
        CREATE INDEX IF NOT EXISTS idx_deliveries_contract ON deliveries(contract_id);
        CREATE INDEX IF NOT EXISTS idx_deliveries_system_name ON deliveries(system_name);
        CREATE INDEX IF NOT EXISTS idx_contract_tags_contract ON contract_tags(contract_id);
        CREATE INDEX IF NOT EXISTS idx_component_platforms_platform ON component_platforms(platform_name);
        CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at);
        """
        c.executescript(ddl); self.conn.commit()

    def get_meta(self, key, default=None):
        r = self.connect().execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return (r[0] if r else default)
    def set_meta(self,key,value):
        self.connect().execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key,str(value))); self.conn.commit()
    def add_log(self, action, entity_type, entity_key, message="", payload=None):
        ts = datetime.now(timezone.utc).isoformat()
        self.connect().execute("INSERT INTO activity_logs(created_at,action,entity_type,entity_key,message,payload_json) VALUES(?,?,?,?,?,?)", (ts,action,entity_type,entity_key,message,json.dumps(payload or {}, ensure_ascii=False))); self.conn.commit()
    def list_logs(self, limit=500):
        return [dict(r) for r in self.connect().execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()]
    def vacuum(self):
        self.connect().execute("VACUUM")
