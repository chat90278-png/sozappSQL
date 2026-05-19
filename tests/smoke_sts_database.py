import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path
from tempfile import TemporaryDirectory
from src.services.sts_database import STSDatabase

def main():
    with TemporaryDirectory() as d:
        p=Path(d)/'x.sts'; db=STSDatabase(p); db.create_new(); c=db.connect()
        c.execute("INSERT INTO platforms(name) VALUES('P1')")
        c.execute("INSERT INTO users(name) VALUES('U1')")
        c.execute("INSERT INTO components(name) VALUES('C1')")
        c.execute("INSERT INTO tags(name,color) VALUES('T1','#fff')")
        c.execute("INSERT INTO contracts(platform,contract_no,contract_type) VALUES('P1','001','Ana Sözleşme')")
        cid=c.execute("SELECT id FROM contracts").fetchone()[0]
        c.execute("INSERT INTO systems(contract_id,name) VALUES(?,?)",(cid,'SYS'))
        c.execute("INSERT INTO deliveries(contract_id,system_name,name) VALUES(?,?,?)",(cid,'SYS','D1'))
        db.conn.commit()
        assert c.execute("SELECT COUNT(*) FROM platforms").fetchone()[0]==1
        c.execute("DELETE FROM contracts WHERE id=?",(cid,)); db.conn.commit()
        assert c.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]==0
if __name__=='__main__': main(); print('ok')
