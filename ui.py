"""Интерфейс на NiceGUI. Только UI, без формул. Два языка: RU / EN (см. localization.py)."""

import base64
import io
import os
import tempfile
from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.patches import Circle
from nicegui import app, ui

from core import (
    solve, MATERIAL_HINT, MATERIAL_HINT_EN,
    compute_profile, compute_balls,
    compute_separator, compute_eccentric,
    min_r_out_from_q_dtk,
    export_dxf,
    get_log, clear_log, export_log,
)
from local import DEFAULT_LANG, LANGUAGES, t


def build_ui():
    """Собирает интерфейс."""

    # Ключи совпадают с аргументами solve(): q, d, m_out, n, tau, kn, eta
    state = {
        "lang": DEFAULT_LANG,
        "q": None, "d": None, "m_out": None, "m_in": None,
        "n": 1,
        "body_type": "roller",
        "tau": 150.0,
        "kn": 0.56,
        "eta": 0.85,
        "use_gost": True,
        "log_fmt": "txt",
        "flags": {
            "profile": True,
            "separator": True,
            "eccentric": True,
            "balls": True,
            "out_diameter": False,
        },
    }

    # Ссылки на виджеты, которые пересоздаются при смене языка
    w = {}

    # ---------- Перевод ----------
    def tr(key, **kw):
        """Строка интерфейса на текущем языке."""
        return t(state["lang"], key, **kw)

    def tr_error(result):
        """Текст ошибки расчёта на текущем языке (по коду из solver)."""
        if result.error_key:
            return tr(result.error_key, **result.error_args)
        return result.error

    def run_solve():
        return solve(
            q=state["q"], d=state["d"], m_out=state["m_out"],
            m_in=state["m_in"],
            n=int(state["n"]), body_type=state["body_type"],
            tau=state["tau"], kn=state["kn"], eta=state["eta"],
            use_gost=state["use_gost"],
        )

    # ---------- Отрисовка ----------
    def draw(result) -> Figure:
        fig = Figure(figsize=(7, 7))
        ax = fig.subplots()

        if result.error or result.dtk is None:
            ax.text(0.5, 0.5, tr("no_data"), ha="center", va="center")
            ax.axis("off")
            return fig

        q = result.q
        dtk = result.dtk
        r_out = result.d / 2
        flags = state["flags"]

        if flags["profile"]:
            x, y = compute_profile(q, dtk, r_out)
            ax.plot(x, y, "b-", linewidth=1.2)

        if flags["separator"]:
            r_sep_out, r_sep_in = compute_separator(q, dtk, r_out)
            ax.add_patch(Circle((0, 0), r_sep_out, fill=False, color="g", linewidth=1.0))
            ax.add_patch(Circle((0, 0), r_sep_in, fill=False, color="g", linewidth=1.0))

        if flags["eccentric"]:
            e, rd = compute_eccentric(q, dtk, r_out)
            ax.add_patch(Circle((0, e), rd, fill=False, color="r", linewidth=1.0))
            ax.plot([0, 0], [0, e], "r--", linewidth=0.8)

        if flags["balls"]:
            x_sh, y_sh = compute_balls(q, dtk, r_out)
            rsh = dtk / 2
            for i in range(len(x_sh) - 1):
                ax.add_patch(Circle((x_sh[i], y_sh[i]), rsh, fill=False,
                                    color="orange", linewidth=1.0))

        if flags["out_diameter"]:
            ax.add_patch(Circle((0, 0), r_out, fill=False, color="k",
                                linestyle="--", linewidth=1.0))

        lim = r_out * 1.1
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.set_xlabel(tr("axis_x"))
        ax.set_ylabel(tr("axis_y"))
        fig.tight_layout()
        return fig

    def fig_to_png(fig: Figure, dpi: int) -> bytes:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi)
        return buf.getvalue()

    # ---------- Журнал ----------
    # Записи журнала формирует core/logger.py — они остаются на русском
    # (технический лог, его удобно сравнивать между запусками).
    def refresh_log():
        w["log_view"].clear()
        for line in get_log().split("\n"):
            w["log_view"].push(line)

    def save_log():
        fmt = state["log_fmt"]
        data = export_log(fmt).encode("utf-8-sig" if fmt == "csv" else "utf-8")
        name = f"vptc_log_{datetime.now():%Y%m%d_%H%M%S}.{fmt}"
        ui.download(data, name)

    def on_clear_log():
        clear_log()
        refresh_log()

    # ---------- Пересчёт ----------
    def recompute():
        result = run_solve()

        w["output"].clear()
        with w["output"]:
            if result.error:
                ui.label(tr("error_prefix", msg=tr_error(result))).classes("text-red-600")
            else:
                if result.gost_rounded:
                    ui.label(tr("dtk_calc", v=result.dtk_calc)) \
                        .classes("text-gray-500 text-sm")
                    ui.label(tr("dtk_gost", v=result.dtk)) \
                        .classes("text-blue-600 font-bold")
                else:
                    ui.label(tr("dtk_plain", v=result.dtk))

                ui.label(tr("line_d", v=result.d))
                ui.label(tr("line_l", v=result.l))
                ui.label(tr("line_w", v=result.w / 1000))

                ui.label(tr("line_q", v=result.q))
                if result.q_raw is not None:
                    dev = (result.m_in - result.m_in_requested) / result.m_in_requested * 100
                    ui.label(tr("q_rounded", q_raw=result.q_raw, q=int(result.q),
                                m_in_req=result.m_in_requested, m_in=result.m_in,
                                dev=dev)).classes("text-orange-600 text-sm")
                ui.separator()
                ui.label(tr("line_zsh", v=result.zsh)).classes("font-bold")
                ui.label(tr("line_zg", v=result.zg)).classes("font-bold")

                min_rout = min_r_out_from_q_dtk(result.q, result.dtk)
                r_out = result.d / 2
                if r_out <= min_rout:
                    ui.label(tr("rout_warn", r=r_out, rmin=min_rout)) \
                        .classes("text-orange-600 font-bold")

                ui.separator()
                ui.label(tr("line_m_out", v=result.m_out)).classes("font-bold")
                ui.label(tr("line_m_in", v=result.m_in)).classes("font-bold text-blue-600")
                ui.label(tr("line_eta", v=result.eta)).classes("text-gray-500 text-sm")

        png = fig_to_png(draw(result), dpi=100)
        w["plot"].set_source("data:image/png;base64," + base64.b64encode(png).decode())
        refresh_log()

    # ---------- Обработчики ----------
    def setter(key, cast=None, allow_none=False):
        """Обновляет state[key] и пересчитывает. Пустое поле (None) либо
        допустимо (q, D, M), либо игнорируется (τ, kN, η)."""
        def handler(e):
            v = e.value
            if v is None:
                if not allow_none:
                    return
            elif cast is not None:
                v = cast(v)
            state[key] = v
            recompute()
        return handler

    def flag_setter(name):
        def handler(e):
            state["flags"][name] = e.value
            recompute()
        return handler

    def save_dxf():
        result = run_solve()
        if result.error:
            ui.notify(tr_error(result), type="negative")
            return
        name = f"vptc_q{result.q:g}_D{result.d:.0f}.dxf"
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, name)
            export_dxf(path, result.q, result.dtk, result.d, state["flags"])
            with open(path, "rb") as f:
                data = f.read()
        ui.download(data, name)

    def save_png():
        result = run_solve()
        if result.error:
            ui.notify(tr_error(result), type="negative")
            return
        ui.download(fig_to_png(draw(result), dpi=150), "vptc.png")

    # ---------- Панель интерфейса ----------
    # @ui.refreshable: при panel.refresh() NiceGUI удаляет элементы панели
    # и выполняет функцию заново — все подписи берутся уже на новом языке.
    # Введённые значения не теряются: они хранятся в state и подставляются
    # в value= при создании полей.
    @ui.refreshable
    def panel():
        ui.page_title(tr("title"))
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(tr("title")).classes("text-2xl font-bold")
            # Закрытие вкладки не останавливает сервер — для этого кнопка
            ui.button(tr("exit"), icon="power_settings_new", on_click=app.shutdown) \
                .props("flat color=negative")

        with ui.card():
            ui.label(tr("main_params")).classes("text-lg font-bold")
            ui.label(tr("fill_two")).classes("text-gray-500 text-sm")
            with ui.row():
                ui.number(label=tr("q_label"), value=state["q"],
                          on_change=setter("q", float, allow_none=True))
                ui.number(label=tr("d_label"), value=state["d"],
                          on_change=setter("d", float, allow_none=True))
                ui.number(label=tr("m_label"), value=state["m_out"],
                          on_change=setter("m_out", float, allow_none=True))
                ui.number(label=tr("m_in_label"), value=state["m_in"],
                          on_change=setter("m_in", float, allow_none=True))

        with ui.card():
            ui.label(tr("construction")).classes("text-lg font-bold")
            with ui.row():
                ui.toggle(
                    options={"ball": tr("ball"), "roller": tr("roller")},
                    value=state["body_type"],
                    on_change=setter("body_type"),
                )
                ui.checkbox(tr("gost_round"), value=state["use_gost"],
                            on_change=setter("use_gost"))
            with ui.row():
                tau_input = ui.number(label=tr("tau_label"), value=state["tau"],
                                      on_change=setter("tau", float))
                with tau_input:
                    ui.tooltip(MATERIAL_HINT_EN if state["lang"] == "en" else MATERIAL_HINT)
                ui.number(label=tr("kn_label"), value=state["kn"], step=0.01,
                          on_change=setter("kn", float))
            with ui.row():
                eta_input = ui.number(label=tr("eta_label"), value=state["eta"],
                                      step=0.01, min=0.1, max=1.0,
                                      on_change=setter("eta", float))
                with eta_input:
                    ui.tooltip(tr("eta_hint"))

        with ui.card():
            ui.label(tr("elements")).classes("text-lg font-bold")
            f = state["flags"]
            with ui.row():
                ui.checkbox(tr("el_profile"), value=f["profile"], on_change=flag_setter("profile"))
                ui.checkbox(tr("el_separator"), value=f["separator"], on_change=flag_setter("separator"))
                ui.checkbox(tr("el_eccentric"), value=f["eccentric"], on_change=flag_setter("eccentric"))
                ui.checkbox(tr("el_balls"), value=f["balls"], on_change=flag_setter("balls"))
                ui.checkbox(tr("el_outline"), value=f["out_diameter"], on_change=flag_setter("out_diameter"))

        with ui.card():
            ui.label(tr("saving")).classes("text-lg font-bold")
            with ui.row():
                ui.button(tr("save_dxf"), on_click=save_dxf)
                ui.button(tr("save_png"), on_click=save_png)

        with ui.card():
            ui.label(tr("results")).classes("text-lg font-bold")
            w["output"] = ui.column()

        with ui.card():
            ui.label(tr("geometry")).classes("text-lg font-bold")
            w["plot"] = ui.image().classes("w-[600px]")

        with ui.card().classes("w-full"):
            ui.label(tr("log_title")).classes("text-lg font-bold")
            w["log_view"] = ui.log(max_lines=500).classes("w-full h-64 font-mono text-xs")
            with ui.row().classes("items-center"):
                ui.select({"txt": "TXT", "json": "JSON", "csv": "CSV"},
                          value=state["log_fmt"], label=tr("log_format"),
                          on_change=lambda e: state.update(log_fmt=e.value))
                ui.button(tr("save_log"), on_click=save_log)
                ui.button(tr("clear_log"), on_click=on_clear_log)

    # ---------- Переключатель языка ----------
    def on_lang(e):
        if e.value is None or e.value == state["lang"]:
            return
        state["lang"] = e.value
        panel.refresh()   # пересоздать все подписи на новом языке
        recompute()       # заново вывести результаты и график

    # Переключатель — вне panel: он не должен пересоздаваться
    # во время обработки собственного события.
    with ui.row().classes("w-full justify-end"):
        ui.toggle(LANGUAGES, value=state["lang"], on_change=on_lang)

    panel()
    recompute()