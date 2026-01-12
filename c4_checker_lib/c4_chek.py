import pandas as pd
from diagram_analis.extract_c4_names import *

from tkinter import Tk
from tkinter.filedialog import askopenfilename






def split_into_tables(df):
    """Разбивает лист на таблицы по пустым строкам."""
    tables = []
    current = []

    for _, row in df.iterrows():
        if row.isna().all():
            if current:
                tables.append(pd.DataFrame(current).reset_index(drop=True))
                current = []
        else:
            current.append(row)

    if current:
        tables.append(pd.DataFrame(current).reset_index(drop=True))

    return tables


def find_header_row(table):
    """Ищет строку, где есть заголовок 'наименование услуги'."""
    for i, row in table.iterrows():
        row_lower = row.astype(str).str.lower()
        if any("наимен" in x for x in row_lower) and any("услуг" in x for x in row_lower):
            return i
    return None


def parse_services_from_excel(file_path):
    xls = pd.read_excel(file_path, sheet_name=None, header=None)
    allowed_indexes = {1, 2, 3}  # 0-based: 1=лист2, 2=лист3, 3=лист4

    for idx, (sheet_name, df) in enumerate(xls.items()):
        if idx not in allowed_indexes:
            continue
    service_counts = {}

    for sheet_name, df in xls.items():

        tables = split_into_tables(df)

        for table in tables:

            # ✅ ВСЕГДА берём только столбец E
            COL_INDEX = 4  # E = 4 (0-based)

            # если в таблице нет столбца E — пропускаем
            if table.shape[1] <= COL_INDEX:
                continue

            services = table.iloc[:, COL_INDEX].dropna()



            AM_INDEX = 38  # AM = 39-й столбец, индекс 38 (A=0)

            for i, service in services.items():
                service = str(service).strip()
                if "1." in service:
                    service = service.replace("1.", "", 1)
                # ✅ ФИЛЬТР: сохраняем ТОЛЬКО строки с "услуга"
                if "услуга" not in service.lower():
                    continue

                key = service


                service_counts[key] = service_counts.get(key, 0) + 1

    return service_counts


def merge_c4_tech_data(data):
    merged = {}

    for entry in data:
        service_name = entry[0][0]  # строка с названием
        number = entry[1][0]  # номер услуги
        count = entry[1][1]  # количество

        if service_name not in merged:
            merged[service_name] = [number, count]
        else:
            merged[service_name][1] += count

    # Превращаем обратно в твой формат
    result = []
    for name, (number, count) in merged.items():
        result.append([[name], [number, count]])

    return result

def compare_services(result, c4_tech_data):
    errors = {}


    aggregated_c4 = {}

    for entry in c4_tech_data:
        name = entry[0][0]
        count = entry[1][1]

        aggregated_c4[name] = aggregated_c4.get(name, 0) + count

    # Проверка каждого элемента C4
    for service_name, needed_count in aggregated_c4.items():

        if service_name not in result:
            errors[service_name] = f'Услуга "{service_name}" отсутствует в файле Excel'
            continue

        file_count = result[service_name]

        if file_count < needed_count:
            diff = needed_count - file_count
            errors[service_name] = (
                f'В файле меньше услуг "{service_name}" на {diff}'
            )

    return errors


