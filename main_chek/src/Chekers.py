import pandas as pd
from main_chek.src.parsers.universal_parser import *

PARAM_LABELS = {
    "cpu_iaas": "vCPU, ядер",
    "ram": "RAM, Гб",
    "ssd": "SSD, Гб",
    "hddf": "HDD Fast, Гб",
    "hdds": "HDD Slow, Гб",
    "os_type": "Тип операционной системы",
    "os_amount": "Количество ОС",
}
def should_skip_row_errors(row_dict, contur_118: dict) -> bool:
    """
    True -> строку полностью пропускаем (не считаем ошибочной).
    """
    if row_dict is None:
        return False

    serv = str(row_dict.get("service_name", "")).strip()
    if serv != "Сервис IAM (услуга 1.1.13)":
        return False

    contour = str(row_dict.get("usage_contour", "")).strip().upper()
    if not contur_118.get(contour, False):
        return False

    try:
        cpu = _to_int(float(str(row_dict.get("cpu_iaas_min", 0))))
        ram = _to_int(float(str(row_dict.get("ram_min", 0))))
        ssd = _to_int(float(str(row_dict.get("ssd_min", 0))))
        hddf = _to_int(float(str(row_dict.get("hddf_min", 0))))
        hdds = _to_int(float(str(row_dict.get("hdds_min", 0))))
        os_type = _to_int(float(str(row_dict.get("os_type_min", 0))))
        # если тебе os_amount не нужен — убери
        os_amount = _to_int(float(str(row_dict.get("os_amount_min", 0))))
    except Exception:
        return False

    # твой эталон: 4 8 0 0 100 2 (+ os_amount=2 у тебя уже фигурирует в chek18)
    return (cpu, ram, ssd, hddf, hdds, os_type, os_amount) == (4, 8, 0, 0, 100, 2, 2)


def report_ones(label, actual,pref,desired=None):
       if pref==1:
           return f"Завышен параметр {label} ({actual}) более чем в 1.5 раза"
       if pref==3:
            return f"Завышен параметр {label} ({actual})."
       if pref==5:
           return f"Завышен параметр {label} ({actual}). Требуется обоснование."
       if pref==8: 
           return f"Завышен параметр {label} ({actual}). Требуется пересмотр архитектуры и согласование."
       if pref==0:
           return f"Параметр {label} ({actual}) ниже значения ТК. Требуется значение {desired}."
       if pref==-1:
           return f"Параметр {label} ({actual}) не верный значения ТК. Требуется значение {desired}."
       

def _to_int(x) -> int:
    try:
        if x is None:
            return 0

        # pandas NaN
        if isinstance(x, float) and x != x:
            return 0

        s = str(x).strip()
        if s == "" or s.lower() in ("nan", "none"):
            return 0

        s = s.replace(",", ".")
        return int(float(s))
    except Exception:
        return 0

def _check_hdd_total_row(row):
    """
    Проверяет, что 'HDD, Гб' == ('SSD, Гб' + 'HDD Fast, Гб' + 'HDD Slow, Гб').
    Если столбца 'HDD, Гб' нет — молча пропускает.
    Возвращает текст ошибки или None.
    """
    # ищем доступное имя колонки HDD
    hdd_col = None
    for cand in ("HDD, Гб", "HDD, Гб.", "HDD"):
        if hasattr(row, "index") and cand in row.index:
            hdd_col = cand
            break

    if not hdd_col:
        return None  # в этой таблице HDD-итога нет — ничего не проверяем

    ssd  = _to_int(row.get("SSD, Гб",  row.get("SSD", 0)))
    hddf = _to_int(row.get("HDD Fast, Гб", row.get("HDD Fast", 0)))
    hdds = _to_int(row.get("HDD Slow, Гб", row.get("HDD Slow", 0)))
    hdd_total = _to_int(row.get(hdd_col, 0))

    summed = ssd + hddf + hdds
    if hdd_total != summed:
        return f"Значение '{hdd_col}' ({hdd_total}) не равно сумме SSD+HDD Fast+HDD Slow ({summed})."
    return None

