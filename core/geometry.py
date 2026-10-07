"""Расчёт координат профиля и тел качения ВПТК."""

import numpy as np
from .formula import zsh_from_q, zg_from_q


def compute_profile(q: float, dtk: float, r_out: float, resolution: int = 600):
    e = 0.2 * dtk # эксцентриситет
    rsh = dtk / 2
    rd = r_out - 2*e - dtk
    zg = zg_from_q(q)
    theta = np.linspace(0, 2*np.pi, resolution)
    s = np.sqrt((rsh + rd)**2 - (e * np.sin(zg * theta))**2)
    l = e * np.cos(zg * theta) + s
    xi = np.arctan2(e * zg * np.sin(zg * theta), s)
    x = l * np.sin(theta) + rsh * np.sin(theta + xi)
    y = l * np.cos(theta) + rsh * np.cos(theta + xi)
    return x, y


def compute_balls(q: float, dtk: float, r_out: float):
    """Центры тел качения. z_sh = int(q)."""
    e = 0.2 * dtk
    rsh = dtk / 2
    rd = r_out - 2*e - dtk
    zg = zg_from_q(q)
    zsh = zsh_from_q(q)
    sh_angle = np.linspace(0, 1, zsh+1) * 2*np.pi
    s_sh = np.sqrt((rsh + rd)**2 - (e * np.sin(zg * sh_angle))**2)
    l_sh = e * np.cos(zg * sh_angle) + s_sh
    x_sh = l_sh * np.sin(sh_angle)
    y_sh = l_sh * np.cos(sh_angle)
    return x_sh, y_sh


def compute_separator(q: float, dtk: float, r_out: float):
    e = 0.2 * dtk # эксцентриситет
    rsh = dtk / 2
    rd = r_out - 2*e - dtk
    hc = 2.2 * e # толщина сепаратора
    r_sep_m = rd + rsh
    return r_sep_m + hc/2, r_sep_m - hc/2


def compute_eccentric(q: float, dtk: float, r_out: float):
    e = 0.2 * dtk
    rd = r_out - 2*e - dtk
    return e, rd