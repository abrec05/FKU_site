import warnings
import pandas as pd
import logging
import re
f=False
# Подавляем предупреждения openpyxl, связанные с заголовками и расширениями в Excel
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r".*(Cannot parse header or footer|Data Validation extension).*"
)

# По умолчанию: соответствие контура использования списку обязательных сервисов
DEFAULT_REQUIRED_SERVICES_MAP = {
    # - контур разработки
    "DEV": [
        "Сервис IAM (услуга 1.1.13)",
        "Сервис журналирования (услуга 1.1.14)",
        "Сервис аудита (услуга 1.1.15)",
        "Сервис мониторинга (услуга 1.1.16)",
        "Сервис управление развертыванием ПО (услуга 1.1.31)"
    ],
    # TEST - контур тестирования
    "TEST": [
        "Сервис IAM (услуга 1.1.13)",
        "Сервис журналирования (услуга 1.1.14)",
        "Сервис аудита (услуга 1.1.15)",
        "Сервис мониторинга (услуга 1.1.16)",
        "Сервис управление развертыванием ПО (услуга 1.1.31)"
    ],
    # PROD - контур продакшена
    "PROD": [
        "Сервис IAM (услуга 1.1.13)",
        "Сервис журналирования (услуга 1.1.14)",
        "Сервис аудита (услуга 1.1.15)",
        "Сервис мониторинга (услуга 1.1.16)",
        "Сервис управление развертыванием ПО (услуга 1.1.31)"
    ],
    "ПСИ": [
        "Сервис IAM (услуга 1.1.13)",
        "Сервис журналирования (услуга 1.1.14)",
        "Сервис аудита (услуга 1.1.15)",
        "Сервис мониторинга (услуга 1.1.16)",
        "Сервис управление развертыванием ПО (услуга 1.1.31)"
    ],
    "HT": [
        "Сервис IAM (услуга 1.1.13)",
        "Сервис журналирования (услуга 1.1.14)",
        "Сервис аудита (услуга 1.1.15)",
        "Сервис мониторинга (услуга 1.1.16)",
        "Сервис управление развертыванием ПО (услуга 1.1.31)"
    ]
}


def parse_services_data(file_path: str, sheet_name: str = "Услуги 1-2.1") -> pd.DataFrame:
    """
    Загружает и возвращает из Excel данные по услугам.

    Алгоритм:
    1. Считывает первые строки листа без заголовков.
    2. Находит индекс строки, содержащей заголовки
       ("Контур использования", "Наименование услуги", "Статус услуги").
    3. Перечитывает лист, используя найденный header_idx.
    4. Нормализует и обрезает значения в названиях колонок и строках.

    Параметры:
    file_path: путь к .xlsx-файлу
    sheet_name: имя листа для чтения (по умолчанию "Услуги 1-2.1")

    Возвращает:
    DataFrame с колонками:
      - "Контур использования"
      - "Наименование услуги"
      - "Статус услуги"
    """
    required_cols = ["Контур использования", "Наименование услуги", "Статус услуги"]


    raw = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        engine="openpyxl",
        header=None
    )

    # 2) Ищем строку, в которой есть все необходимые заголовки
    header_idx = None
    for idx in range(min(10, len(raw))):
        row_vals = raw.iloc[idx].astype(str).str.strip().tolist()
        if all(col in row_vals for col in required_cols):
            header_idx = idx
            break
    if header_idx is None:
        raise ValueError(f"Не удалось найти заголовки {required_cols} в листе '{sheet_name}'")

    # 3) Перечитываем лист, устанавливая header=header_idx
    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        engine="openpyxl",
        header=header_idx
    )

    # 4) Обрезаем пробелы в названиях колонок
    df.columns = df.columns.astype(str).str.strip()

    # Проверяем, что все нужные колонки присутствуют
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found after header parsing in sheet '{sheet_name}'")

    # Оставляем только нужные колонки и удаляем пустые строки
    df = df[required_cols].dropna(subset=required_cols)


    for col in required_cols:
        df[col] = df[col].astype(str).str.strip()
    return df