def chek(serv, label, actual, desired, contur):
    actual = _to_int(actual)
    desired = _to_int(desired)
    contur  = _to_int(contur)
    # 1.31
    if (serv in ('Сервис управление развертыванием ПО (услуга 1.1.31)',)):
        if 'CPU' in label:
            if actual != (desired + contur): return report_ones(label, actual, -1, desired)
        elif 'RAM' in label:
            if actual != (desired + contur): return report_ones(label, actual, -1, desired)
        else:
            if actual != desired: return f"Неверный параметр {label} ({actual}). Требуется {desired}."
        return None

    # 1.9
    if (serv in ('Сервисы интеграционного взаимодействия (услуга 1.1.9)',)):
        if 'CPU' in label:
            if actual != (desired + contur): return report_ones(label, actual, -1, desired)
        elif 'RAM' in label:
            if actual != (desired + contur): return report_ones(label, actual, -1, desired)
        else:
            if actual != desired: return f"Неверный параметр {label} ({actual}). Требуется {desired}."
        return None

    # 1.1
    if (serv in ('Сервис транзакционной СУБД (услуга 1.1.1)',)):
        if 'CPU' in label:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        elif 'RAM' in label:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        elif 'Количество ОС' in label:
            if actual != desired: return report_ones(label, actual, -1, desired)
        if label == 'Тип ОС':
            if actual != desired:
                return f"Неверный параметр {label} ({actual}). Требуется {desired}."
        else:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        return None

    # 1.3
    if (serv in ('Сервис Key-value СУБД (in-memory) (услуга 1.1.3)',)):
        if 'CPU' in label:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        elif 'RAM' in label:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        elif 'Количество ОС' in label:
            if actual != desired: return report_ones(label, actual, -1, desired)
        elif label == 'Тип ОС':
            if actual != desired:
                return f"Неверный параметр {label} ({actual}). Требуется {desired}."
        else:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        return None

    # 1.4
    if (serv in ('Сервис СУБД полнотекстового индекса (услуга 1.1.4)',)):
        if 'CPU' in label:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        elif 'RAM' in label:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        elif 'Количество ОС' in label:
            if actual != desired: return report_ones(label, actual, -1, desired)
        elif label == 'Тип ОС':
            if actual != desired:
                return f"Неверный параметр {label} ({actual}). Требуется {desired}."
        else:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        return None

    # 1.10
    if (serv in ('Сервисы управления очередями сообщений (услуга 1.1.10)',)):
        if 'CPU' in label:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        elif 'RAM' in label:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        elif 'Количество ОС' in label:
            if actual != desired: return report_ones(label, actual, -1, desired)
        elif label == 'Тип ОС':
            if actual != desired:
                return f"Неверный параметр {label} ({actual}). Требуется {desired}."
        else:
            if actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)
        return None

    # дефолт для прочих сервисов
    if label == 'Тип ОС':
        if actual != desired:
            return f"Неверный параметр {label} ({actual}). Требуется {desired}."
    elif actual > desired * 8:  return report_ones(label, actual, 8)
    elif actual > desired * 5:  return report_ones(label, actual, 5)
    elif actual > desired * 3:  return report_ones(label, actual, 3)
    elif actual > desired * 1.5:return report_ones(label, actual, 1)
    elif actual < desired:     return report_ones(label, actual, 0, desired)

    return None
            
