# paas.py
import logging

class PaaSValidator:
    name = 'PaaS'  # Название валидатора (используется в отчётах и логах)

    def __init__(self, cfg_parser):
        # Загружаем конфигурации из файла service_config.txt
        raw = cfg_parser.get('service_config.txt')
        self.required = {}  # Словарь: имя сервиса -> список обязательных параметров

        for svc, val in raw.items():
            if isinstance(val, list):
                # Если уже список — сохраняем напрямую
                self.required[svc] = val
            elif isinstance(val, str):
                # Если строка — разбиваем по ';'
                self.required[svc] = [p.strip() for p in val.split(';') if p.strip()]
            elif val is None:
                # Пустое значение — не требуется параметров
                self.required[svc] = []
                logging.info(f"[PaaSValidator] Пустое значение для '{svc}' — параметры не заданы.")
            else:
                # Любой другой тип данных — ошибка и игнорируем
                self.required[svc] = []
                logging.warning(f"[PaaSValidator] '{svc}' имеет неподдерживаемый формат: {type(val)} — игнорируется.")

    def validate(self, row):
        """
        Проверяет, что все параметры, обязательные для данного сервиса, заданы.
        Возвращает список отсутствующих параметров, либо None если всё заполнено.
        """
        svc = row['service_name']  # Используем только имя сервиса (без digital_prod)
        needed = self.required.get(svc, [])

        # Вспомогательная функция для преобразования логического имени в имя колонки
        def actual_field(param):
            if param.lower() == 'cpu':
                return 'cpu_paas'  # Для PaaS CPU хранится в колонке cpu_paas
            return param

        missing = []
        for p in needed:
            field = actual_field(p)
            # Если значение не задано (None, пустая строка или 0) — считаем отсутствующим
            if not row.get(field):
                missing.append(p)

        return missing or None  # None, если все параметры на месте