def check_required_services(
    file_path: str,
    sheet_name: str = "Услуги 1-2.1",
    required_map: dict = None
) -> list:
    """
    Проверяет наличие обязательных сервисов в рамках каждого контура.

    Логика:
    1. Загружает данные через parse_services_data().
    2. Оставляет только строки со статусами
       "Новая услуга" и "Заказанная услуга".
    3. Для каждого контура из required_map проверяет,
       какие сервисы из списка отсутствуют.

    Параметры:
    file_path: путь к .xlsx-файлу
    sheet_name: имя листа с таблицей услуг
    required_map: словарь контур->список обязательных сервисов
                  (используется DEFAULT_REQUIRED_SERVICES_MAP по умолчанию)

    Возвращает:
    Список строк-описаний отсутствующих сервисов, например:
      ["Для контура 'TEST' отсутствует обязательная услуга: Сервис IAM (услуга 1.13)", ...]
    """
    # 1) Берём пользовательскую карту или дефолтную
    service_map = required_map or DEFAULT_REQUIRED_SERVICES_MAP

    # 2) Загружаем и фильтруем данные по статусам
    df = parse_services_data(file_path, sheet_name)
    if f:
        valid_statuses = ["Новая услуга", "Заказанная услуга"]
    else:
        valid_statuses = ["Новая услуга", "Заказанная услуга", "Изменение заказанной услуги"]
    df = df[df["Статус услуги"].isin(valid_statuses)]

    comments = []
    # 3) По каждому контуру сравниваем список обязательных и найденных сервисов
    for contour_key, expected_services in service_map.items():
        mask = df["Контур использования"].str.upper() == contour_key
        sub = df[mask]
        if sub.empty:
            # Если для контура нет ни одной услуги — пропускаем без ошибок
            continue

        present = set(sub["Наименование услуги"].tolist())
        for req in expected_services:
            if req not in present:
                comments.append(
                    f"Для контура '{contour_key}' отсутствует обязательная услуга: {req}\n"
            )
   
    return comments


def parse_kubernetes_service_counts_by_gis(
    file_path: str,
    sheet_name: str = "Услуги 1-2.1",
    target_service_name: str = "Система управления контейнера (услуга 1.2.1.2)",
    valid_statuses: list | None = None,
) -> dict:
    """
    Считает количество услуг 2.1.2 по паре (Контур использования, Наименование ГИС (Сервиса)).
    Возвращает словарь вида:
      { "DEV": {"ГИС А": 1, "ГИС Б": 2}, "TEST": {...}, ... }
    """
    import pandas as pd

    # --- NEW: жесткий список по умолчанию + нормализация статусов ---
    def _norm(s: str) -> str:
        return " ".join(str(s).strip().split()).lower()

    valid_statuses = valid_statuses or ["Новая услуга", "Заказанная услуга"]
    valid_norm = {_norm(s) for s in valid_statuses}
    # ---------------------------------------------------------------

    empty = {c: {} for c in ["DEV", "TEST", "PROD", "ПСИ", "HT"]}

    try:
        df2 = read_second_table_with_columns(file_path, sheet_name=sheet_name)
    except Exception:
        return empty

    df2 = df2.copy()
    df2["Контур использования"] = df2["Контур использования"].astype(str).str.strip()
    df2["Наименование ГИС (Сервиса)"] = df2["Наименование ГИС (Сервиса)"].astype(str).str.strip()
    df2["Наименование услуги"] = df2["Наименование услуги"].astype(str).str.strip()

    # --- NEW: фильтр только по нужным статусам (нормализованным) ---
    if "Статус услуги" in df2.columns:
        df2["Статус услуги"] = df2["Статус услуги"].astype(str)
        df2 = df2[df2["Статус услуги"].map(_norm).isin(valid_norm)]
    # ---------------------------------------------------------------

    df2 = df2[df2["Наименование услуги"] == target_service_name]

    if df2.empty:
        return empty

    grp = (df2.groupby(["Контур использования", "Наименование ГИС (Сервиса)"])
              .size()
              .reset_index(name="cnt"))

    result = {}
    for contour, sub in grp.groupby("Контур использования"):
        result[str(contour).strip()] = {
            str(row["Наименование ГИС (Сервиса)"]).strip(): int(row["cnt"])
            for _, row in sub.iterrows()
        }

    for k in ["DEV", "TEST", "PROD", "ПСИ", "HT"]:
        result.setdefault(k, {})
    return result


