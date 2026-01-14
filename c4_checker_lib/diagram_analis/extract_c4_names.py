import xml.etree.ElementTree as ET
from typing import List, Dict, Union
from math import *
import c4_checker_lib.с4_config.global_word_book as gwb

from c4_checker_lib.с4_config.imena_uslug import *

def extract_c4_names(drawio_file_path: str) -> List[str]:
    """
    Извлекает элементы с атрибутами 'c4Application' и 'C___c4count' 
    из файла Drawio и сохраняет их данные в global_word_book.
    Если в 'c4Application' несколько сервисов через запятую,
    каждый сервис записывается отдельно с полным именем из IMENA_USLUG.

    Args:
        drawio_file_path (str): Путь к файлу .drawio.

    Returns:
        List[str]: Список всех значений 'c4Application'.
    """
    c4_technologies: List[str] = []

    try:
        with open(drawio_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        root = ET.fromstring(xml_content)
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл не найден по пути: {drawio_file_path}")
        return []
    except ET.ParseError as e:
        print(f"❌ Ошибка XML: {e}")
        return []

    diagrams = root.findall("diagram")
    if not diagrams:
        print("❌ Ошибка: В файле не найдено ни одного листа (диаграммы).")
        return []

    selected_diagram = None
    if gwb.SELECTED_SHEET_NAME:
        for diagram in diagrams:
            if diagram.attrib.get("name") == gwb.SELECTED_SHEET_NAME:
                selected_diagram = diagram
                break
        if not selected_diagram:
            print(f"❌ Лист с именем '{gwb.SELECTED_SHEET_NAME}' не найден.")
            return []
    else:
        print("❌ Имя листа не выбрано. Установите 'SELECTED_SHEET_NAME'.")
        return []

    print(f"✅ Выбран лист: \"{selected_diagram.attrib.get('name', '(Без имени)')}\"")
    diagram_root = ET.fromstring(ET.tostring(selected_diagram, encoding='unicode'))

    fapp=1
    for element in diagram_root.iter():
        if 'c4Application' in element.attrib:
            fapp=1
            f=False
            if 'c4count' in element.attrib:
                f=True
            
            number_services_raw = element.attrib['c4Application']
            full_service_name='1'

            number_services_list = [s.strip() for s in number_services_raw.split()]
            for number_service in number_services_list:
                # Ищем полное имя услуги в IMENA_USLUG
                  # по умолчанию просто номер
                if number_service == '1.12':
                    fapp = 3
                    matched = False  # флаг: нашли ли совпадение по COMPONENT_1_12

                    # --- 1. Проверяем COMPONENT_1_12 (комментарии в c4Application) ---
                    for comp_key, comp_value in COMPONENT_1_12.items():
                        for token in number_services_list:
                            if token.lower() == comp_key:
                                full_service_name = "Сервис управления процессами (1.12)"
                                record = ['1.12', 1, comp_value]

                                update_global_word_book(
                                    service_name=full_service_name,
                                    NumberService=number_service,
                                    element_dict=record,
                                    f=fapp
                                )
                                matched = True
                                break
                        if matched:
                            break

                    # --- 2. Если НЕ нашли комментарий — проверяем c4Name ---
                    if not matched:
                        c4name = element.attrib.get("c4Name", "").strip().lower()

                        for comp_key, comp_value in COMPONENT_1_12.items():
                            if comp_key in c4name:
                                full_service_name = "Сервис управления процессами (1.12)"
                                record = ['1.12', 1, comp_value]

                                update_global_word_book(
                                    service_name=full_service_name,
                                    NumberService=number_service,
                                    element_dict=record,
                                    f=fapp
                                )
                                matched = True
                                break
                        if matched:
                            break

                    # --- 3. Если не нашли НИ по Application, НИ по c4Name —
                    #     обрабатываем как обычный сервис ---
                    if not matched:
                        full_service_name = "Сервис управления процессами (1.12)"
                        record = ['1.12', 1]

                        update_global_word_book(
                            service_name=full_service_name,
                            NumberService=number_service,
                            element_dict=record,
                            f=fapp
                        )
                    
                for key, value in IMENA_USLUG.items():

                    if key == number_service:
                        full_service_name = value
                        c4_technologies.append(number_service)
                        # Формируем словарь только для этого сервиса
                        if f:
                            atr=element.attrib.get('c4count', '')
                            atr=atr.split('+')
                            if 'LB' in atr:
                                atr=int(atr[0])+1
                                record = [number_service,atr]
                                
                            else:
                                record = [
                                
                                number_service,
                                int(element.attrib.get('c4count', '')),
                            ]
                            if full_service_name!='1':
                                if record[0]=='3.2.5':
                                    record[1]=ceil(record[1]/50)
                                update_global_word_book(
                                    service_name=full_service_name,
                                    NumberService=number_service,
                                    element_dict=record,
                                    f = fapp
                                )

                            
                        else:
                            record = [
                                    
                                    number_service,
                                    1,
                            ]
                            if full_service_name!='1':
                                update_global_word_book(
                                    service_name=full_service_name,
                                    NumberService=number_service,
                                    element_dict=record,
                                    f = fapp
                                )

                        break    

        if 'c4Technology' in element.attrib:
            fapp=2
            number_services_raw = element.attrib['c4Technology']
            full_service_name='1'
            # Разделяем по пробелу и убираем пробелы
            number_services_list = [s.strip() for s in number_services_raw.split()]
            for number_service in number_services_list:
                # Ищем полное имя услуги в IMENA_USLUG
                  # по умолчанию просто номер
                for key, value in IMENA_USLUG.items():

                    if key == number_service:
                        full_service_name = value
                        c4_technologies.append(number_service)
                        # Формируем словарь только для этого сервиса
                        
                        record = [
                                number_service,
                                1,
                        ]
                        break
                if full_service_name!='1':
                    update_global_word_book(
                        service_name=full_service_name,
                        NumberService=number_service,
                        element_dict=record,
                        f = fapp
                    )



    return c4_technologies

c4_tech_data = []
def update_global_word_book(service_name: set, NumberService: str, element_dict, f: int) -> None:
    """
    Добавляет запись в глобальную переменную c4_tech_data.
    Формат каждого элемента:
        [
            [service_name],
            record
        ]
    """
    global c4_tech_data

    name = next(iter(service_name))
    if f == 2:
        record = [element_dict[0], 1]
    elif f == 1:
        record = [element_dict[0], element_dict[1]]
    else:
        record = [element_dict, element_dict[1], element_dict[2]]
        name=service_name


    c4_tech_data.append([[name],list(record)])

def get_c4_tech_data():
    return c4_tech_data




