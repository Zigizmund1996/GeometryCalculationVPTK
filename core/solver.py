"""Три режима расчёта ВПКТ, ГОСТ-округление + Момент входа"""

from dataclasses import dataclass, field

from scipy.optimize import brentq
import math

from .formula import (
    dtk_from_q_m, m_out_from_q_dtk, l_from_n_dtk,
    w_from_d_l, m_in_from_m_out, d_from_q_dtk,
    zsh_from_q, zg_from_q, km_from_tau
)
from .constans import round_up_to_gost, GOST_BALL_DIAMETERS, GOST_ROLLER_DIAMETERS
from .logger import (
    log_error, log_info, log_warn
)


# Коды ошибок → русский текст. Английский текст — в localization.py (интерфейс).
ERRORS_RU = {
    "err_min2": "Заполните минимум 2 поля из 3",
    "err_exact2": "Заполните ровно 2 поля",
    "err_n": "Число рядов n должно быть >= 1",
    "err_tau": "[τ] должно быть > 0",
    "err_eta": "КПД η должен быть в диапазоне (0; 1]",
    "err_positive": "{name} должно быть > 0",
    "err_q_min": "q должно быть > 2 (sin(π/(q-1)) должен быть > 0)",
    "err_no_root": "Решение не найдено в q = 4.1...100",
    "err_gost_range": "dтк={dtk:.3f} мм больше максимального стандартного ({dmax} мм) по ГОСТ",
}


@dataclass
class VPTCResult:
    """Результат расчета ВПТК."""
    q: float | None = None
    d: float | None = None
    m_out: float | None = None
    m_in: float | None = None
    eta: float | None = None
    dtk: float | None = None
    dtk_calc: float | None = None
    l: float | None = None
    w: float | None = None
    zsh: int | None = None
    zg: int | None = None
    gost_rounded: bool = False
    error: str | None = None          # текст по-русски (для логов/совместимости)
    error_key: str | None = None      # код ошибки — по нему UI подбирает перевод
    error_args: dict = field(default_factory=dict)


def _error(key: str, **args) -> "VPTCResult":
    """Результат-ошибка: русский текст + код и параметры для перевода в UI."""
    return VPTCResult(error=ERRORS_RU[key].format(**args),
                      error_key=key, error_args=args)


def _apply_gost(result: VPTCResult, q: float, n: int, k: float,
                km: float, kn: float, kh: float,
                eta: float, body_type: str, use_gost: bool) -> VPTCResult:
    """Округляем dtk вверх под ГОСТ."""
    if not use_gost:
        log_info("gost", "Rounding according to GOST is DISABLED")
        return result
    try:
        dtk_rounded = round_up_to_gost(result.dtk, body_type)
    except ValueError as e:
        table = GOST_BALL_DIAMETERS if body_type == "ball" else GOST_ROLLER_DIAMETERS
        log_error("gost", str(e), dtk=round(result.dtk, 4), body_type=body_type)
        return _error("err_gost_range", dtk=result.dtk, dmax=table[-1])
    result.dtk_calc = result.dtk
    result.dtk = dtk_rounded
    result.gost_rounded = True

    result.d = d_from_q_dtk(q, dtk_rounded)
    result.l = l_from_n_dtk(n, dtk_rounded)
    result.w = w_from_d_l(result.d, result.l)
    result.m_out = m_out_from_q_dtk(q, dtk_rounded, n, k, km, kn, kh)
    result.m_in = m_in_from_m_out(result.m_out, q, eta)

    log_info("gost",
             f"Rounding {body_type}: {result.dtk_calc:.3f} → {dtk_rounded:.3f} мм",
             dtk_calc=round(result.dtk_calc, 4),
             dtk_gost=round(dtk_rounded, 4),
             d=round(result.d, 2), l=round(result.l, 2),
             w=round(result.w / 1000, 2), m_out=round(result.m_out, 2))

    return result


def _solve_q_d(q: float, d: float, n: int, k: float, km: float, kn: float, kh: float, eta: float):
    dtk = d / (2.06 / math.sin(math.pi / q) + 1.8)
    m_out = m_out_from_q_dtk(q, dtk, n, k, km, kn, kh)
    l = l_from_n_dtk(n, dtk)
    w = w_from_d_l(d, l)
    m_in = m_in_from_m_out(m_out, q, eta)

    log_info("solve.q_d",
            f"q={q}, D={d} → M_вых={m_out:.2f}, dTK={dtk:.3f}, "
            f"Число тел качения={zsh_from_q(q)}, Число впадин={zg_from_q(q)}, M_вх={m_in:.3f}",
            q=q, d=d, zsh=zsh_from_q(q), zg=zg_from_q(q),
            dtk=round(dtk, 4), m_out=round(m_out, 4),
            l=round(l, 3), w=round(w / 1000, 3), m_in=round(m_in, 4))

    return VPTCResult(q=q, d=d, m_out=m_out, m_in=m_in, eta=eta,
                      dtk=dtk, l=l, w=w, zsh=zsh_from_q(q), zg=zg_from_q(q)
                      )


