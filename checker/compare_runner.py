import warnings

def run_compare(new_excel_path: str, old_excel_path: str) -> str:
    """Запуск сравнения заказов (WEB) и возврат текста отчёта."""
    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

    # импорт внутри функции, чтобы Django не падал при старте
    from ost_zak import sravn

    return sravn.run_web(new_excel_path, old_excel_path)