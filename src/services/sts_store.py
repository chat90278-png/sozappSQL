from __future__ import annotations
import json, getpass
from contextlib import contextmanager
from pathlib import Path
from src.models.app_models import ComponentDef, ContractInfo, SystemInfo, DeliveryInfo, TagDef
from src.services.sts_database import STSDatabase

class STSStore:
    def __init__(self, path: Path):
        self.path = Path(path); self.db = STSDatabase(self.path); self.db.init_schema(); self.wb=None
    def _normalize_label(self, s:str)->str: return str(s or "").strip().lower()
    def current_actor(self): return getpass.getuser()
    def save(self): return True
    def reload_from_disk(self): self.db.close(); self.db.connect(); return True
    @contextmanager
    def batch_save(self): yield self
    def flush_pending_styles(self): return None
    def rebuild_platform_headers(self,*a,**k): return None
    def style_platform_rows(self,*a,**k): return None
    def platform_names(self):
        rows=self.db.connect().execute("SELECT name FROM platforms WHERE is_active=1 ORDER BY sort_order,name").fetchall(); return [r[0] for r in rows]
    def all_sheet_names(self): return self.platform_names()
    def create_platform(self,name,logo_source=None):
        self.db.connect().execute("INSERT OR IGNORE INTO platforms(name,display_name) VALUES(?,?)",(name,name)); self.db.conn.commit(); return name
    def delete_platform(self,name): self.db.connect().execute("DELETE FROM platforms WHERE name=?",(name,)); self.db.conn.commit(); return True
    def load_excluded_platforms(self):
        return [r[0] for r in self.db.connect().execute("SELECT name FROM platforms WHERE is_excluded=1").fetchall()]
    def save_excluded_platforms(self, excluded):
        con=self.db.connect(); con.execute("UPDATE platforms SET is_excluded=0");
        for n in excluded or []: con.execute("UPDATE platforms SET is_excluded=1 WHERE name=?", (n,)); con.commit()
    def get_platform_logo_bytes(self, platform):
        r=self.db.connect().execute("SELECT logo_blob FROM platforms WHERE name=?",(platform,)).fetchone(); return r[0] if r else None
    def set_platform_logo_bytes(self, platform,data,ext=None): self.db.connect().execute("UPDATE platforms SET logo_blob=?, logo_ext=? WHERE name=?",(data,ext,platform)); self.db.conn.commit()
    def load_users(self, active_only=True):
        q="SELECT name,yi_yd,active,note FROM users" + (" WHERE active=1" if active_only else "")
        return [{"name":r[0],"yi_yd":r[1] or "Yİ","active":bool(r[2]),"note":r[3] or ""} for r in self.db.connect().execute(q)]
    def write_users(self, users_payload, actor=None):
        con=self.db.connect(); con.execute("DELETE FROM users")
        for u in users_payload or []: con.execute("INSERT INTO users(name,yi_yd,active,note) VALUES(?,?,?,?)", (u.get('name'),u.get('yi_yd','Yİ'),1 if u.get('active',True) else 0,u.get('note','')))
        con.commit(); return True
    def load_components(self):
        con=self.db.connect(); out=[]
        for r in con.execute("SELECT id,name,version,unit,active,usage FROM components ORDER BY name"):
            plats={x[0]:bool(x[1]) for x in con.execute("SELECT platform_name,enabled FROM component_platforms WHERE component_id=?", (r[0],))}
            out.append(ComponentDef(name=r[1],version=r[2] or "",unit=r[3] or "Adet",active=bool(r[4]),usage=float(r[5] or 1),platforms=plats))
        return out
    def write_components(self, components_payload, actor=None):
        con=self.db.connect(); con.execute("DELETE FROM component_platforms"); con.execute("DELETE FROM components")
        for c in components_payload or []:
            cobj = c if isinstance(c, ComponentDef) else ComponentDef(**c)
            cur=con.execute("INSERT INTO components(name,version,unit,active,usage) VALUES(?,?,?,?,?)", (cobj.name,cobj.version,cobj.unit,1 if cobj.active else 0,cobj.usage))
            cid=cur.lastrowid
            for p,e in (cobj.platforms or {}).items(): con.execute("INSERT INTO component_platforms(component_id,platform_name,enabled) VALUES(?,?,?)", (cid,p,1 if e else 0))
        con.commit(); return True
    def load_tags(self): return [TagDef(name=r[0],color=r[1] or "#3B82F6",kind=r[2] or "contract") for r in self.db.connect().execute("SELECT name,color,kind FROM tags ORDER BY name")]
    load_tag_defs=load_tags
    def write_tags(self,tags,actor=None):
        con=self.db.connect(); con.execute("DELETE FROM tags")
        for t in tags or []:
            to=t if isinstance(t,TagDef) else TagDef(**t); con.execute("INSERT INTO tags(name,color,kind) VALUES(?,?,?)", (to.name,to.color,to.kind))
        con.commit(); return True
    def load_tag_snapshot(self): return self.load_tags(), self.all_contract_tags_map()
    def write_tag_snapshot(self,tags,assignments_by_key,actor=None): self.write_tags(tags,actor); return True
    def all_contract_tags_map(self):
        q="SELECT c.platform,c.contract_no,c.contract_type,t.tag_name FROM contracts c LEFT JOIN contract_tags t ON c.id=t.contract_id"
        out={}
        for p,no,ct,tg in self.db.connect().execute(q):
            k=f"{p}|{no}|{ct}"; out.setdefault(k,[])
            if tg: out[k].append(tg)
        return out
    def _contract_id(self,p,no,ct):
        r=self.db.connect().execute("SELECT id FROM contracts WHERE platform=? AND contract_no=? AND contract_type=?",(p,no,ct)).fetchone(); return int(r[0]) if r else 0
    def load_contract_tags(self,p,no,ct):
        cid=self._contract_id(p,no,ct); return [r[0] for r in self.db.connect().execute("SELECT tag_name FROM contract_tags WHERE contract_id=?",(cid,))] if cid else []
    def save_contract_tags(self,p,no,ct,tags,actor=None):
        cid=self._contract_id(p,no,ct); con=self.db.connect(); con.execute("DELETE FROM contract_tags WHERE contract_id=?",(cid,));
        for t in tags or []: con.execute("INSERT OR IGNORE INTO contract_tags(contract_id,tag_name) VALUES(?,?)",(cid, t if isinstance(t,str) else t.get('name'))); con.commit()
    def build_contract_index(self):
        out=[]; tags=self.all_contract_tags_map()
        for r in self.db.connect().execute("SELECT * FROM contracts ORDER BY id DESC"):
            key=f"{r['platform']}|{r['contract_no']}|{r['contract_type']}"
            out.append({"id":r['id'],"row":r['id'],"platform":r['platform'],"no":r['contract_no'],"user":r['user_name'],"type":r['contract_type'],"type_display":r['type_display'],"link":r['link_type'],"status":r['status'],"completion_date":r['completion_date'],"content":r['content'] or r['note'] or "","is_main":bool(r['is_main']),"tags":tags.get(key,[]),"search":r['search_text'] or ""})
        return out
    def list_main_contracts(self,platform,tags_map=None): return [x for x in self.build_contract_index() if x['platform']==platform and x['is_main']]
    def find_main_contract_info(self,platform,contract_no):
        for x in self.list_main_contracts(platform):
            if self._normalize_label(x['no'])==self._normalize_label(contract_no): return {"row":x['row'],"block_start":x['row'],"block_end":x['row']}
        return None
    def next_sd_code(self,platform,contract_no): return f"{contract_no}-SD-{len(self.build_contract_index())+1:03d}"
    def load_contract_structure(self,platform,contract_no,start_row=None):
        q="SELECT * FROM contracts WHERE platform=? AND contract_no=?"+ (" AND id=?" if start_row else "") +" ORDER BY id DESC LIMIT 1"
        r=self.db.connect().execute(q,(platform,contract_no,*(([start_row] if start_row else [])))).fetchone()
        ci=ContractInfo(platform=r['platform'],no=r['contract_no'],user=r['user_name'] or "",yi_yd=r['yi_yd'] or "Yİ",contract_type=r['contract_type'] or "",type_display=r['type_display'] or "",link=r['link_type'] or "",status=r['status'] or "",completion_date=r['completion_date'] or "",content=r['content'] or "",note=r['note'] or "",entry_start_row=r['id'],contract_id=r['id'])
        systems=[]; deliveries={}
        for s in self.db.connect().execute("SELECT * FROM systems WHERE contract_id=? ORDER BY sort_order,id",(r['id'],)):
            comps={x[0]:float(x[1] or 0) for x in self.db.connect().execute("SELECT component_name,qty FROM system_components WHERE system_id=?",(s['id'],))}
            systems.append(SystemInfo(name=s['name'],status=s['status'] or "",completion_date=s['completion_date'] or "",acceptance_date=s['acceptance_date'] or "",note=s['note'] or "",components=comps))
        for d in self.db.connect().execute("SELECT * FROM deliveries WHERE contract_id=? ORDER BY sort_order,id",(r['id'],)):
            pl={x[0]:float(x[1] or 0) for x in self.db.connect().execute("SELECT component_name,planned FROM delivery_components WHERE delivery_id=?",(d['id'],))}
            dl={x[0]:float(x[1] or 0) for x in self.db.connect().execute("SELECT component_name,delivered FROM delivery_components WHERE delivery_id=?",(d['id'],))}
            deliveries.setdefault(d['system_name'],[]).append(DeliveryInfo(name=d['name'],status=d['status'] or "",acceptance_date=d['acceptance_date'] or "",note=d['note'] or "",planned=pl,delivered=dl))
        return ci, systems, deliveries
    def write_contract(self,ci,systems,deliveries,old_contract_no=None,old_start_row=None):
        con=self.db.connect(); cid=int(getattr(ci,'contract_id',0) or getattr(ci,'entry_start_row',0) or 0)
        vals=(ci.platform,ci.no,ci.user,ci.yi_yd,ci.contract_type,ci.type_display,ci.link,ci.status,ci.completion_date,ci.content,ci.note,1 if ci.is_main else 0,f"{ci.platform} {ci.no} {ci.user} {ci.content}")
        if cid and con.execute('SELECT 1 FROM contracts WHERE id=?',(cid,)).fetchone():
            con.execute("UPDATE contracts SET platform=?,contract_no=?,user_name=?,yi_yd=?,contract_type=?,type_display=?,link_type=?,status=?,completion_date=?,content=?,note=?,is_main=?,search_text=? WHERE id=?",(*vals,cid))
        else:
            cur=con.execute("INSERT OR REPLACE INTO contracts(platform,contract_no,user_name,yi_yd,contract_type,type_display,link_type,status,completion_date,content,note,is_main,search_text) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",vals); cid=cur.lastrowid
        con.execute("DELETE FROM systems WHERE contract_id=?",(cid,)); con.execute("DELETE FROM deliveries WHERE contract_id=?",(cid,))
        for i,s in enumerate(systems or []):
            cur=con.execute("INSERT INTO systems(contract_id,name,status,completion_date,acceptance_date,note,sort_order,payload_json) VALUES(?,?,?,?,?,?,?,?)",(cid,s.name,s.status,s.completion_date,s.acceptance_date,s.note,i,json.dumps({}))); sid=cur.lastrowid
            for cn,qt in (s.components or {}).items(): con.execute("INSERT INTO system_components(system_id,component_name,qty) VALUES(?,?,?)",(sid,cn,qt))
        for sys_name,items in (deliveries or {}).items():
            for i,d in enumerate(items or []):
                cur=con.execute("INSERT INTO deliveries(contract_id,system_name,name,status,acceptance_date,note,sort_order,payload_json) VALUES(?,?,?,?,?,?,?,?)",(cid,sys_name,d.name,d.status,d.acceptance_date,d.note,i,json.dumps({}))); did=cur.lastrowid
                for cn,pl in (d.planned or {}).items(): con.execute("INSERT INTO delivery_components(delivery_id,component_name,planned,delivered) VALUES(?,?,?,?)",(did,cn,pl,(d.delivered or {}).get(cn,0)))
        con.commit(); return cid
    def delete_contract(self,platform,contract_no,start_row=None,actor=None,progress_cb=None):
        cid = start_row or self._contract_id(platform,contract_no,self.find_main_contract_info(platform,contract_no) and 'Ana Sözleşme' or '')
        if not cid:
            r=self.db.connect().execute("SELECT id FROM contracts WHERE platform=? AND contract_no=? ORDER BY id DESC LIMIT 1",(platform,contract_no)).fetchone(); cid=int(r[0]) if r else 0
        con=self.db.connect(); con.execute("DELETE FROM contract_tags WHERE contract_id=?",(cid,)); con.execute("DELETE FROM systems WHERE contract_id=?",(cid,)); con.execute("DELETE FROM deliveries WHERE contract_id=?",(cid,)); con.execute("DELETE FROM contracts WHERE id=?",(cid,)); con.commit()
        return {"platform":platform,"contract_no":contract_no,"start_row":cid,"end_row":cid,"deleted_rows":1 if cid else 0}
