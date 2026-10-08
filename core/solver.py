"""Три режима расчёта ВПКТ, ГОСТ-округление + Момент входа"""

from dataclasses import dataclass, field

from scipy.optimize import brentq
import math

from .formula import (
    dtk_from_q_m, m_out_from_q_dtk, l_from_n_dtk,
    w_from_d_l, m_in_from_m_out, d_from_q_dtk,
    zsh_from_q, zg_from_q, km_from_tau
)
from .constans import round_up_to_gost, gost_table
from .logger import (
    log_error, log_info, log_warn
)


# Коды ошибок → русский текст. Английский текст — в local.py (интерфейс).
ERRORS_RU = {
    "err_min2": "Заполните минимум 2 поля из 4",
    "err_exact2": "Заполните ровно 2 поля",
    "err_n": "Число рядов n должно быть >= 1",
    "err_tau": "[τ] должно быть > 0",
    "err_eta": "КПД η должен быть в диапазоне (0; 1]",
    "err_positive": "{name} должно быть > 0",
    "err_q_min": "q должно быть > 2 (sin(π/(q-1)) должен быть > 0)",
    "err_no_root": "Решение не найдено в q = 4.1...100",
    "err_gost_range": "dтк={dtk:.3f} мм больше максимального стандартного ({dmax} мм) по ГОСТ",
    "err_unsupported": "Эта пара не поддерживается",
    "err_q_calc": "Из моментов получилось q={q:.3f} ≤ 2 — проверьте Mвх, Mвых и η"
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
    q_raw: float | None = None  # q до округления (режим M_вх + M_вых)
    m_in_requested: float | None = None  # M_вх, введённый пользователем


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
        table = gost_table(body_type)
        log_error("gost", str(e), dtk=round(result.dtk, 4), body_type=body_type)
        return _error("err_gost_range", dtk=result.dtk, dmax=table[-1])
    result.dtk_calc = result.dtk
    result.dtk = dtk_rounded
    result.gost_rounded = True

    result.d = d_from_q_dtk(q, dtk_rounded)
    result.l = l_from_n_dtk(n, dtk_rounded, body_type)
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


def _solve_q_d(q: float, d: float, n: int, k: float, km: float, kn: float, kh: float, eta: float, body_type: str):
    dtk = d / (2.06 / math.sin(math.pi / q) + 1.8)
    m_out = m_out_from_q_dtk(q, dtk, n, k, km, kn, kh)
    l = l_from_n_dtk(n, dtk, body_type)
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


def _solve_q_m_out(q, m_out, n, k, km, kn, kh, eta, body_type):
    dtk = dtk_from_q_m(q, m_out, n, k, km, kn, kh)
    d = d_from_q_dtk(q, dtk)
    l = l_from_n_dtk(n, dtk, body_type)
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


def _solve_d_m_out(d, m_out, n, k, km, kn, kh, eta, body_type):
    q_min, q_max, steps = 4.1, 100.0, 2000

    # Невязка как функция от q при фиксированном m
    def f(q, m):
        dtk = dtk_from_q_m(q, m, n, k, km, kn, kh)
        return d_from_q_dtk(q, dtk) - d

    # Все корни по q для фиксированного m (D(q) немонотонна — ищем все смены знака)
    def roots_for_m(m):
        roots = []
        prev_q = q_min
        prev_f = f(q_min, m)
        for i in range(1, steps + 1):
            cur_q = q_min + (q_max - q_min) * i / steps
            cur_f = f(cur_q, m)
            if prev_f == 0:
                roots.append(prev_q)
            elif prev_f * cur_f < 0:
                roots.append(brentq(lambda qq, mm=m: f(qq, mm), prev_q, cur_q))
            prev_q, prev_f = cur_q, cur_f
        return roots

    # 1) пробуем точное значение m_out
    roots = roots_for_m(m_out)
    m_used = m_out

    # 2) если решения нет — ищем ближайшее m_out, при котором q существует
    if not roots:
        span = 0.5          # ±50 % от m_out
        n_scan = 200        # число проб по m
        m_lo = max(1e-9, m_out * (1.0 - span))
        m_hi = m_out * (1.0 + span)

        best = None         # (|m - m_out|, m, q)
        for i in range(n_scan + 1):
            m = m_lo + (m_hi - m_lo) * i / n_scan
            if m <= 0:
                continue
            r = roots_for_m(m)
            if not r:
                continue
            q_cand = max(r)
            dist = abs(m - m_out)
            if best is None or dist < best[0]:
                best = (dist, m, q_cand)

        if best is None:
            log_error("solve.d_m_out",
                      f"Не найдено решение для D={d}, M_вых={m_out}",
                      d=d, m_out=m_out)
            return _error("err_no_root")

        _, m_used, q_best = best
        log_warn("solve.d_m_out.nearest",
                 f"Точное решение для M_вых={m_out} не найдено; "
                 f"использовано ближайшее M_вых={m_used:.6f}",
                 m_out_target=m_out, m_out_used=m_used)
        roots = [q_best]

    q = max(roots)  # большее q: больше тел качения, меньше dтк
    if len(roots) > 1:
        log_warn("solve.d_m_out.multi",
                 f"Найдено несколько решений q={[round(x, 4) for x in roots]}, "
                 f"выбрано q={q:.4f}",
                 roots=[round(x, 6) for x in roots])

    dtk = dtk_from_q_m(q, m_used, n, k, km, kn, kh)
    l = l_from_n_dtk(n, dtk, body_type)
    w = w_from_d_l(d, l)
    m_in = m_in_from_m_out(m_used, q, eta)

    log_info("solve.D_M",
            f"D={d}, M_вых={m_out} → q={q:.4f}, dTK={dtk:.3f}, "
            f"Число тел качения={zsh_from_q(q)}, Число впадин={zg_from_q(q)}, M_вх={m_in:.3f}",
            d=d, m_out=m_out, m_out_used=round(m_used, 6),
            zsh=zsh_from_q(q), zg=zg_from_q(q),
            q_solved=round(q, 6), dtk=round(dtk, 4),
            l=round(l, 3), w=round(w / 1000, 3), m_in=round(m_in, 4))

    return VPTCResult(q=q, d=d, m_out=m_out, m_in=m_in, eta=eta,
                      dtk=dtk, l=l, w=w, zsh=zsh_from_q(q), zg=zg_from_q(q)
                      )


def _solve_m_in_m_out(m_in, m_out, n, k, km, kn, kh, eta, body_type):
    """По M_вх и M_вых: q округляется до целого, M_вх пересчитывается."""
    q_raw = m_out / (m_in * eta)
    q = round(q_raw)
    log_info("solve.m_in_m_out",
             f"M_вх={m_in}, M_вых={m_out}, η={eta} → q_расч={q_raw:.4f}, q={q}",
             m_in=m_in, m_out=m_out, eta=eta, q_raw=round(q_raw, 6), q=q)

    if q_raw <= 2 or q <= 2:
        log_error("solve.m_in_m_out", f"q={q_raw:.4f} <= 2", q=round(q_raw, 6))
        return _error("err_q_calc", q=q_raw)

    m_in_new = m_out / (q * eta)
    if q != q_raw:
        dev = (m_in_new - m_in) / m_in * 100
        log_warn("solve.m_in_recalc",
                 f"q округлено {q_raw:.4f} → {q}; "
                 f"M_вх пересчитан {m_in} → {m_in_new:.4f} ({dev:+.1f} %)",
                 m_in_requested=m_in, m_in_new=round(m_in_new, 6),
                 deviation_pct=round(dev, 3))

    result = _solve_q_m_out(q, m_out, n, k, km, kn, kh, eta, body_type)
    if not result.error and q != q_raw:
        result.q_raw = q_raw
        result.m_in_requested = m_in
    return result


def _solve_q_m_in(q, m_in, n, k, km, kn, kh, eta, body_type):
    """По q и входному моменту: M_вых = M_вх · q · η."""
    m_out = m_in * q * eta
    return _solve_q_m_out(q, m_out, n, k, km, kn, kh, eta, body_type)


def _solve_d_m_in(d, m_in, n, k, km, kn, kh, eta, body_type):
    """По D и M_вх: решаем M_вых(q, dтк(q, D)) = M_вх·q·η относительно q,
    затем q округляем до целого и считаем как q + D."""
    q_min, q_max, steps = 4.1, 100.0, 2000

    def f(q):
        dtk = d / (2.06 / math.sin(math.pi / q) + 1.8)
        return m_out_from_q_dtk(q, dtk, n, k, km, kn, kh) - m_in * q * eta

    roots = []
    prev_q, prev_f = q_min, f(q_min)
    for i in range(1, steps + 1):
        cur_q = q_min + (q_max - q_min) * i / steps
        cur_f = f(cur_q)
        if prev_f == 0:
            roots.append(prev_q)
        elif prev_f * cur_f < 0:
            roots.append(brentq(f, prev_q, cur_q))
        prev_q, prev_f = cur_q, cur_f

    if not roots:
        log_error("solve.d_m_in",
                  f"Не найдено решение для D={d}, M_вх={m_in}", d=d, m_in=m_in)
        return _error("err_no_root")

    q_raw = max(roots)  # большее q: больше тел качения
    if len(roots) > 1:
        log_warn("solve.d_m_in.multi",
                 f"Найдено несколько решений q={[round(x, 4) for x in roots]}, "
                 f"выбрано q={q_raw:.4f}",
                 roots=[round(x, 6) for x in roots])

    q = round(q_raw)
    log_info("solve.d_m_in",
             f"D={d}, M_вх={m_in} → q_расч={q_raw:.4f}, q={q}",
             d=d, m_in=m_in, q_raw=round(q_raw, 6), q=q)

    result = _solve_q_d(q, d, n, k, km, kn, kh, eta, body_type)
    if not result.error and abs(q - q_raw) > 1e-6:
        dev = (result.m_in - m_in) / m_in * 100
        log_warn("solve.m_in_recalc",
                 f"q округлено {q_raw:.4f} → {q}; "
                 f"M_вх пересчитан {m_in} → {result.m_in:.4f} ({dev:+.1f} %)",
                 m_in_requested=m_in, m_in_new=round(result.m_in, 6),
                 deviation_pct=round(dev, 3))
        result.q_raw = q_raw
        result.m_in_requested = m_in
    return result


def solve(q=None, d=None, m_out=None, n=1, body_type="roller",
          tau=150.0, kn=0.56, eta=0.85, use_gost=False, m_in=None) -> VPTCResult:
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

    given = {name for name, v in (("q", q), ("d", d),
                                  ("m_out", m_out), ("m_in", m_in))
             if v is not None}
    if len(given) < 2:
        log_warn("solve.validation", "Заполнено меньше 2 полей")
        return _error("err_min2")
    if len(given) > 2:
        log_warn("solve.validation", "Заполнено больше 2 полей")
        return _error("err_exact2")

        # --- валидация числовых значений ---
    if n < 1:
        return _error("err_n")
    if tau <= 0:
        return _error("err_tau")
    if not 0 < eta <= 1:
        return _error("err_eta")
    for name, val in (("q", q), ("D", d), ("Mвых", m_out), ("Mвх", m_in)):
        if val is not None and val <= 0:
                return _error("err_positive", name=name)
    if q is not None and q <= 2:
        return _error("err_q_min")

    # --- выбор режима ---
    args = (n, k, km, kn, kh, eta, body_type)
    if given == {"d", "m_out"}:
        result = _solve_d_m_out(d, m_out, *args)
    elif given == {"q", "m_out"}:
        result = _solve_q_m_out(q, m_out, *args)
    elif given == {"q", "d"}:
        result = _solve_q_d(q, d, *args)
    elif given == {"m_in", "m_out"}:
        result = _solve_m_in_m_out(m_in, m_out, *args)
    elif given == {"q", "m_in"}:
        result = _solve_q_m_in(q, m_in, *args)
    elif given == {"d", "m_in"}:
        result = _solve_d_m_in(d, m_in, *args)
    else:
        return _error("err_unsupported")

    if result.error:
        return result

    if result.q != int(result.q):
        log_warn("solve.q_fractional",
                 f"q={result.q:.4f} не целое: zsh=int(q), zg=int(q)+1 "
                 f"усечены, подберите целое q",
                 q=round(result.q, 6))

    return _apply_gost(result, result.q, n, k, km, kn, kh, eta, body_type, use_gost)