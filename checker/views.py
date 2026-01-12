from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import io
import traceback
from contextlib import redirect_stdout, redirect_stderr

from .services import run_check

def _save_upload(file_obj, subdir="uploads") -> str:
    # сохраняем в MEDIA (если MEDIA не используешь — Django всё равно может сохранить через default_storage)
    path = default_storage.save(f"{subdir}/{file_obj.name}", ContentFile(file_obj.read()))
    return default_storage.path(path)

def index(request):
    output = None

    if request.method == "POST":
        env = request.POST.get("environment", "PROD")
        drawio = request.FILES.get("drawio_file")
        excel = request.FILES.get("excel_file")

        # Лог будем собирать сюда
        buf = io.StringIO()

        try:
            if not drawio or not excel:
                output = "[ERR] Нужно загрузить оба файла: drawio и заказ (excel)"
                return render(request, "checker/main.html", {"output": output})

            drawio_path = _save_upload(drawio)
            excel_path = _save_upload(excel)

            with redirect_stdout(buf), redirect_stderr(buf):
                print(f"[INFO] Контур: {env}")
                print(f"[INFO] DRAWIO сохранён: {drawio_path}")
                print(f"[INFO] Excel сохранён:  {excel_path}")
                print("[INFO] Запуск проверки...")

                # ВАЖНО: sheet_name пока не выбираем на сайте — можно поставить None
                # но твой extract_c4_names требует SELECTED_SHEET_NAME.
                # Временное решение: пробуем взять первый лист автоматически:
                sheet_name = _try_get_first_sheet_name(drawio_path)
                print(f"[INFO] Выбран лист: {sheet_name}")

                errors = run_check(drawio_path, excel_path, sheet_name=sheet_name)

                if errors:
                    print(f"[ERR] Найдено ошибок: {len(errors)}")
                    for _, msg in errors.items():
                        print(f"  - {msg}")
                else:
                    print("[OK] Все услуги совпадают!")

            output = buf.getvalue()

        except Exception:
            # добавим traceback в лог
            buf.write("\n[ERR] Упало с исключением:\n")
            buf.write(traceback.format_exc())
            output = buf.getvalue()

    return render(request, "checker/main.html", {"output": output})


def _try_get_first_sheet_name(drawio_path: str) -> str | None:
    """
    Временный хак: extract_c4_names требует SELECTED_SHEET_NAME.
    Берём имя первого <diagram name="..."> из drawio.
    """
    import xml.etree.ElementTree as ET

    with open(drawio_path, "r", encoding="utf-8") as f:
        xml_content = f.read()
    root = ET.fromstring(xml_content)
    diagrams = root.findall("diagram")
    if not diagrams:
        return None
    return diagrams[0].attrib.get("name")
