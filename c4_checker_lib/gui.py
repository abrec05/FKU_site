# gui.py
import tkinter as tk
from tkinter import filedialog, scrolledtext
from typing import Tuple, Optional

def start_gui() -> Tuple[Optional[str], Optional[str]]:
    """
    Открывает модальное окно для выбора двух файлов.
    Возвращает (drawio_path, excel_path) после нажатия "Старт".
    Если пользователь закрыл окно — возвращает (None, None).
    """
    drawio_path = None
    excel_path = None

    def select_drawio():
        nonlocal drawio_path
        path = filedialog.askopenfilename(
            title="Выберите DRAWIO файл",
            filetypes=[("Drawio/XML files", "*.drawio *.xml")]
        )
        if path:
            drawio_path = path
            drawio_label.config(text=f"Выбрано: {path}")

    def select_excel():
        nonlocal excel_path
        path = filedialog.askopenfilename(
            title="Выберите Excel файл",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if path:
            excel_path = path
            excel_label.config(text=f"Выбрано: {path}")

    def run_app():
        if not drawio_path or not excel_path:
            result_label.config(text="❌ Выберите оба файла!")
        else:
            # Закрываем главный цикл — и start_gui вернёт пути
            root.quit()

    root = tk.Tk()
    root.title("Выбор файлов")
    root.geometry("450x260")
    root.resizable(False, False)

    tk.Label(root, text="Выберите файлы:", font=("Arial", 14)).pack(pady=8)

    tk.Button(root, text="Выбрать DRAWIO файл", command=select_drawio).pack(pady=4)
    drawio_label = tk.Label(root, text="Файл не выбран", wraplength=420)
    drawio_label.pack()

    tk.Button(root, text="Выбрать Excel файл", command=select_excel).pack(pady=4)
    excel_label = tk.Label(root, text="Файл не выбран", wraplength=420)
    excel_label.pack()

    tk.Button(root, text="Старт", command=run_app).pack(pady=12)
    result_label = tk.Label(root, text="", fg="red")
    result_label.pack()

    # Запускаем цикл; после quit() выполнение продолжится
    root.mainloop()

    # Закрываем окно полностью
    try:
        root.destroy()
    except Exception:
        pass

    return drawio_path, excel_path


def show_errors(errors: dict):
    """
    Открывает окно с сообщением об ошибках.
    Предполагается, что start_gui уже отработал (нет лишнего root).
    """
    # Создаём отдельный root для окна ошибок (не при импорте)
    err_root = tk.Tk()
    err_root.title("Ошибки проверки")
    err_root.geometry("700x500")

    txt = scrolledtext.ScrolledText(err_root, wrap=tk.WORD, font=("Arial", 12))
    txt.pack(expand=True, fill="both", padx=8, pady=8)

    for key, msg in errors.items():
        txt.insert(tk.END, f"• {msg}\n\n")

    txt.configure(state="disabled")

    err_root.lift()
    err_root.attributes('-topmost', True)
    err_root.after(600, lambda: err_root.attributes('-topmost', False))

    # Окно ошибок должно ждать закрытия пользователя
    err_root.mainloop()
