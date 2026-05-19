from pathlib import Path
from src.services.sts_store import STSStore

class _Base:
    def __init__(self,path,*args,**kwargs): self.path=Path(path); self.args=args; self.kwargs=kwargs
    def _store(self): return STSStore(self.path) if self.path.suffix.lower()=='.sts' else STSStore(self.path)

class UserSaveWorker(_Base):
    def run(self):
        s=self._store(); s.write_users(self.args[0], actor=self.args[1] if len(self.args)>1 else None)
class ComponentSaveWorker(_Base):
    def run(self):
        s=self._store(); s.write_components(self.args[0], actor=self.args[1] if len(self.args)>1 else None)
class ContractSaveWorker(_Base):
    def run(self): pass
class ExcelLoadWorker(_Base):
    def run(self): pass
class AnalyzeDialog: ...
