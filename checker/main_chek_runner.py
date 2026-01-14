import warnings
from pathlib import Path
from django.conf import settings
def run_main_chek(target_path: str, over: bool = False) -> str:
    """
    Запускает проверку из main_chek и возвращает ТОЛЬКО итоговый report (строку).
    target_path — путь к загруженному Excel (это и есть "target").
    """
    # чтобы не лезли варнинги openpyxl в вывод
    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

    # импортируем "движок" из main_chek
    from main_chek.src.parsers.config_parser import ConfigParser
    from main_chek.src.excel_processor import ExcelProcessor
    from main_chek.src.context_builder import ContextBuilder
    import main_chek.src.context_builder as cr

    cr.ov = bool(over)

    cfg = ConfigParser("config")
    proc = ExcelProcessor(cfg)
    builder = ContextBuilder(cfg, proc)

    default_test_zak = Path(settings.BASE_DIR) / "main_chek" / "data" / "test_zak.xlsx"
    if not default_test_zak.exists():
        return f"Ошибка: не найден эталонный файл: {default_test_zak}"

    try:
        _, report, _ = builder.build(target_path, str(default_test_zak))
        return report
    except Exception as e:
        return f"Ошибка при проверке услуг: {e}"
