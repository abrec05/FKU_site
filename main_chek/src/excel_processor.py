import pandas as pd
import logging
import os

class ExcelProcessor:
    def __init__(self, cfg_parser):
        # Сохраняем конфигурационный парсер, содержащий настройки приложения
        self.cfg = cfg_parser

    def _detect_header_row(self, df_sample: pd.DataFrame, required_columns: list[str]) -> int:
        """
        Определяет номер строки, с которой начинается таблица в Excel-файле.
        Проверяет каждую строку на наличие хотя бы одного из требуемых заголовков.
        Возвращает индекс строки, если заголовки найдены, иначе возвращает 0.
        """
        for i in range(len(df_sample)):
            row = df_sample.iloc[i].astype(str).str.strip().tolist()
            if any(col in row for col in required_columns):
                return i
        return 0

    def detect_target_skiprows(self, path: str, sheet_name: str = None) -> int:
        """
        Определяет, сколько строк нужно пропустить (skiprows), чтобы начать чтение таблицы
        в target-файле. Ищет первую строку с ключевыми названиями столбцов.
        """
        xls = pd.ExcelFile(path)
        if not sheet_name:
            # Выбираем первый подходящий лист, начинающийся с 'Услуги'
            sheet_name = next(
                (s for s in xls.sheet_names if s.startswith('Услуги')),
                xls.sheet_names[0]
            )

        # Читаем первые 20 строк без заголовков для анализа структуры
        df_preview = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=20)
        required_columns = ['№ п/п', 'Статус услуги', 'Наименование услуги', 'Контур использования']
        return self._detect_header_row(df_preview, required_columns)

    def read_test_zak(self, path: str) -> pd.DataFrame:
        """
        Загружает Excel-файл test_zak.xlsx и возвращает DataFrame с ожидаемыми колонками.
        Производит переименование, проверку и заполнение пропущенных значений.
        """
        params = self.cfg.get('app_config.txt').get('test_zak', {})
        skip = int(params.get('skiprows', 0))  # Строки для пропуска до заголовков
        header = int(params.get('header', 0))  # Номер строки с заголовками
        sheet = params.get('sheet', 0)         # Название или номер листа Excel

        xls = pd.ExcelFile(path)
        available = xls.sheet_names
        logging.info(f"Доступные листы в файле {path}: {available}")
        if 'Потребитель' in available:
            sheet_name = 'Потребитель'
        else:
            sheet_name = sheet if sheet in available else available[0]
        logging.info(f"Используем лист test_zak: {sheet_name}")

        # Считываем таблицу
        df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=skip, header=header)
        df.columns = df.columns.str.strip()

        # Переименовываем колонки на понятные ключи
        rename_map = {
            'Наименование ГИС (Сервиса)': 'gis_name',
            'Наименование услуги': 'service_name',
            'vCPU, ядер':           'cpu_iaas',
            'RAM, Гб':              'ram',
            'SSD, Гб':              'ssd',
            'HDD Fast, Гб':         'hddf',
            'HDD Slow, Гб':         'hdds',
            'Тип операционной системы': 'os_type',
            'Количество операционных систем, шт.': 'os_amount',
            'Цифровой продукт':     'digital_prod',
            'Комментарий':          'comment'
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # Проверяем наличие всех нужных колонок
        expected = [
            'service_name', 'cpu_iaas', 'ram', 'ssd',
            'hddf', 'hdds', 'os_type', 'os_amount', 'digital_prod', 'comment'
        ]
        missing = [c for c in expected if c not in df.columns]
        if missing:
            raise ValueError(f"Отсутствуют необходимые колонки в test_zak: {missing}")

        # Приводим таблицу к нужному формату и заполняем пропуски
        df = df[expected].copy()
        df['service_name'] = df['service_name'].fillna('')
        df['digital_prod']  = df['digital_prod'].fillna('')
        df[['cpu_iaas','ram','ssd','hddf','hdds','os_amount']] = df[
            ['cpu_iaas','ram','ssd','hddf','hdds','os_amount']
        ].fillna(0)
        df['os_type'] = df['os_type'].fillna('')
        df['comment'] = df['comment'].fillna('')
        return df

    def _load_target_df(self, path: str, sheet_name: str = None):
        """
        Загружает лист из target-файла Excel с многоуровневыми заголовками (MultiIndex).
        Автоматически определяет нужный лист и строку начала таблицы.
        """
        xls = pd.ExcelFile(path)
        if sheet_name is None:
            sheet_name = next(
                (s for s in xls.sheet_names if s.startswith('Услуги')),
                xls.sheet_names[0]
            )
        skip = self.detect_target_skiprows(path, sheet_name)
        df_full = pd.read_excel(
            xls, sheet_name=sheet_name,
            header=[0, 1], skiprows=skip
        )
        # 1) найдём все «дочерние» колонки под lvl0 == 'Примечание'
        note_cols = [col for col in df_full.columns if col[0] == 'Примечание']
        if note_cols:
            # 2) Выбираем первую (или самую «насыщенную») из них
            selected = max(note_cols, key=lambda c: df_full[c].notna().sum())
            # 3) Удаляем все остальные дубляжи под lvl0 == 'Примечание'
            to_drop = [c for c in note_cols if c != selected]
            df_full = df_full.drop(columns=to_drop)

        # Теперь в df_full есть единственный столбец с именем lvl1 ('Unnamed: 34_level_1'),
        # и вы можете к нему обратиться как:
        return df_full, sheet_name

    def _flatten_and_rename(self, df: pd.DataFrame):
        """
        Преобразует таблицу с многоуровневыми заголовками в плоскую таблицу.
        Разделяет CPU ресурсы для IaaS и PaaS, переименовывает колонки
        и отбирает только нужные для анализа.
        """
        tuples = df.columns.tolist()
        cols = []
        
        for lvl0, lvl1 in tuples:
            if lvl1 == 'vCPU, ядер':
                if 'PaaS' in str(lvl0):
                    cols.append('cpu_paas')
                else:
                    cols.append('cpu_iaas')
            else:
                if isinstance(lvl1, str) and lvl1.strip() and not lvl1.startswith('Unnamed'):
                    cols.append(lvl1.strip())
                else:
                    cols.append(str(lvl0).strip())
        df_flat = df.copy()
        df_flat.columns = cols
        

        # Переименование колонок в понятные ключи
        rename_map = {
            '№ п/п':                 '№ п/п',
            'Наименование ГИС (Сервиса)': 'gis_name',
            'Статус услуги':         'service_status',
            'Наименование услуги':   'service_name',
            'Контур использования':  'usage_contour',
            'vCPU, ядер':            'cpu_iaas',
            'RAM, Гб':               'ram',
            'SSD, Гб':               'ssd',
            'HDD Fast, Гб':          'hddf',
            'HDD Slow, Гб':          'hdds',
            'Тип операционной системы': 'os_type',
            'Количество операционных систем, шт.': 'os_amount',
            'HDD, Гб.':              'hdd_paas',
            'Цифровой продукт':      'digital_prod',
            'Примечание':            'comment'
        }
        df_flat = df_flat.rename(columns={k: v for k, v in rename_map.items() if k in df_flat.columns})

        # Проверка наличия обязательных колонок
        cols_expected = [
            '№ п/п', 'service_status', 'service_name',
            'cpu_iaas', 'cpu_paas', 'hdd_paas',
            'ram', 'ssd', 'hddf', 'hdds',
            'os_type', 'os_amount', 'digital_prod', 'usage_contour', 'comment'
        ]
        extra = ['gis_name'] if 'gis_name' in df_flat.columns else []
        missing = []  # создаём пустой список для хранения отсутствующих колонок
        # Проходим по каждой колонке, которую ожидаем увидеть
        for c in cols_expected:
            if c not in df_flat.columns:
                missing.append(c)
        if missing:
            raise ValueError(f"Отсутствуют необходимые колонки в target: {missing}")
        df_flat['service_name'] = df_flat['service_name'].fillna('')
        return df_flat[cols_expected+extra].copy()

    def read_target_file(self, path: str) -> pd.DataFrame:
        """
        Читает target-файл Excel, выполняет все преобразования
        и возвращает таблицу с унифицированными колонками для анализа ресурсов.
        """
        df_full, _ = self._load_target_df(path)
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        pd.set_option("display.max_colwidth", None)
        return self._flatten_and_rename(df_full)
