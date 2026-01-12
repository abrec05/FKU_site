import xml.etree.ElementTree as ET
from typing import List, Optional
# Импортируем модуль config для доступа к global_word_book
import config.global_word_book as gwb

def select_diagram_from_drawio(drawio_file_path: str) -> Optional[ET.Element]:
    """
    Открывает файл Drawio, отображает список доступных листов (диаграмм) и позволяет пользователю выбрать один.
    Выбранное имя листа сохраняется в global_word_book.

    Args:
        drawio_file_path (str): Путь к файлу .drawio.

    Returns:
        Optional[ET.Element]: Выбранный элемент <diagram> или None в случае ошибки.
    """
    try:
        with open(drawio_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        root = ET.fromstring(xml_content)
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл не найден по пути: {drawio_file_path}")
        return None
    except ET.ParseError as e:
        print(f"❌ Ошибка XML: Ошибка разбора XML в файле: {e}")
        return None
    except Exception as e:
        print(f"❌ Ошибка при работе с файлом: {e}")
        return None

    diagrams = root.findall("diagram")
    if not diagrams:
        print("❌ Ошибка: В файле не найдено ни одного листа (диаграммы).")
        return None

    print("\nДоступные листы (диаграммы) в файле:")
    for i, diagram in enumerate(diagrams):
        name = diagram.attrib.get("name", f"Лист {i + 1}")
        print(f"{i + 1}. {name}")

    while True:
        try:
            sheet_number = int(input("Введите номер листа, который хотите проанализировать: "))
            if 1 <= sheet_number <= len(diagrams):
                selected_diagram = diagrams[sheet_number - 1]
                # Сохраняем имя выбранного листа в global_word_book
                gwb.SELECTED_SHEET_NAME = selected_diagram.attrib.get("name", f"Лист {sheet_number}")
                return selected_diagram
            else:
                print("❌ Ошибка: Некорректный номер листа. Попробуйте еще раз.")
        except ValueError:
            print("❌ Ошибка: Введите целое число, представляющее номер листа.")

def get_diagram_name(diagram: ET.Element) -> str:
    """
    Извлекает имя диаграммы из элемента <diagram>.

    Args:
      diagram (ET.Element): Элемент <diagram>.

    Returns:
      str: Имя диаграммы или "(Без имени)", если имя отсутствует.
    """
    return diagram.attrib.get("name", "(Без имени)")