def chek18(serv, label, actual, desired, contur, row_dict, f18, contur_118):
    if serv == "Сервис IAM (услуга 1.1.13)" and row_dict is not None and contur_118[row_dict["usage_contour"]]:
        try:
            if (int(float(str(row_dict.get("cpu_iaas_min", 0)))) == 4 and
                int(float(str(row_dict.get("ram_min", 0)))) == 8 and
                int(float(str(row_dict.get("ssd_min", 0)))) == 0 and
                int(float(str(row_dict.get("hddf_min", 0)))) == 0 and
                int(float(str(row_dict.get("hdds_min", 0)))) == 100 and
                int(float(str(row_dict.get("os_type_min", 0)))) == 2 and
                int(float(str(row_dict.get("os_amount_min", 0)))) == 2):
                return None
        except Exception:

            pass

    if (serv == "Сервис журналирования (услуга 1.1.14)" and row_dict is not None) and f18 and contur_118[row_dict["usage_contour"]]:
        try:
            if (int(float(str(row_dict.get("cpu_iaas_min", 0)))) == 8 and
                int(float(str(row_dict.get("ram_min", 0)))) == 16 and
                int(float(str(row_dict.get("ssd_min", 0)))) == 200 and
                int(float(str(row_dict.get("hddf_min", 0)))) == 0 and
                int(float(str(row_dict.get("hdds_min", 0)))) == 100 and
                int(float(str(row_dict.get("os_type_min", 0)))) == 2 and
                int(float(str(row_dict.get("os_amount_min", 0)))) == 2):
                return None
        except Exception:
            pass

    if (serv == "Сервис аудита (услуга 1.1.15)" and row_dict is not None) and f18 and contur_118[row_dict["usage_contour"]]:
        try:
            if (int(float(str(row_dict.get("cpu_iaas_min", 0)))) == 8 and
                int(float(str(row_dict.get("ram_min", 0)))) == 8 and
                int(float(str(row_dict.get("ssd_min", 0)))) == 0 and
                int(float(str(row_dict.get("hddf_min", 0)))) == 0 and
                int(float(str(row_dict.get("hdds_min", 0)))) == 100 and
                int(float(str(row_dict.get("os_type_min", 0)))) == 2 and
                int(float(str(row_dict.get("os_amount_min", 0)))) == 2):
                return None
        except Exception:
            pass

    if (serv == "Сервис мониторинга (услуга 1.1.16)" and row_dict is not None) and f18 and contur_118[row_dict["usage_contour"]]:
        try:
            if (int(float(str(row_dict.get("cpu_iaas_min", 0)))) == 8 and
                int(float(str(row_dict.get("ram_min", 0)))) == 8 and
                int(float(str(row_dict.get("ssd_min", 0)))) == 200 and
                int(float(str(row_dict.get("hddf_min", 0)))) == 0 and
                int(float(str(row_dict.get("hdds_min", 0)))) == 100 and
                int(float(str(row_dict.get("os_type_min", 0)))) == 2 and
                int(float(str(row_dict.get("os_amount_min", 0)))) == 2):
                return None
        except Exception:
            pass

    actual = _to_int(actual)
    desired = _to_int(desired)
    contur  = _to_int(contur)

    # 1.15 — Сервис аудита
    if (serv in ('Сервис аудита (услуга 1.1.15)',)) and (contur != 0):
        if 'CPU' in label:
            if actual > (desired + 4 * contur) * 8:  return report_ones(label, actual, 8)
            elif actual > (desired + 4 * contur) * 5: return report_ones(label, actual, 5)
            elif actual > (desired + 4 * contur) * 3: return report_ones(label, actual, 3)
            elif actual > (desired + 4 * contur) * 1.5: return report_ones(label, actual, 1)
            elif actual < desired + (4 * contur):     return report_ones(label, actual, 0, desired + 4 * contur)
        elif 'RAM' in label:
            if actual > (desired + 8 * contur) * 8:  return report_ones(label, actual, 8)
            elif actual > (desired + 8 * contur) * 5: return report_ones(label, actual, 5)
            elif actual > (desired + 8 * contur) * 3: return report_ones(label, actual, 3)
            elif actual > (desired + 8 * contur) * 1.5: return report_ones(label, actual, 1)
            elif actual < desired + (8 * contur):     return report_ones(label, actual, 0, desired + 8 * contur)
        else:
            if label == 'Тип ОС':
                if actual != desired: return f"Неверный параметр {label} ({actual}). Требуется {desired}."
            elif actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > (desired + contur) * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)

    # 1.16 — Сервис мониторинга
    if (serv in ('Сервис мониторинга (услуга 1.1.16)',)) and (contur != 0):

        if 'CPU' in label:
            if actual > (desired + 2) * 8:  return report_ones(label, actual, 8)
            elif actual > (desired + 2) * 5: return report_ones(label, actual, 5)
            elif actual > (desired + 2) * 3: return report_ones(label, actual, 3)
            elif actual > (desired + 2) * 1.5: return report_ones(label, actual, 1)
            elif actual < desired + 2:        return report_ones(label, actual, 0, desired + 2)
        elif 'RAM' in label:
            if actual > (desired + 2) * 8:  return report_ones(label, actual, 8)
            elif actual > (desired + 2) * 5: return report_ones(label, actual, 5)
            elif actual > (desired + 2) * 3: return report_ones(label, actual, 3)
            elif actual > (desired + 2) * 1.5: return report_ones(label, actual, 1)
            elif actual < desired + 2:        return report_ones(label, actual, 0, desired + 2)
        else:
            if 'Тип ОС' in label:
                if actual != desired: return f"Неверный параметр {label} ({actual}). Требуется {desired}."
            elif actual > desired * 8: return report_ones(label, actual, 8)
            elif actual > desired * 5: return report_ones(label, actual, 5)
            elif actual > desired * 3: return report_ones(label, actual, 3)
            elif actual > desired * 1.5: return report_ones(label, actual, 1)
            elif actual < desired: return report_ones(label, actual, 0, desired)

    # 1.14 — Сервис журналирования
    if (serv in ('Сервис журналирования (услуга 1.1.14)',)) and (contur != 0):
        if 'CPU' in label:
            if actual != (desired + 4 * contur): return report_ones(label, actual, -1, desired + 4 * contur)
        elif 'RAM' in label:
            if actual != (desired + 8 * contur): return report_ones(label, actual, -1, desired + 8 * contur)
        else:
            if actual != desired: return f"Неверный параметр {label} ({actual}). Требуется {desired}."

    # 1.13 — Сервис IAM
    if (serv in ('Сервис IAM (услуга 1.1.13)')):
        if 'CPU' in label:
            if actual != desired: return report_ones(label, actual, -1, desired)
        elif 'RAM' in label:
            if actual != desired: return report_ones(label, actual, -1, desired)
        else:
            if actual != desired: return f"Неверный параметр {label} ({actual}). Требуется {desired}."

    return None


