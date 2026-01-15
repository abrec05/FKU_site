import os

class ConfigParser:
    """
    Класс для парсинга конфигурационных файлов .txt из папки.
    Поддерживает разные форматы строк:
    - комментарии (#)
    - пары ключ:значение или ключ=значение
    - составные строки с разделителем ';'
    - одиночные значения без ключа
    Возвращает содержимое каждого файла в виде словаря.
    """

    def __init__(self, config_dir: str):
        # Путь к папке с конфигурационными файлами
        self.config_dir = config_dir
        self.configs = {}
        self._load_all()  # Загружаем все конфигурации при инициализации

    def _load_all(self):
        # Проходим по всем файлам в директории
        for fn in os.listdir(self.config_dir):
            path = os.path.join(self.config_dir, fn)
            # Обрабатываем только текстовые файлы
            if os.path.isfile(path) and fn.endswith('.txt'):
                # Парсим содержимое файла и сохраняем в словарь
                self.configs[fn] = self._parse_file(path)

    def _parse_file(self, path: str) -> dict:
        # Словарь для хранения содержимого конфигурационного файла
        result = {}
        with open(path, encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith('#'):
                    continue  # Пропускаем пустые строки и комментарии

                # Определяем разделитель строки
                if ':' in s:
                    k, v = s.split(':', 1)
                elif '=' in s:
                    k, v = s.split('=', 1)
                else:
                    # Строка без разделителя — сохраняем как ключ без значения
                    result[s] = None
                    continue

                k = k.strip()
                v = v.strip()

                # Обработка составного значения с несколькими параметрами
                if ';' in v:
                    parts = [p.strip() for p in v.split(';') if p.strip()]
                    sub = {}
                    for part in parts:
                        if ':' in part:
                            sk, sv = part.split(':', 1)
                        elif '=' in part:
                            sk, sv = part.split('=', 1)
                        else:
                            # Если не пара ключ:значение — сохраняем как список
                            sub = None
                            break
                        sub[sk.strip()] = sv.strip()

                    if sub is not None and sub:
                        result[k] = sub  # Сохраняем как словарь
                    else:
                        result[k] = parts  # Сохраняем как список
                else:
                    # Простое значение без ';'
                    result[k] = v
        return result

    def get(self, filename: str) -> dict:
        """
        Возвращает разобранный словарь для указанного файла (например, 'app_config.txt')
        Если файл не найден — возвращает пустой словарь
        """
        return self.configs.get(filename, {})