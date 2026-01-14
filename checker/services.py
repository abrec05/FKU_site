import c4_checker_lib.с4_config.global_word_book as gwb

from c4_checker_lib.diagram_analis.extract_c4_names import extract_c4_names, get_c4_tech_data
from c4_checker_lib.c4_chek import parse_services_from_excel, merge_c4_tech_data, compare_services


def run_services_check(drawio_path: str, excel_path: str, sheet_name: str | None) -> dict:
    # сброс глобального состояния
    try:
        gwb.c4_tech_data.clear()
    except Exception:
        pass

    gwb.SELECTED_SHEET_NAME = sheet_name
    extract_c4_names(drawio_path)

    result = parse_services_from_excel(excel_path)
    result = {name: count for name, count in result.items() if "(у" in name}

    c4_data = get_c4_tech_data()
    c4_data = merge_c4_tech_data(c4_data)

    errors = compare_services(result, c4_data)
    return errors


def run_diagram_check(drawio_path: str, sheet_name: str | None) -> dict:
    """
    TODO: сюда подключим твою 'проверку диаграммы'.
    Пока просто проверим, что лист выбран и C4 данные извлекаются.
    """
    try:
        gwb.c4_tech_data.clear()
    except Exception:
        pass

    gwb.SELECTED_SHEET_NAME = sheet_name

    # если парсинг упадёт — это будет видно как исключение (в view мы его покажем)
    extract_c4_names(drawio_path)

    # пока без конкретных правил — возвращаем пусто (значит "ок")
    return {}