def check_vitrin_fixed_params_rows(df_all: pd.DataFrame) -> list[str]:
    """
    Если заказ витринный, то для строк с услугами 1.1.13/1.1.14/1.1.15/1.1.16
    проверяем строго IaaS-параметры. При несовпадении — ошибка с № п/п.
    """
    if df_all is None or df_all.empty:
        return []

    df = df_all.copy()

    # статусы как обычно (если у тебя другой набор — оставь свой)
    valid_statuses = {"Новая услуга", "Заказанная услуга", "Изменение заказанной услуги"}
    if "service_status" in df.columns:
        df = df[df["service_status"].astype(str).str.strip().isin(valid_statuses)]

    # определяем витринность: в заказе есть 1.1.18 и нет лишних услуг (кроме 1.1.31)
    services_all = df["service_name"].astype(str).tolist()

    def _has(code: str) -> bool:
        return any(re.search(rf"\(услуга\s*{re.escape(code)}\)", s) for s in services_all)

    def _allowed_only() -> bool:
        allowed = {"1.1.13", "1.1.14", "1.1.15", "1.1.16", "1.1.18", "1.1.31"}
        for s in services_all:
            m = re.search(r"\(услуга\s*([0-9.]+)\)", str(s))
            if m and m.group(1) not in allowed:
                return False
        return True

    if not (_has("1.1.18") and _allowed_only()):
        return []

    # эталоны по скрину (IaaS блок)
    EXPECTED_BY_CODE = {
        "1.1.16": {"cpu_iaas": 8, "ram": 8,  "ssd": 200, "hddf": 0, "hdds": 100, "os_type": 2, "os_amount": 2},
    }

    need_cols = set().union(*[set(v.keys()) for v in EXPECTED_BY_CODE.values()])
    missing_cols = [c for c in need_cols if c not in df.columns]
    if missing_cols:
        return [f"Витринный заказ: нет колонок IaaS для проверки параметров: {missing_cols}"]

    errors: list[str] = []

    for idx, row in df.iterrows():
        sname = str(row.get("service_name", "")).strip()
        m = re.search(r"\(услуга\s*([0-9.]+)\)", sname)
        if not m:
            continue

        code = m.group(1)
        if code not in EXPECTED_BY_CODE:
            continue

        expected = EXPECTED_BY_CODE[code]
        bad = []

        for col, exp in expected.items():
            try:
                val = int(float(row.get(col, 0)))
            except Exception:
                bad.append(f"{col}=<не число> (нужно {exp})")
                continue

            if val != exp:
                bad.append(f"{col}={val} (нужно {exp})")

        if bad:
            row_no = row.get("№ п/п", idx)  # № п/п из Excel, если есть
            contour = str(row.get("usage_contour", "")).strip()
            errors.append(
                f"Строка {row_no} (контур '{contour}', {sname}): неверные параметры IaaS:\n"
                + "\n".join([f"   - {x}" for x in bad])
            )

    return errors



