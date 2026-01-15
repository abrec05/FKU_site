from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
# from .storage import save_excel_once
import warnings
import xml.etree.ElementTree as ET

from .main_chek_runner import run_main_chek


def _save_upload(file_obj, subdir="uploads") -> str:
    """
    Сохраняет загруженный файл и возвращает абсолютный путь на диске.
    """
    path = default_storage.save(f"{subdir}/{file_obj.name}", ContentFile(file_obj.read()))
    return default_storage.path(path)


def _first_diagram_name(drawio_path: str) -> str | None:
    """
    Всегда возвращает имя первого листа drawio (первого <diagram>).
    """
    with open(drawio_path, "r", encoding="utf-8") as f:
        xml_content = f.read()
    root = ET.fromstring(xml_content)
    diagrams = root.findall("diagram")
    if not diagrams:
        return None
    return diagrams[0].attrib.get("name")


def _run_diagram_check(drawio_path: str) -> str:
    """
    Рабочая проверка диаграммы без input():
    - выбираем первый лист
    - ставим SELECTED_SHEET_NAME
    - запускаем extract_c4_names
    Возвращаем только итоговую строку.
    """
    # ВАЖНО: импорт внутри функции, чтобы не падать импортом при старте, если пути ещё не настроены
    try:
        from c4_checker_lib.с4_config import global_word_book as gwb
        from c4_checker_lib.diagram_analis.extract_c4_names import extract_c4_names
    except Exception as e:
        return f"Ошибка импорта C4-проверки: {e}"

    sheet_name = _first_diagram_name(drawio_path)
    gwb.SELECTED_SHEET_NAME = sheet_name

    # сброс глобального состояния, чтобы не копилось между запусками
    try:
        gwb.c4_tech_data.clear()
    except Exception:
        pass

    try:
        extract_c4_names(drawio_path)
        # Если тебе нужно выводить что-то конкретное по диаграмме — скажи, добавим.
        return "Все проверки пройдены"
    except Exception as e:
        return f"Ошибка при проверке диаграммы: {e}"


def index(request):
    try:
        output = None
        mode = "diagram"
        submode = "params"

        if request.method == "POST":
            warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

            mode = request.POST.get("mode", "diagram")
            submode = request.POST.get("submode", "params")
            if mode == "diagram":
                excel_new = request.FILES.get("excel_new_file")
                # if excel_new:
                    # try:
                    #     save_excel_once(excel_new, source="diagram")
                    # except Exception:
                    #     pass
            # --- ПРОВЕРКА ЗАКАЗА ---
            if mode == "services":
                submode = request.POST.get("submode", "params")

                new_file = request.FILES.get("excel_new_file")
                # if new_file:
                    # try:
                    #     save_excel_once(new_file, source="order_params")
                    # except Exception:
                    #     pass

                old_file = request.FILES.get("excel_old_file")  # будет только для compare

                if submode == "params":
                    if not new_file:
                        return render(request, "checker/main.html",
                                      {"output": "Нужно загрузить заказ (Excel)", "mode": mode, "submode": submode})

                    # ✅ сохраняем только этот один файл


                    new_path = _save_upload(new_file)
                    over = request.POST.get("over") == "on"
                    output = run_main_chek(new_path, over=over)

                    return render(request, "checker/main.html", {"output": output, "mode": mode, "submode": submode})

                elif submode == "security":
                    if not new_file:
                        return render(request, "checker/main.html",
                                      {"output": "Нужно загрузить заказ (Excel)", "mode": mode, "submode": submode})

                    # ✅ для ИБ тоже один файл


                    new_path = _save_upload(new_file)
                    from .security_runner import run_security_check
                    output = run_security_check(new_path)

                    return render(request, "checker/main.html", {"output": output, "mode": mode, "submode": submode})


                elif submode == "compare":
                    new_file = request.FILES.get("excel_new_file")
                    old_file = request.FILES.get("excel_old_file")
                    if not new_file or not old_file:
                        output = "Нужно загрузить НОВЫЙ и СТАРЫЙ заказы (Excel)"
                        return render(request, "checker/main.html", {"output": output, "mode": mode, "submode": submode})
                    new_path = _save_upload(new_file)
                    old_path = _save_upload(old_file)
                    from .compare_runner import run_compare
                    output = run_compare(new_path, old_path)
                    return render(request, "checker/main.html", {"output": output, "mode": mode, "submode": submode})

            # --- ПРОВЕРКА ДИАГРАММЫ ---
            drawio = request.FILES.get("drawio_file")
            if not drawio:
                return render(request, "checker/main.html", {
                    "output": "Нужно загрузить drawio файл",
                    "mode": mode,
                    "submode": submode
                })

            drawio_path = _save_upload(drawio)
            output = _run_diagram_check(drawio_path)

            return render(request, "checker/main.html", {"output": output, "mode": mode, "submode": submode})
    except Exception as e:
        output = f"Ошибка: данные некорректные.\n\n{e}"
    return render(request, "checker/main.html", {"output": output, "mode": mode, "submode": submode})

