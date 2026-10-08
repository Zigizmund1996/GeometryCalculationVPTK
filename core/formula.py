"""Формулы расчета ВПТК. Без UI, без состояния."""

import math
from .constans import GOST_ROLLER_DIAMETERS


def km_from_tau(tau: float) -> float:
    """
    Коэффициент материала сепаратора.
    km = 33.8e3 / [τ], где [τ] максимальное напряжение на срез в МПа.
    Источник: Подшибнев 2022, табл. 3.3
    """
    return 33.8e3 / tau


def dtk_from_q_m(q: float, m_out: float, n: int, k: float,
                 km: float, kn: float, kh: float) -> float:
    """Диаметр тела качения [dtk] из передаточного число [q] и выходного момента [m_out]. Подшибнев 2022, ф. 3.15."""
    num = km * m_out * math.sin(math.pi / (q-1))
    den = kn * k * kh * n * (q-1)
    # n - число рядов (1) k - тип контакта (1-шарик, 2-роллик)
    # kn - неравномерность в одном раду (0.56) kh - неравномерность между рядами (1 - один ряд)
    return (num / den) ** (1/3)


def m_out_from_q_dtk(q: float, dtk: float, n: int, k: float,
                 km: float, kn: float, kh: float) -> float:
    """Момент из q и dtk."""
    return (dtk ** 3 * kn * k * kh * n * (q - 1)) / (km * math.sin(math.pi / (q - 1)))


def d_from_q_dtk(q:float, dtk: float) -> float:
    """Наружный диаметр из q и dtk. Подшибнев 2022, ф. 3.16."""
    return (2.06 / math.sin(math.pi / q) + 1.8) * dtk


def l_from_n_dtk(n: int, dtk: float, body_type: str) -> float:
    """Длина из n и dtk. Подшибнев 2022, ф. 3.17."""
    if body_type == "roller":
        # Для ролика — берём длину из таблицы по ключу dTK
        l_roller = GOST_ROLLER_DIAMETERS.get(dtk, dtk)  # если нет ключа — берём dTK
        return (1.2 * n + 1.8) * l_roller
    else:
        # Для шарика — используем диаметр
        return (1.2 * n + 1.8) * dtk


def w_from_d_l(d: float, l: float) -> float:
    """Объём из d и l. Подшибнев 2022, ф. 3.18."""
    return (math.pi / 4) * d**2 * l


def m_in_from_m_out(m_out: float, q: float, eta: float) -> float:
    """
    Момент на входе (на валу волнообразователя).
    M_вх = M_вых / (q · η).
    """
    return m_out / (q * eta)


def zsh_from_q(q: float) -> int:
    """
    Число тел качения в одном ряду число волн = 1
    """
    return int(q)


def zg_from_q(q: float) -> int:
    """
    Число впадин при одной волне
    """
    return int(q) + 1


def min_r_out_from_q_dtk(q: float, dtk: float) -> float:
    """
    Минимальный внешний радиус жёсткого колеса.
    Из условия, что Rin > 1.03 * dtk / sin(pi / zg)
    """
    zg = zg_from_q(q)
    return (1.03 * dtk) / math.sin(math.pi / zg) + 0.4 * dtk
