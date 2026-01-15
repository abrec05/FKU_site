# iaas.py
import logging
import pandas as pd

class IaaSValidator:
    name = 'IaaS'  # Название валидатора (используется в отчётах)

    def __init__(self, cfg_parser):
        # Загружаем конфигурацию требований из файла service_config.txt
        raw = cfg_parser.get('service_config.txt')
        self.required = {}  # Словарь: "сервис | продукт" -> список обязательных параметров

        for svc, val in raw.items():
            if isinstance(val, list):
                # Если значение уже список — сохраняем как есть
                self.required[svc] = val
            elif isinstance(val, str):
                # Если строка — разбиваем по ';'
                self.required[svc] = [p.strip() for p in val.split(';') if p.strip()]
            elif val is None:
                # Пустое значение — нет обязательных параметров
                self.required[svc] = []
                logging.info(f"[IaaSValidator] Пустое значение для '{svc}' — параметры не заданы.")
            else:
                # Неподдерживаемый формат — игнорируем
                self.required[svc] = []
                logging.warning(f"[IaaSValidator] '{svc}' имеет неподдерживаемый формат: {type(val)} — игнорируется.")

    def validate(self, row):
        """
        Проверяет, что в строке заполнены все параметры,
        обязательные для данного сервиса и цифрового продукта.
        Возвращает список недостающих параметров, либо None.
        """
        # Ключ: "название услуги | цифровой продукт"
        service_key = f"{row['service_name']} | {row['digital_prod']}".strip()
        needed = self.required.get(service_key, [])

        # Вспомогательная функция: сопоставляет логическое имя параметра с колонкой
        def actual_field(param):
            if param.lower() == 'cpu':
                return 'cpu_iaas'  # CPU в IaaS обозначается отдельной колонкой
            return param

        missing = []
        for p in needed:
            field = actual_field(p)
            val = row.get(field)
            if val is None or pd.isna(val) or val == '':
                missing.append(p)  # Параметр отсутствует или пуст

        return missing or None  # None, если всё на месте
