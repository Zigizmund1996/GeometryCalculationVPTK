"""Экспорт геометрии ВПТК в DXF. Единицы: миллиметры."""

import ezdxf
from ezdxf.units import MM
from .geometry import (
    compute_profile, compute_balls,
    compute_separator, compute_eccentric,
)


def export_dxf(filename: str, q: float, dtk: float, d: float,
               flags: dict):
    """
    Сохраняет геометрию ВПТК в DXF.

    Единицы измерения: миллиметры ($INSUNITS = 4).

    flags: dict с ключами:
        'profile'      — жёсткое колесо
        'separator'    — сепаратор
        'eccentric'    — эксцентрик
        'balls'        — тела качения
        'out_diameter' — габаритный диаметр
    """
    r_out = d / 2
    doc = ezdxf.new("R2000")
    doc.units = MM              # миллиметры
    msp = doc.modelspace()

    if flags.get("profile"):
        x, y = compute_profile(q, dtk, r_out)
        msp.add_lwpolyline(list(zip(x, y)))

    if flags.get("separator"):
        r_sep_out, r_sep_in = compute_separator(q, dtk, r_out)
        msp.add_circle((0, 0), r_sep_out)
        msp.add_circle((0, 0), r_sep_in)

    if flags.get("eccentric"):
        e, rd = compute_eccentric(q, dtk, r_out)
        msp.add_circle((0, e), rd)
        msp.add_point([0, e])
        msp.add_lwpolyline([[0, 0], [0, e]])

    if flags.get("balls"):
        x_sh, y_sh = compute_balls(q, dtk, r_out)
        rsh = dtk / 2
        for i in range(len(x_sh) - 1):
            msp.add_circle((x_sh[i], y_sh[i]), rsh)

    if flags.get("out_diameter"):
        msp.add_circle((0, 0), d/2)

    doc.saveas(filename)