def chek2(label, actual):
    if (label in ('Предоставление пространства имен на кластере Kubernetes (услуга 1.2.1.2)', 'Выделение места (услуга 1.2.1.3)')):
        if 'Тип операционной системы' in label:
            if actual!=2:
                return f'Не верный параметр Тип операционной системы ({actual}. Должен быть 2)'
        if 'Количество операционных систем' in label:
            if actual!=0:
                return f'Не верный параметр Тип операционной системы ({actual}. Должен быть 0)'
    elif (label in ('Предоставление виртуальной машины (услуга 1.2.1.1)')):
        if 'Количество операционных систем' in label:
            if actual!=1:
                return f'Не верный параметр Тип операционной системы ({actual}. Должен быть 1)'
            
FULL_NAME_118 = (
    'Сервис «Витрина данных» (услуга 1.1.18)'
)
FULL_NAME_113 = 'Сервис IAM (услуга 1.1.13)'  # Замените на ваше точное полное название 1.13

# —————————————————————————————————
# 3) Эталонные параметры для 1.13
EXPECTED_PARAMS = {
    'cpu_iaas':  4,
    'ram':       8,
    'ssd':       0,
    'hddf':      0,
    'hdds':      100,
    'os_type':   2,
    'os_amount': 2
}

# —————————————————————————————————
def check_1_18(df: pd.DataFrame) -> list:
    # Переименуем
    # Уберём пробелы по краям, чтобы точное сравнение работало надёжно
    df['service_name'] = df['service_name'].str.strip()
    
    # Найдём все контуры, где service_name точно равно FULL_NAME_118
    mask_118 = df["service_name"].astype(str).str.contains(r"\(услуга\s*1\.1\.18\)", regex=True, na=False)
    contours_with_118 = df.loc[mask_118, "usage_contour"].unique()
    
    warnings = []
    for contour in sorted(contours_with_118):
        sub = df[df['usage_contour'] == contour]
        # Ищем строки с полным именем 1.13
        mask_113 = sub["service_name"].astype(str).str.contains(r"\(услуга\s*1\.1\.13\)", regex=True, na=False)
        sub113 = sub[mask_113]

        expected = {'cpu_iaas': 4, 'ram': 8, 'ssd': 0, 'hddf': 0, 'hdds': 100, 'os_type': 2, 'os_amount': 2}

        # sub113 — все строки 1.1.13 в данном контуре
        # если есть хотя бы одна полностью правильная — НЕ РУГАЕМСЯ ВООБЩЕ
        has_ok = False
        for _, r in sub113.iterrows():
            ok = True
            for col, exp in expected.items():
                try:
                    v = int(float(r.get(col)))
                except Exception:
                    ok = False
                    break
                if v != exp:
                    ok = False
                    break
            if ok:
                has_ok = True
                break

        # если нет ни одной правильной — тогда выводим построчные ошибки по каждой 1.1.13
        if not has_ok:
            for _, r in sub113.iterrows():
                bad = []
                for col, exp in expected.items():
                    try:
                        v = int(float(r.get(col)))
                    except Exception:
                        param_name = PARAM_LABELS.get(col, col)
                        bad.append(f"Параметр {param_name} (<не число>) не верны по ТК. Требуется значение {exp}.")
                        continue
                    if v != exp:
                        param_name = PARAM_LABELS.get(col, col)
                        bad.append(
                            f"Параметр {param_name} ({v}) не верны по ТК. Требуется значение {exp}."
                        )

                if bad:
                    row_no = r.get("№ п/п", r.name)
                    kontur = str(r.get("usage_contour", "")).strip().upper()
                    sname = str(r.get("service_name", "")).strip()
                    warnings.append(
                        f"Строка {row_no} (контур '{kontur}', {sname}): неверные параметры IaaS:\n"
                        + "\n".join([f"   - {x}" for x in bad])
                    )
    
    return warnings