def parse_kubernetes_service_counts(
    file_path: str,
    sheet_name: str = "Услуги 1-2.1",
    header_keyword: str = "Контур использования",
    target_service_name: str = "Система управления контейнерами (услуга 1.2.1.2)",
) -> dict:
    # статусы учитываем ТОЛЬКО эти два
    valid_statuses = ["Новая услуга", "Заказанная услуга"]

    # 1) Чтение листа без header для поиска
    df_full = pd.read_excel(file_path, sheet_name=sheet_name, header=None, dtype=str)

    # 2) Поиск строки заголовков по ключевому слову
    header_rows = df_full.index[df_full.eq(header_keyword).any(axis=1)].tolist()
    if not header_rows:
        raise ValueError(f"Не удалось найти строку с заголовком '{header_keyword}'")
    header_row_idx = header_rows[0]

    # 3) Чтение таблицы с правильными заголовками и колонками
    df_table = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=header_row_idx,
        usecols=["Контур использования", "Наименование услуги", "Статус услуги"],
        dtype=str
    ).dropna(how="all").reset_index(drop=True)

    # нормализуем пробелы/регистры в статусе
    df_table["Статус услуги"] = df_table["Статус услуги"].astype(str).str.strip()

    # 4) Фильтр по статусам
    df_filtered = df_table[df_table["Статус услуги"].isin(valid_statuses)]

    # 5) Только целевая услуга
    df_target = df_filtered[df_filtered["Наименование услуги"] == target_service_name]

    # 6) Группировка и подсчёт по контуру
    counts = df_target.groupby("Контур использования").size().reset_index(name="count")

    # 7) В словарь + заполняем отсутствующие контуры нулями
    result = dict(counts.values.tolist())
    for contour in ["DEV", "TEST", "PROD", "ПСИ", "HT"]:
        result.setdefault(contour, 0)
    return result

import pandas as pd
import re

FINAL_COLS = [
    "№ п/п",
    "Наименование Потребителя услуг",
    "Наименование ГИС (Сервиса)",
    "Контур использования",
    "Наименование услуги",
    "Статус услуги",
    "Технологическая площадка размещения",
    "ID сервиса",
    "Параметр доступности",
    "Коэф-т переподписки",
    "МТП или МИ",
    "vCPU, ядер",
    "RAM, Гб",
    "SSD, Гб",
    "HDD Fast, Гб",
    "HDD Slow, Гб",
    "Тип операционной системы",
    "Количество операционных систем, шт."
]

def is_unnamed(x: str) -> bool:
    s = str(x).strip()
    return s == "" or s.lower().startswith("unnamed:")

def _norm(x):
    # нормализуем к строке без лишних пробелов
    return str(x).strip() if x is not None else ""

def _find_all_header_rows(path, sheet_name):
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None, engine="openpyxl")
    rows = []
    for i in range(len(raw)):
        row = raw.iloc[i].astype(str).str.strip().tolist()
        if ("Контур использования" in row) and ("Наименование услуги" in row):
            rows.append(i)
    return raw, rows

def read_second_table_with_columns(path, sheet_name=None):
    xls = pd.ExcelFile(path)
    if sheet_name is None:
        sheet_name = next((s for s in xls.sheet_names if str(s).startswith("Услуги")), xls.sheet_names[0])

    raw, header_rows = _find_all_header_rows(path, sheet_name)
    if len(header_rows) < 2:
        raise IndexError(f"Не найдено двух таблиц на листе '{sheet_name}'. Найдено заголовков: {header_rows}")

    start = header_rows[1]
    end = header_rows[2] if len(header_rows) > 2 else None
    nrows = (end - start) if end is not None else None

    # читаем вторую таблицу с двумя строками заголовков (MultiIndex)
    dfm = pd.read_excel(path, sheet_name=sheet_name, header=[start, start + 1], nrows=nrows, engine="openpyxl")

    # сплющиваем заголовки – берём 2-й уровень, если не пустой; иначе 1-й
    flat_cols = []
    for lvl0, lvl1 in dfm.columns.to_list():
        c0 = _norm(lvl0)
        c1 = _norm(lvl1)
        use_lower = (not is_unnamed(c1))  # нижний годится только если он НЕ Unnamed
        col = c1 if use_lower else c0
        flat_cols.append(col)

    df = dfm.copy()
    df.columns = [ _norm(c) for c in flat_cols ]
    df = df.dropna(how="all").reset_index(drop=True)

    required = [
        "№ п/п",
        "Наименование ГИС (Сервиса)",
        "Контур использования",
        "Наименование услуги",
        "Статус услуги",
        "Технологическая площадка размещения",
        "ID сервиса",
        "Параметр доступности",
        "Коэф-т переподписки",
        "МТП или МИ",
        "vCPU, ядер",
        "RAM, Гб",
        "SSD, Гб",
        "HDD Fast, Гб",
        "HDD Slow, Гб",
        "Тип операционной системы",
        "Количество операционных систем, шт.",
        "Примечание",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            "Во 2-й таблице не найдены нужные колонки: "
            + ", ".join(missing)
            + f"\nДоступные колонки: {list(df.columns)}"
        )

    out = df[required].copy()
    return out