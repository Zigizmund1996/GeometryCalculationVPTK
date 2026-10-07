"""Локализация интерфейса: словари строк и функция перевода.

Как добавить язык: скопируйте блок "en", переведите значения и добавьте
код языка в LANGUAGES. Ключи (слева) не меняются.
Подстановки {имя} и форматы вроде {v:.3f} оставляйте как есть.
"""

DEFAULT_LANG = "ru"

# код языка → подпись на кнопке переключателя
LANGUAGES = {"ru": "RU", "en": "EN"}

TRANSLATIONS = {
    "ru": {
        "title": "Расчёт ВПТК",
        "exit": "Выход",
        # --- карточки и поля
        "main_params": "Основные параметры",
        "fill_two": "Заполните ровно два поля из трёх",
        "q_label": "Передаточное число q",
        "d_label": "Наружный диаметр D, мм",
        "m_label": "Момент на выходе M, Н·м",
        "construction": "Параметры конструкции",
        "ball": "Шарики",
        "roller": "Ролики",
        "gost_round": "Округлить под ГОСТ",
        "tau_label": "τ (напряжение на срез), МПа",
        "kn_label": "kN (неравномерность в ряду)",
        "eta_label": "η (КПД)",
        "eta_hint": (
            "КПД ВПТК:\n"
            "  0.92 — экспериментально (Степанов 2009)\n"
            "  0.95 — расчётно\n"
            "  0.80…0.90 — типовой диапазон\n"
            "Используем при расчетах 0.85"
        ),
        "elements": "Элементы на графике",
        "el_profile": "Жёсткое колесо",
        "el_separator": "Сепаратор",
        "el_eccentric": "Эксцентрик",
        "el_balls": "Тела качения",
        "el_outline": "Габарит",
        "saving": "Сохранение",
        "save_dxf": "Сохранить DXF",
        "save_png": "Сохранить PNG",
        "results": "Результаты",
        "geometry": "Геометрия",
        # --- результаты
        "error_prefix": "Ошибка: {msg}",
        "dtk_calc": "d_ТК расчётный: {v:.3f} мм",
        "dtk_gost": "d_ТК по ГОСТ: {v:.3f} мм",
        "dtk_plain": "d_ТК = {v:.3f} мм",
        "line_d": "D = {v:.2f} мм",
        "line_l": "L = {v:.2f} мм",
        "line_w": "W = {v:.2f} см³",
        "line_q": "q = {v:.4f}",
        "line_zsh": "zsh = {v} — число тел качения",
        "line_zg": "zg = {v} — число впадин жёсткого колеса",
        "rout_warn": "⚠ Rout = {r:.2f} мм ≤ min = {rmin:.2f} мм",
        "line_m_out": "M_вых = {v:.2f} Н·м",
        "line_m_in": "M_вх = {v:.2f} Н·м",
        "line_eta": "η = {v:.2f}",
        # --- график
        "no_data": "Нет данных",
        "axis_x": "x, мм",
        "axis_y": "y, мм",
        # --- журнал
        "log_title": "Журнал расчёта",
        "log_format": "Формат",
        "save_log": "Сохранить журнал",
        "clear_log": "Очистить журнал",
        # --- ошибки расчёта (коды из core/solver.py)
        "err_min2": "Заполните минимум 2 поля из 3",
        "err_exact2": "Заполните ровно 2 поля",
        "err_n": "Число рядов n должно быть >= 1",
        "err_tau": "[τ] должно быть > 0",
        "err_eta": "КПД η должен быть в диапазоне (0; 1]",
        "err_positive": "{name} должно быть > 0",
        "err_q_min": "q должно быть > 2 (sin(π/(q-1)) должен быть > 0)",
        "err_no_root": "Решение не найдено в q = 4.1...100",
        "err_gost_range": "dтк={dtk:.3f} мм больше максимального стандартного ({dmax} мм) по ГОСТ",
    },
    "en": {
        "title": "Wave gear with rolling elements — calculation",
        "exit": "Exit",
        "main_params": "Main parameters",
        "fill_two": "Fill in exactly two of the three fields",
        "q_label": "Gear ratio q",
        "d_label": "Outer diameter D, mm",
        "m_label": "Output torque M, N·m",
        "construction": "Design parameters",
        "ball": "Balls",
        "roller": "Rollers",
        "gost_round": "Round to GOST standard sizes",
        "tau_label": "τ (allowable shear stress), MPa",
        "kn_label": "kN (non-uniformity within a row)",
        "eta_label": "η (efficiency)",
        "eta_hint": (
            "Gear efficiency:\n"
            "  0.92 — experimental (Stepanov 2009)\n"
            "  0.95 — calculated\n"
            "  0.80…0.90 — typical range\n"
            "0.85 is used in calculations"
        ),
        "elements": "Elements on the plot",
        "el_profile": "Rigid wheel",
        "el_separator": "Cage",
        "el_eccentric": "Eccentric",
        "el_balls": "Rolling elements",
        "el_outline": "Outline",
        "saving": "Export",
        "save_dxf": "Save DXF",
        "save_png": "Save PNG",
        "results": "Results",
        "geometry": "Geometry",
        "error_prefix": "Error: {msg}",
        "dtk_calc": "d_RE calculated: {v:.3f} mm",
        "dtk_gost": "d_RE per GOST: {v:.3f} mm",
        "dtk_plain": "d_RE = {v:.3f} mm",
        "line_d": "D = {v:.2f} mm",
        "line_l": "L = {v:.2f} mm",
        "line_w": "W = {v:.2f} cm³",
        "line_q": "q = {v:.4f}",
        "line_zsh": "zsh = {v} — number of rolling elements",
        "line_zg": "zg = {v} — number of rigid-wheel cavities",
        "rout_warn": "⚠ Rout = {r:.2f} mm ≤ min = {rmin:.2f} mm",
        "line_m_out": "M_out = {v:.2f} N·m",
        "line_m_in": "M_in = {v:.2f} N·m",
        "line_eta": "η = {v:.2f}",
        "no_data": "No data",
        "axis_x": "x, mm",
        "axis_y": "y, mm",
        "log_title": "Calculation log",
        "log_format": "Format",
        "save_log": "Save log",
        "clear_log": "Clear log",
        "err_min2": "Fill in at least 2 of the 3 fields",
        "err_exact2": "Fill in exactly 2 fields",
        "err_n": "Number of rows n must be >= 1",
        "err_tau": "[τ] must be > 0",
        "err_eta": "Efficiency η must be in the range (0; 1]",
        "err_positive": "{name} must be > 0",
        "err_q_min": "q must be > 2 (sin(π/(q-1)) must be > 0)",
        "err_no_root": "No solution found for q in 4.1...100",
        "err_gost_range": "d_RE={dtk:.3f} mm exceeds the largest GOST standard size ({dmax} mm)",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Перевод по ключу. Нет в языке → берём русский → иначе сам ключ."""
    table = TRANSLATIONS.get(lang) or TRANSLATIONS[DEFAULT_LANG]
    text = table.get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT_LANG].get(key, key)
    return text.format(**kwargs) if kwargs else text