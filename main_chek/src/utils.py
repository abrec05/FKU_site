import os
import logging

import os
import logging

def setup_logging(current_log='logs/current_log', history_log='logs/main_log.log', clear=True):
    # Создаем папку logs, если её нет
    log_dir = os.path.dirname(current_log)
    os.makedirs(log_dir, exist_ok=True)

    # Гарантируем, что оба файла существуют
    for log_file in [current_log, history_log]:
        if not os.path.exists(log_file):
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('')  # создаёт пустой файл

    # Очищаем current_log при необходимости
    if clear:
        with open(current_log, 'w', encoding='utf-8') as f:
            f.truncate(0)

    # Удаляем старые хендлеры (если есть)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)

    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(current_log, encoding='utf-8'),
            logging.FileHandler(history_log, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def write_results(df, output_path: str):
    """
    Сохранить DataFrame в Excel.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_excel(output_path, index=False)
    logging.info(f"Результаты сохранены в {output_path}")
