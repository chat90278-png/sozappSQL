import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path
from tempfile import TemporaryDirectory
from src.services.sts_store import STSStore
from src.models.app_models import ComponentDef, ContractInfo, SystemInfo, DeliveryInfo, TagDef

def main():
  with TemporaryDirectory() as d:
    s=STSStore(Path(d)/'a.sts'); s.create_platform('P1'); assert 'P1' in s.platform_names(); s.all_sheet_names()
    s.write_users([{"name":"Ali","yi_yd":"Yİ","active":True,"note":"n"}]); assert s.load_users(active_only=False)
    s.write_components([ComponentDef(name='Comp',platforms={'P1':True})]); assert s.load_components()
    s.write_tag_snapshot([TagDef(name='Tag')],{}); s.load_tag_snapshot();
    ci=ContractInfo(platform='P1',no='001',contract_type='Ana Sözleşme',user='Ali')
    cid=s.write_contract(ci,[SystemInfo(name='SYS',components={'Comp':2})],{'SYS':[DeliveryInfo(name='D',planned={'Comp':2},delivered={'Comp':1})]})
    idx=s.build_contract_index(); assert idx and cid
    s.save_contract_tags('P1','001','Ana Sözleşme',['Tag']); assert s.load_contract_tags('P1','001','Ana Sözleşme')
    ci2,sys,dl=s.load_contract_structure('P1','001',start_row=cid); assert ci2.no=='001' and sys and dl
    s.load_excluded_platforms(); s.get_platform_logo_bytes('P1'); s.batch_save(); s.current_actor(); s.reload_from_disk()
    s.delete_contract('P1','001',start_row=cid)
if __name__=='__main__': main(); print('ok')
