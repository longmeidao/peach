from dataclasses import dataclass
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PeachSettings:
    db_path: Path = Path(r"R:\Resources\Intake\ledger.db")
    page_path: Path = TOOLS_DIR / "rm-web.html"
    token: str = ""
    legacy_module_path: Path = TOOLS_DIR / "rm-web.py"
    docs_enabled: bool = False