def _solve_q_m_out(q, m_out, n, k, km, kn, kh, eta):
    dtk = dtk_from_q_m(q, m_out, n, k, km, kn, kh)
    d = d_from_q_dtk(q, dtk)
    l = l_from_n_dtk(n, dtk)
    w = w_from_d_l(d, l)
    m_in = m_in_from_m_out(m_out, q, eta)

    log_info("solve.q_m_out",
             f"q={q}, M_вых={m_out:.2f} → D={d}, dTK={dtk:.3f}, "
            f"Число тел качения={zsh_from_q(q)}, Число впадин={zg_from_q(q)}, M_вх={m_in:.3f}",
            q=q, d=d, zsh=zsh_from_q(q), zg=zg_from_q(q),
            dtk=round(dtk, 4), m_out=round(m_out, 4),
            l=round(l, 3), w=round(w / 1000, 3), m_in=round(m_in, 4))

    return VPTCResult(q=q, d=d, m_out=m_out, m_in=m_in, eta=eta,
                      dtk=dtk, l=l, w=w, zsh=zsh_from_q(q), zg=zg_from_q(q)
                      )


def _solve_d_m_out(d, m_out, n, k, km, kn, kh, eta):
    def f(q):
        dtk = dtk_from_q_m(q, m_out, n, k, km, kn, kh)
        return d_from_q_dtk(q, dtk) - d
    # D(q) немонотонна (есть минимум), поэтому ищем все смены знака на сетке
    # и уточняем каждый корень через brentq.
    q_min, q_max, steps = 4.1, 100.0, 2000
    grid = [q_min + (q_max - q_min) * i / steps for i in range(steps + 1)]
    roots = []
    prev_q, prev_f = grid[0], f(grid[0])
    for cur_q in grid[1:]:
        cur_f = f(cur_q)
        if prev_f == 0:
            roots.append(prev_q)
        elif prev_f * cur_f < 0:
            roots.append(brentq(f, prev_q, cur_q))
        prev_q, prev_f = cur_q, cur_f
    if not roots:
        log_error("solve.d_m_out", f"Не найдено решение для D={d}, M_вых={m_out}",
                  d=d, m_out=m_out)
        return _error("err_no_root")
    q = max(roots)  # большее q: больше тел качения, меньше dтк
    if len(roots) > 1:
        log_warn("solve.d_m_out.multi",
                 f"Найдено несколько решений q={[round(x, 4) for x in roots]}, "
                 f"выбрано q={q:.4f}",
                 roots=[round(x, 6) for x in roots])
    dtk = dtk_from_q_m(q, m_out, n, k, km, kn, kh)
    l = l_from_n_dtk(n, dtk)
    w = w_from_d_l(d, l)
    m_in = m_in_from_m_out(m_out, q, eta)

    log_info("solve.D_M",
            f"D={d}, M_вых={m_out} → q={q:.4f}, dTK={dtk:.3f}, "
            f"Число тел качения={zsh_from_q(q)}, Число впадин={zg_from_q(q)}, M_вх={m_in:.3f}",
            d=d, m_out=m_out, zsh=zsh_from_q(q), zg=zg_from_q(q),
            q_solved=round(q, 6), dtk=round(dtk, 4),
            l=round(l, 3), w=round(w / 1000, 3), m_in=round(m_in, 4))

    return VPTCResult(q=q, d=d, m_out=m_out, m_in=m_in, eta=eta,
                      dtk=dtk, l=l, w=w, zsh=zsh_from_q(q), zg=zg_from_q(q)
                      )


def solve(q=None, d=None, m_out=None, n=1, body_type="roller",
          tau=150.0, kn=0.56, eta=0.85, use_gost=False) -> VPTCResult:
    """
    Универсальная точка входа. Заполни ровно два из трёх: q, D, M.
    kH = 1.0 (один ряд). km = 33.8e3 / tau.
    M_вх = M_вых / (q · η). z_sh = int(q), z_g = int(q) + 1.
    """
    k = 1.0 if body_type == "ball" else 2.0
    km = km_from_tau(tau)
    kh = 1.0

    log_info("solve.start",
             f"Старт: q={q}, D={d}, M_вых={m_out}, body={body_type}",
             q=q, d=d, m_out=m_out, n=n, body_type=body_type,
             tau=tau, kn=kn, eta=eta, use_gost=use_gost,
             k=k, km=round(km, 3), kh=kh)

    filled = sum(x is not None for x in (q, d, m_out))
    if filled < 2:
        log_warn("solve.validation", "Заполнено меньше 2 полей")
        return _error("err_min2")
    if filled == 3:
        log_warn("solve.validation", "Заполнено 3 поля вместо 2")
        return _error("err_exact2")

    # --- валидация числовых значений ---
    if n < 1:
        return _error("err_n")
    if tau <= 0:
        return _error("err_tau")
    if not 0 < eta <= 1:
        return _error("err_eta")
    for name, val in (("q", q), ("D", d), ("M", m_out)):
        if val is not None and val <= 0:
            return _error("err_positive", name=name)
    if q is not None and q <= 2:
        return _error("err_q_min")

    # --- выбор режима ---
    if q is None:
        result = _solve_d_m_out(d, m_out, n, k, km, kn, kh, eta)
    elif d is None:
        result = _solve_q_m_out(q, m_out, n, k, km, kn, kh, eta)
    else:
        result = _solve_q_d(q, d, n, k, km, kn, kh, eta)

    if result.error:
        return result

    if result.q != int(result.q):
        log_warn("solve.q_fractional",
                 f"q={result.q:.4f} не целое: zsh=int(q), zg=int(q)+1 "
                 f"усечены, подберите целое q",
                 q=round(result.q, 6))

    return _apply_gost(result, result.q, n, k, km, kn, kh, eta, body_type, use_gost)