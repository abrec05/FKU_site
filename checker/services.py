import config.global_word_book as gwb

from diagram_analis.extract_c4_names import extract_c4_names, get_c4_tech_data
from c4_chek import parse_services_from_excel, merge_c4_tech_data, compare_services

def run_check(drawio_path: str, excel_path: str, sheet_name: str | None = None) -> dict:
    # сброс глобального состояния между запусками (важно для веба)
    try:
        gwb.c4_tech_data.clear()
    except Exception:
        pass

    # если лист не передан — всё равно ставим (иначе extract_c4_names ругнётся)
    gwb.SELECTED_SHEET_NAME = sheet_name

    # 1) вытащить услуги из drawio
    extract_c4_names(drawio_path)

    # 2) распарсить excel
    result = parse_services_from_excel(excel_path)
    result = {name: count for name, count in result.items() if "(у" in name}

    # 3) получить данные из C4 и сравнить
    c4_data = get_c4_tech_data()
    c4_data = merge_c4_tech_data(c4_data)

    errors = compare_services(result, c4_data)
    return errors