def full_chek2(row):
    m=[]

    service = str(row["Наименование услуги"]).strip()
    contour = str(row["Контур использования"]).strip().upper()
    vcpu = _to_int(row.get("vCPU, ядер", 0))
    ram = _to_int(row.get("RAM, Гб", 0))
    ssd = _to_int(row.get("SSD, Гб", 0))
    hddf = _to_int(row.get("HDD Fast, Гб", 0))
    hdds = _to_int(row.get("HDD Slow, Гб", 0))
    disk_total = ssd + hddf + hdds
    os_type = str(row["Тип операционной системы"]).strip()
    os_type = _to_int(float(str(os_type).strip().replace(',', '.')))
    os_amount = _to_int(row["Количество операционных систем, шт."]or 0)
    coef = _to_int(row["Коэф-т переподписки"] or 0)

    if service == "Предоставление виртуальной машины (услуга 1.2.1.1)":
        if vcpu < 2:
            m.append(report_ones("vCPU, ядер", vcpu, 0, 2))

        if ram < 2:
            m.append(report_ones("RAM, Гб", ram, 0, 2))

        if disk_total < 50:
            # В сообщении явно показываем, что это сумма трёх колонок
            m.append(report_ones("Диск (SSD+HDD Fast+HDD Slow), Гб", disk_total, 0, 50))

    # 1. VM (2.1.1), DEV/TEST
    if service == "Предоставление виртуальной машины (услуга 1.2.1.1)" and contour in ("DEV", "TEST"):
        if coef != 10: m.append(report_ones("Коэф-т переподписки", coef,-1, 10))
        if vcpu == 0: m.append(report_ones("vCPU, ядер", vcpu, -1,'Не нулевое'))
        if ram == 0: m.append(report_ones("RAM, Гб", ram,-1, 'Не нулевое'))
        if (ssd == 0 and hddf == 0 and hdds == 0): m.append('Хотя бы 1 из параметров: SSD, Гб, HDD Fast, Гб, HDD Slow, Гб должен быть не нулевым')
        if os_type == 0: m.append(report_ones("Тип операционной системы", os_type,-1, 'Не нулевое'))
        if os_amount != 1: m.append(report_ones("Количество операционных систем, шт.",os_amount, -1, 1))

    # 2. VM (2.1.1), PROD
    if service == "Предоставление виртуальной машины (услуга 1.2.1.1)" and contour == "PROD":
        if coef not in (3, 5): m.append(report_ones("Коэф-т переподписки", coef,-1, "значение 3 или 5"))
        if vcpu == 0: m.append(report_ones("vCPU, ядер", vcpu, -1,'Не нулевое'))
        if ram == 0: m.append(report_ones("RAM, Гб", ram, -1,'Не нулевое'))
        if (ssd == 0 and hddf == 0 and hdds == 0): m.append('Хотя бы 1 из параметров: SSD, Гб, HDD Fast, Гб, HDD Slow, Гб должен быть не нулевым')
        if os_type == 0: m.append(report_ones("Тип операционной системы", os_type, -1,'Не нулевое'))
        if os_amount != 1: m.append(report_ones("Количество операционных систем, шт.", os_amount, -1,1))

    # 3. Kubernetes (2.1.2)
    if service == "Предоставление пространства имен на кластере Kubernetes (услуга 1.2.1.2)":
        if vcpu == 0: m.append(report_ones("vCPU, ядер", vcpu, -1,'Не нулевое'))
        if ram == 0: m.append(report_ones("RAM, Гб", ram,-1, 'Не нулевое'))
        if ssd != 0: m.append(report_ones("SSD, Гб", ssd,-1, 0))
        if hddf != 0: m.append(report_ones("HDD Fast, Гб", hddf, -1,0))
        if hdds != 0: m.append(report_ones("HDD Slow, Гб", hdds,-1, 0))
        if os_type!=2: m.append(report_ones("Тип операционной системы", os_type,-1, 2))
        if os_amount != 0: m.append(report_ones("Количество операционных систем, шт.", os_amount, -1, 0))

    # 4. Disk space (2.1.3)
    if service == "Выделение места (услуга 2.1.3)":
        if vcpu != 0: m.append(report_ones("vCPU, ядер", vcpu,-1, 0))
        if ram != 0: m.append(report_ones("RAM, Гб", ram,-1, 0))
        if ssd != 0: m.append(report_ones("SSD, Гб", ssd,-1, 0))
        if hddf != 0: m.append(report_ones("HDD Fast, Гб", hddf,-1, 0))
        if hdds == 0: m.append(report_ones("HDD Slow, Гб", hdds, -1,'Не нулевое'))
        if os_type!=2: m.append(report_ones("Тип операционной системы", os_type,-1, 2))
        if os_amount != 0: m.append(report_ones("Количество операционных систем, шт.", os_amount,-1, 0))
    return m

