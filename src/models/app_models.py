from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class ComponentDef:
    name: str
    version: str = ""
    unit: str = "Adet"
    active: bool = True
    usage: float = 1.0
    platforms: Dict[str, bool] = field(default_factory=dict)

@dataclass
class TagDef:
    name: str
    color: str = "#3B82F6"
    kind: str = "contract"

@dataclass
class ContractInfo:
    platform: str
    no: str
    user: str = ""
    yi_yd: str = "Yİ"
    contract_type: str = "Ana Sözleşme"
    type_display: str = ""
    link: str = ""
    status: str = ""
    signed_date: str = ""
    t0_date: str = ""
    t0_months: int = 0
    completion_date: str = ""
    acceptance_date: str = ""
    content: str = ""
    note: str = ""
    is_main: bool = True
    entry_start_row: int = 0
    contract_id: int = 0

@dataclass
class SystemInfo:
    name: str
    status: str = ""
    completion_date: str = ""
    acceptance_date: str = ""
    note: str = ""
    components: Dict[str, float] = field(default_factory=dict)

@dataclass
class DeliveryInfo:
    name: str
    status: str = ""
    acceptance_date: str = ""
    note: str = ""
    planned: Dict[str, float] = field(default_factory=dict)
    delivered: Dict[str, float] = field(default_factory=dict)
