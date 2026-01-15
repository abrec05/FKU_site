import pandas as pd
from main_chek.src.parsers.universal_parser import *



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
       

def _to_int(x):
    try:
        return int(float(str(x).strip().replace(',', '.')))
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
    actual = int(actual)
    desired = int(desired)
    contur  = int(contur)
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

    actual = int(actual)
    desired = int(desired)
    contur  = int(contur)

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
    'Сервис «Типовое тиражируемое программное обеспечение витрин данных» '
    '(«Витрина НСУД»)» (услуга 1.1.18)'
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
    contours_with_118 = df.loc[
        df['service_name'] == FULL_NAME_118,
        'usage_contour'
    ].unique()
    
    warnings = []
    for contour in sorted(contours_with_118):
        sub = df[df['usage_contour'] == contour]
        # Ищем строки с полным именем 1.13
        sub113 = sub[sub['service_name'] == FULL_NAME_113]
        
        if sub113.empty:
            warnings.append(
                f'Контур "{contour}": '
                f'нужно добавить строку "{FULL_NAME_113}" '
                f'с параметрами {EXPECTED_PARAMS}'
            )
        else:
            # Проверяем, есть ли среди них хотя бы одна строка,
            # у которой _все_ столбцы из EXPECTED_PARAMS совпадают
            mask = (
                sub113[list(EXPECTED_PARAMS)] ==
                pd.Series(EXPECTED_PARAMS)
            ).all(axis=1)
            if not mask.any():
                warnings.append(
                    f'Контур "{contour}": услуга 1.1.13 есть, '
                    'но ни одна запись не соответствует всем параметрам; '
                    f'ожидается {EXPECTED_PARAMS}'
                )
    
    return warnings
    
def full_chek2(row):
    m=[]
    service = str(row["Наименование услуги"]).strip()
    contour = str(row["Контур использования"]).strip().upper()

    vcpu = int(row["vCPU, ядер"] or 0)
    ram = int(row["RAM, Гб"] or 0)
    ssd = int(row["SSD, Гб"] or 0)
    hddf = int(row["HDD Fast, Гб"] or 0)
    hdds = int(row["HDD Slow, Гб"] or 0)
    os_type = str(row["Тип операционной системы"]).strip()
    os_type = int(float(str(os_type).strip().replace(',', '.')))
    os_amount = int(row["Количество операционных систем, шт."] or 0)
    coef = int(row["Коэф-т переподписки"] or 0)

    # 1. VM (2.1.1), DEV/TEST
    if service == "Предоставление виртуальной машины (услуга 1.2.1.1)" and contour in ("DEV", "TEST"):
        if coef != 10: m.append(report_ones("Коэф-т переподписки", coef,-1, 10))
        if vcpu == 0: m.append(report_ones("vCPU, ядер", vcpu, -1,'Не нулевое'))
        if ram == 0: m.append(report_ones("RAM, Гб", ram,-1, 'Не нулевое'))
        if (ssd == 0 and hddf == 0 and hdds == 0): m.append('Хотя бы 1 из параметров: SSD, Гб, HDD Fast, Гб, HDD Slow, Гб должен быть не нулевым')
        if os_type == 0: m.append(report_ones("Тип операционной системы", os_type,-1, 'Не нулевое'))
        if os_amount != 1: m.append(report_ones("Количество операционных систем, шт.",-1, os_amount, 1))

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

        