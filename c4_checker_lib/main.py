
# файл 1 получение диаграммы = select_diagram_from_drawio.py       Этот код открывает файл Drawio в формате XML, отображает пользователю список доступных листов (диаграмм), запрашивает номер для выбора и сохраняет имя выбранной диаграммы в глобальном хранилище.
# файл 2 ищем поля в кубиках = extract_c4_names.py                 Этот код заглядывает внутрь файла Drawio, чтобы распаковать спрятанную там информацию о диаграмме и составить список всех архитектурных объектов C4
from diagram_analis.select_diagram_from_drawio import select_diagram_from_drawio

from c4_chek import *
from gui import *
def main():
    drawio_file_path, excel_file_path = start_gui()


    # Запускаем модуль, который извлекает перечень услуг.  Теперь функция сама не печатает.
    result = select_diagram_from_drawio(drawio_file_path)




    # Запускаем модуль 3 для извлечения и сохранения данных C4
    c4_data =extract_c4_names(drawio_file_path) # Вызываем функцию из модуля 3

    result = parse_services_from_excel(excel_file_path)

    # Оставляем только те услуги, где есть "("
    result = {name: count for name, count in result.items() if "(у" in name}
    c4_tech_data = get_c4_tech_data()

    c4_tech_data = merge_c4_tech_data(c4_tech_data)

    errors = compare_services(result, c4_tech_data) # ← твоя функция сравнения

    if errors:
        show_errors(errors)
    else:
        print("Все услуги совпадают!")
if __name__ == "__main__":
    main()