def check_service_118_by_contours(df_all):
    """
    Проверяет наличие услуги 1.18 в каждом контуре.
    df_all — датафрейм target с колонками 'service_name' и 'usage_contour'.

    Возвращает словарь вида:
      {"DEV": True/False, "TEST": True/False, "PROD": True/False, "ПСИ": True/False, "HT": True/False}
    """
    contours = ["DEV", "TEST", "PROD", "ПСИ", "HT"]
    result = {c: False for c in contours}

    if df_all.empty:
        return result

    # нормализуем текст
    df = df_all.copy()
    df = df[~df["service_name"].astype(str).str.contains("услуга 1.1.12", case=False, regex=False, na=False)]
    df["service_name"] = df["service_name"].astype(str).str.strip()
    df["usage_contour"] = df["usage_contour"].astype(str).str.strip().str.upper()
    for c in contours:
        mask_contour = df["usage_contour"] == c
        mask_service = df["service_name"].astype(str).str.contains("услуга 1.1.18", case=False, regex=False, na=False)
        if df[mask_contour & mask_service].shape[0] > 0:
            result[c] = True

    return result
import re

def check_vitrin_iam_iaas_params_by_contours(df_all):
    """
    Для витринного заказа: на каждом контуре должна существовать ХОТЯ БЫ ОДНА услуга 1.1.13
    с параметрами ИМЕННО из блока IaaS:
      cpu_iaas=4, ram=8, ssd=0, hddf=0, hdds=100, os_type=2, os_amount=2
    """
    if df_all is None or df_all.empty:
        return []

    df = df_all.copy()

    # берём только нужные статусы (как у тебя в остальном проекте)
    valid_statuses = {"Новая услуга", "Заказанная услуга", "Изменение заказанной услуги"}
    if "service_status" in df.columns:
        df = df[df["service_status"].astype(str).str.strip().isin(valid_statuses)]

    # определяем "витринность" по списку услуг в заказе
    services_all = df["service_name"].astype(str).tolist()

    def _has(code: str) -> bool:
        return any(re.search(rf"\(услуга\s*{re.escape(code)}\)", s) for s in services_all)

    def _allowed_only() -> bool:
        allowed = {"1.1.13", "1.1.14", "1.1.15", "1.1.16", "1.1.18", "1.1.31"}
        for s in services_all:
            m = re.search(r"\(услуга\s*([0-9.]+)\)", str(s))
            if m and m.group(1) not in allowed:
                return False
        return True

    if not _has("1.1.18"):
        return []

    # эталон IaaS (ВАЖНО: используем именно cpu_iaas/ram/ssd/hddf/hdds/os_type/os_amount)
    expected = {
        "cpu_iaas": 4,
        "ram": 8,
        "ssd": 0,
        "hddf": 0,
        "hdds": 100,
        "os_type": 2,
        "os_amount": 2,
    }
    expected_116 = {
        "cpu_iaas": 8,
        "ram": 8,
        "ssd": 200,
        "hddf": 0,
        "hdds": 100,
        "os_type": 2,
        "os_amount": 2,
    }

    # проверяем, что колонки вообще есть
    missing_cols = [c for c in expected.keys() if c not in df.columns]
    if missing_cols:
        return [f"Витринный заказ: в target нет колонок IaaS для проверки 1.1.13: {missing_cols}\n"]

    comments = []

    # контуры, где вообще есть услуги (или можно фиксированный список)
    df["usage_contour"] = df["usage_contour"].astype(str).str.strip()
    contours = sorted(set(df["usage_contour"].str.upper()) - {""})

    for contour in contours:
        sub = df[df["usage_contour"].str.upper() == contour]
        iam = sub[sub["service_name"].astype(str).str.contains(r"\(услуга\s*1\.1\.13\)", regex=True)]
        if iam.empty:
            comments.append(f"Контур '{contour}' — отсутствует услуга 1.1.13\n")
            continue

        # есть ли хотя бы одна строка 1.1.13 с нужными IaaS параметрами
        ok_any = False
        for _, r in iam.iterrows():
            ok = True
            for col, exp in expected.items():
                try:
                    val = r[col]
                    v = int(float(val))  # нормализация 4 / 4.0 / "4"
                except Exception:
                    ok = False
                    break
                if v != exp:
                    ok = False
                    break
            if ok:
                ok_any = True
                break

        if not ok_any:
            comments.append(
                f"Контур '{contour}' — нет ни одной 1.1.13 с IaaS параметрами "
                f"(CPU=4,RAM=8,SSD=0,HDD Fast=0,HDD Slow=100,Тип ОС=2,Кол-во ОС=2)\n"
            )
        # --- Витринный заказ: все 1.1.16 должны иметь особые IaaS параметры ---
        svc_116 = sub[sub["service_name"].astype(str).str.contains(r"\(услуга\s*1\.1\.16\)", regex=True)]

        if not svc_116.empty:
            for idx, r in svc_116.iterrows():
                ok = True
                bad = []

                for col, exp in expected_116.items():
                    try:
                        v = int(float(r[col]))
                    except Exception:
                        ok = False
                        param_name = PARAM_LABELS.get(col, col)
                        bad.append(f"Параметр {param_name} (<не число>) не верны по ТК. Требуется значение {exp}.")
                        continue

                    if v != exp:
                        ok = False
                        param_name = PARAM_LABELS.get(col, col)
                        bad.append(f"Параметр {param_name} ({v}) не верны по ТК. Требуется значение {exp}.")

                if not ok:
                    comments.append(
                        f"Контур '{contour}' — 1.1.16 не соответствует IaaS параметрам: "
                        + ", ".join(bad)
                        + "\n"
                    )


    return comments

        