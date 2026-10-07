"""Точка входа. Запускает локальный сервер NiceGUI и открывает интерфейс в браузере."""

import os
import socket
import sys
import tempfile
import traceback
from datetime import datetime
from multiprocessing import freeze_support

HOST = "127.0.0.1"   # только эта машина: не торчим в сеть и нет запроса брандмауэра


def _setup_log_file() -> None:
    """У exe, собранного с --windowed, нет консоли: sys.stdout/sys.stderr = None,
    и ошибок не видно. Тогда пишем всё в vptk.log рядом с программой.
    Если консоль есть (обычный запуск, PyCharm, exe без --windowed) — ничего
    не трогаем: вывод виден в консоли."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    candidates = [
        os.path.join(os.path.dirname(sys.executable), "vptk.log"),
        os.path.join(tempfile.gettempdir(), "vptk.log"),   # если папка только для чтения
    ]
    for path in candidates:
        try:
            stream = open(path, "a", encoding="utf-8", buffering=1)
        except OSError:
            continue
        sys.stdout = sys.stderr = stream
        print(f"\n===== запуск {datetime.now():%Y-%m-%d %H:%M:%S}, лог: {path} =====")
        return
    sys.stdout = sys.stderr = open(os.devnull, "w")   # писать некуда — не оставлять None


_setup_log_file()
freeze_support()

from nicegui import app, ui  # noqa: E402  (после настройки лога — намеренно)
from ui import build_ui  # noqa: E402


def _find_open_port(start: int = 8000, attempts: int = 100) -> int:
    """Первый свободный порт, начиная с 8000."""
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"Нет свободных портов в диапазоне {start}-{start + attempts - 1}")


def _log_environment() -> None:
    """Диагностика собранного exe: версии и наличие файлов NiceGUI внутри сборки
    (без них сервер отвечает 500 Internal Server Error)."""
    import platform
    from importlib import metadata
    from pathlib import Path

    import nicegui

    print("python  :", sys.version.replace("\n", " "))
    print("system  :", platform.platform())
    for pkg in ("nicegui", "numpy", "matplotlib", "scipy", "ezdxf"):
        try:
            print(f"{pkg:10}:", metadata.version(pkg))
        except Exception:
            print(f"{pkg:10}: версия недоступна")
    base = Path(nicegui.__file__).parent
    for rel in ("templates/index.html", "static"):
        print(f"nicegui/{rel}:", "есть" if (base / rel).exists() else "ОТСУТСТВУЕТ")


def _log_exception(e: Exception) -> None:
    print("--- исключение NiceGUI ---")
    traceback.print_exception(e)


if getattr(sys, "frozen", False):
    _log_environment()
app.on_exception(_log_exception)


@ui.page("/")
def index():
    """Страница строится при каждом открытии. Если в build_ui() случится
    ошибка, показываем её текст на странице (и пишем в лог), а не голый
    'Internal Server Error'."""
    try:
        build_ui()
    except Exception:
        tb = traceback.format_exc()
        print(tb)
        ui.label("Ошибка при построении интерфейса / UI build error").classes(
            "text-xl font-bold text-red-600")
        ui.label(tb).classes("whitespace-pre-wrap font-mono text-xs")


if __name__ in {"__main__", "__mp_main__"}:
    port = _find_open_port()
    print(f"[vptk] Интерфейс: http://{HOST}:{port}  (закрыть программу: кнопка «Выход» или Ctrl+C)")
    ui.run(
        title="Расчёт ВПТК",
        host=HOST,
        port=port,
        reload=False,
        show=True,        # сам откроет вкладку в браузере по умолчанию
    )

