import os
import sys
from datetime import datetime

# Aktivace podpory ANSI escape kódů pro Windows konzoli
if sys.platform == "win32":
    os.system("")


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Barvy textu (Bright ANSI)
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


def _format_time() -> str:
    """Vrací časovou značku v šedé barvě [HH:MM:SS]."""
    return f"{Colors.GRAY}[{datetime.now().strftime('%H:%M:%S')}]{Colors.RESET}"


def log_dm(action: str, detail: str = "") -> None:
    """Logování pro DM sekci (Tyrkysová / Azurová)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.CYAN}{Colors.BOLD}🛡️ [DM] {action}{Colors.RESET}{d}")


def log_arena(action: str, detail: str = "") -> None:
    """Logování pro události v bojové aréně (Červená / Zlatá)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.RED}{Colors.BOLD}⚔️ [ARÉNA] {action}{Colors.RESET}{d}")


def log_hp(action: str, detail: str = "") -> None:
    """Logování pro změny životů HP (Karmínová)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.MAGENTA}{Colors.BOLD}❤️ [HP] {action}{Colors.RESET}{d}")


def log_mob(action: str, detail: str = "") -> None:
    """Logování pro generování a správu monster (Fialová)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.MAGENTA}{Colors.BOLD}👾 [MONSTRUM] {action}{Colors.RESET}{d}")


def log_player(action: str, detail: str = "") -> None:
    """Logování pro akce hráčů a jejich postav (Zelená)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.GREEN}{Colors.BOLD}🧙 [HRÁČ] {action}{Colors.RESET}{d}")


def log_gold(action: str, detail: str = "") -> None:
    """Logování pro transakce se zlaťáky (Žlutá / Zlatá)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.YELLOW}{Colors.BOLD}💰 [ZLAŤÁKY] {action}{Colors.RESET}{d}")


def log_success(action: str, detail: str = "") -> None:
    """Logování pro úspěšně dokončené operace (Zelená)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.GREEN}{Colors.BOLD}✅ {action}{Colors.RESET}{d}")


def log_warning(action: str, detail: str = "") -> None:
    """Logování pro varování a neplatné vstupy (Žlutá)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.YELLOW}{Colors.BOLD}⚠️ [VAROVÁNÍ] {action}{Colors.RESET}{d}")


def log_error(action: str, detail: str = "") -> None:
    """Logování pro chyby a výjimky (Červená)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.RED}{Colors.BOLD}❌ [CHYBA] {action}{Colors.RESET}{d}")


def log_info(action: str, detail: str = "") -> None:
    """Logování pro obecné systémové zprávy (Modrá)."""
    d = f" {Colors.WHITE}{detail}{Colors.RESET}" if detail else ""
    print(f"{_format_time()} {Colors.BLUE}ℹ️ {action}{Colors.RESET}{d}")
