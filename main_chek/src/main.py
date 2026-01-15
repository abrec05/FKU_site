import sys
import logging
from PyQt6 import QtWidgets
from src.utils import setup_logging
import sys

def main():
    setup_logging(
        current_log='logs/current_log',
        history_log='logs/main_log.log'
    )
    logging.info("Запуск приложения GUI")
    app = QtWidgets.QApplication(sys.argv)
    # Пример использования функции
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
