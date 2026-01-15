import logging
import pandas as pd
from main_chek.src.validators.iaas import IaaSValidator
from main_chek.src.validators.paas import PaaSValidator
from main_chek.src.parsers.universal_parser import *
from main_chek.src.Chekers import *
f=True
f18=False
ov = True
class ContextBuilder:
    """
    Класс, объединяющий данные из target и test_zak и запускающий валидацию.
    Валидаторы можно включать/отключать через app_config.txt.
    Используется для проверки корректности параметров услуг.
    """
    def __init__(self, cfg_parser, excel_proc):
        self.cfg = cfg_parser  # Парсер конфигурации
        self.proc = excel_proc  # Объект ExcelProcessor
        self.validators = []    # Список активных валидаторов

        general_config = self.cfg.get('app_config.txt')

        # Подключаем валидатор IaaS, если включен в конфиге
        if str(general_config.get('enable_iaas', 'true')).strip().lower() == 'true':
            self.validators.append(IaaSValidator(self.cfg))
            logging.info("IaaSValidator включён")
        else:
            logging.info("IaaSValidator отключён")

        # Подключаем валидатор PaaS, если включен в конфиге
        if str(general_config.get('enable_paas', 'true')).strip().lower() == 'true':
            self.validators.append(PaaSValidator(self.cfg))
            logging.info("PaaSValidator включён")
        else:
            logging.info("PaaSValidator отключён")

    @staticmethod
    def _sum_counts(obj):
        if isinstance(obj, dict):
            total = 0
            for v in obj.values():
                total += ContextBuilder._sum_counts(v)
            return total
        try:
            return int(obj)
        except (TypeError, ValueError):
            return 0


    def build(self, target_path: str, test_zak_path: str):
        """
        Загружает target и test_zak, объединяет по ключам и выполняет валидацию.
        Возвращает кортеж: (объединённый DataFrame, текстовый отчёт).
        """
        
        # Проверяем обязательные сервисы
        missing = check_required_services(
            file_path=target_path,
            sheet_name="Услуги 1-2.1",
            required_map=None
        )
        if missing:
            for msg in missing:
                logging.warning(msg)
            missing_report = (
                "Обнаружены нарушения обязательных сервисов:\n\n\n"
                + "".join(f" - {m}" for m in missing)
            )
        else:
            missing_report = "Обнаружены нарушения обязательных сервисов: НЕТ\n\n\n"
        
        # Удаляем дубликаты из _target и _zak
        df_all = self.proc.read_target_file(target_path)  # Данные с требованиями
        df_test = self.proc.read_test_zak(test_zak_path)  # Данные из заявки
        df_2list= read_second_table_with_columns(target_path, "Услуги 1-2.1")
        df_all = df_all.loc[:, ~df_all.columns.duplicated()]
        df_test = df_test.loc[:, ~df_test.columns.duplicated()]
        # Объединение по service_name и digital_prod
        df = pd.merge(
            df_all,
            df_test,
            on=['service_name', 'digital_prod'],
            how='inner',
            suffixes=('_min','_test')
        )
        logging.info(f"После объединения строк: {len(df)}")

        df = df.reset_index(drop=True)

        # Применяем валидаторы к каждой строке
        df['errors'] = df.apply(self._validate_row, axis=1)
        # Генерируем подробный отчёт
        detailed_report = self._generate_report(df, df_all, target_path, df_2list)
        # Составляем итоговый отчёт: сначала missing_report, потом основной
        final_report = f"{missing_report}\n\n\n{detailed_report}"
        return df, final_report, df_2list

    def _validate_row(self, row: pd.Series) -> dict:
        # Применяет все валидаторы к строке и собирает ошибки
        errs = {}
        for validator in self.validators:
            result = validator.validate(row)
            if result:
                errs[validator.name] = result
        return errs
    
    


    def _generate_report(self, df: pd.DataFrame,df_all: pd.DataFrame,  path, df_2list) -> str:
        """
        Формирует подробный текстовый отчёт по ошибкам валидации.
        Отчёт разбит по строкам таблицы, с указанием услуг и параметров.
        """
        display_map = {
            'vCPU, ядер': 'vCPU, ядер',
            'RAM, Гб':    'RAM, Гб',
            'SSD, Гб':    'SSD, Гб',
            'HDD Fast, Гб': 'HDD Fast, Гб',
            'HDD Slow, Гб': 'HDD Slow, Гб',
            'Тип операционной системы': 'Тип ОС',
            'Количество операционных систем, шт.': 'Количество ОС'
        }

        rename_map = {
            'Наименование ГИС (Сервиса)': 'gis_name',
            'Наименование услуги': 'service_name',
            'Статус услуги':       'service_status',
            'Контур использования':  'usage_contour',
            'vCPU, ядер':         'cpu_iaas',
            'RAM, Гб':            'ram',
            'SSD, Гб':            'ssd',
            'HDD Fast, Гб':       'hddf',
            'HDD Slow, Гб':       'hdds',
            'Тип операционной системы': 'os_type',
            'Количество операционных систем, шт.': 'os_amount',
            'Комментарий':        'comment'
        }

        lines = ["Таблица 1 (сводный отчёт):"]
        remarks = check_1_18(df_all)

        kontur_for_1_18 = check_service_118_by_contours(df_all)
        # 5) Печатаем результаты
        if remarks:
            for r in remarks:
                lines.append(" -", r)
        count_212 = parse_kubernetes_service_counts(path)
        count_212_by_gis = parse_kubernetes_service_counts_by_gis(path)

        # 1.9 считаем так же «по контурам», вернётся dict
        count_19_by_contour = parse_kubernetes_service_counts(
            path,
            target_service_name="Сервисы интеграционного взаимодействия (услуга 1.1.9)"
        )

        # корректно получаем тоталы
        total_212 = self._sum_counts(count_212)                # сумма по 2.1.2
        total_19  = self._sum_counts(count_19_by_contour)      # сумма по 1.9

        if total_19 != total_212:
            report_5 = "Не совпадает количество услуг 1.1.9 и 1.2.1.2"
        #report_6_----------------------------------------------------

        for _, row in df.iterrows():
            import re

            def _canon(s: str) -> str:
                # нормализуем пробелы/кавычки, убираем неразрывные пробелы
                s = (s or "").replace("\xa0", " ")
                s = s.replace("“", '"').replace("”", '"').replace("«", '"').replace("»", '"')
                s = re.sub(r"\s+", " ", s)
                return s.strip()
            kontur_raw = (row.get('usage_contour') or '')
            gis_raw    = (row.get('gis_name') or '')

            kontur = _canon(kontur_raw)
            gis    = _canon(gis_raw)

            # словарь квантов по ГИС в рамках контура
            by_gis = count_212_by_gis.get(kontur, {}) or {}

            # индекс для сопоставления после канонизации
            canon_index = { _canon(k): k for k in by_gis.keys() }

            if gis:
                # если ГИС указан в строке, используем ТОЛЬКО его квант (или 0)
                matched_key = canon_index.get(gis)
                q_gis = by_gis.get(matched_key, 0) if matched_key is not None else 0
                quant = q_gis
            else:
                # если ГИС в строке пуст — тогда используем общий по контуру
                quant = count_212.get(kontur, 0)

            row_num = row.get('№ п/п', '<n/a>')
            msgs = []
            if row['service_name']=='Сервис управления процессами (услуга 1.1.12)':
                if ((pd.isna(row['comment_min']))):
                    continue
            if f:
                r=('Новая услуга', 'Заказанная услуга')
            else:
                r=('Новая услуга', 'Заказанная услуга', 'Изменение заказанной услуги')
            if row['service_status'] in r:

                # Ошибки, собранные валидаторами
                for param in rename_map.keys():

                    if row['service_name'] == 'Сервис управления процессами (услуга 1.1.12)':
                        if row['comment_test'] not in row['comment_min']:
                            continue
                        label = display_map.get(param, param)
                        code = rename_map.get(param)
                        actual = row.get(f"{code}_min", '<нет>')
                        desired = row.get(f"{code}_test", '<нет>')
                    else:
                        label = display_map.get(param, param)
                        code = rename_map.get(param)
                        actual = row.get(f"{code}_min", '<нет>')
                        desired = row.get(f"{code}_test", '<нет>')

                    if desired == 'Нет':
                        continue
                    if actual in (None, '', '<нет>'):
                        continue


                    if desired in (None, '', '<нет>'):
                        continue

                    if not str(actual).strip().isdigit():
                        continue
                    if not str(desired).strip().isdigit():
                        continue
                    comment = row['comment_min']
                    kontur = row['usage_contour']
                    # Пропускаем строки, где заявлено "Нет"

                    if desired == 'Нет' :
                        continue
                    comment=row['comment_min']
                    # Проверка на особенные услуги
                    kontur=row['usage_contour']# Здесь будет храниться текущщий контур обробатываемой строки

                    if (not(chek(row['service_name'],label, actual, desired, quant) is None) or (not(chek18(row['service_name'],label, actual, desired,quant, row, f18, kontur_for_1_18) is None))) and f18==False:
                        if ((row['service_name'] in ('Сервис IAM (услуга 1.1.13)')) or (row['service_name'] in ('Сервис журналирования (услуга 1.1.14)')) or (row['service_name'] in ('Сервис аудита (услуга 1.1.15)')) or (row['service_name'] in ('Сервис мониторинга (услуга 1.1.16)'))):
                            if (not(chek18(row['service_name'],label, actual, desired,quant, row, f18, kontur_for_1_18) is None)):
                                msgs.append(chek18(row['service_name'],label, actual, desired,quant, row, f18, kontur_for_1_18))
                            elif not (chek(row['service_name'], label, actual, desired, quant) is None):
                                msgs.append(chek(row['service_name'], label, actual, desired, quant))
                        elif not(chek(row['service_name'],label, actual, desired, quant) is None):
                            msgs.append(chek(row['service_name'],label, actual, desired, quant))
                    elif (not(chek(row['service_name'],label, actual, desired, quant) is None) or (not(chek18(row['service_name'],label, actual, desired,quant, row, f18, kontur_for_1_18) is None))) and f18:
                        if ((row['service_name'] in ('Сервис IAM (услуга 1.1.13)')) or (row['service_name'] in ('Сервис журналирования (услуга 1.1.14)')) or (row['service_name'] in ('Сервис аудита (услуга 1.1.15)')) or (row['service_name'] in ('Сервис мониторинга (услуга 1.1.16)'))):
                            msgs.append(chek18(row['service_name'],label, actual, desired,quant, row, f18, kontur_for_1_18))
                        elif not(chek(row['service_name'],label, actual, desired, quant) is None):
                            msgs.append(chek(row['service_name'],label, actual, desired, quant))

                cpu_iaas = row.get('cpu_iaas')
                cpu_paas = row.get('cpu_paas')
                hdd_paas = row.get('hdd_paas')
                ssd   = row.get('ssd_min')
                hddf  = row.get('hddf_min')
                hdds  = row.get('hdds_min')

                if pd.notna(cpu_iaas) and pd.notna(cpu_paas) and cpu_iaas != cpu_paas:
                    msgs.append(f"Значение CPU IaaS и CPU PaaS не совпадают ({cpu_iaas} ≠ {cpu_paas}).")

                total_iaas = sum(v for v in (ssd, hddf, hdds) if pd.notna(v))
                if pd.notna(hdd_paas) and hdd_paas != total_iaas:
                    msgs.append(f"Значение PaaS HDD ({hdd_paas}) не равно сумме SSD+HDD Fast+HDD Slow ({total_iaas}).")

            try:
                from main_chek.src.context_builder import ov as _ov_flag
            except Exception:
                _ov_flag = True

            if not _ov_flag:
                msgs = [m for m in msgs if not (isinstance(m, str) and m.startswith("Завышен параметр"))]
            # Формируем блок отчёта, если есть ошибки
            if msgs:
                svc = row['service_name']
                prod = row['digital_prod']
                status = row['service_status']
                lines.append(f"Строка {row_num} ({svc} {status}, {prod}):")
                for m in msgs:
                    lines.append(f" - {m}")
                lines.extend(['', '', ''])
        # — фильтрация «завышений» при отключённой галочке
            
            


        lines.append('Таблица 2\n')
        for i, row in df_2list.iterrows():
            if row['Наименование услуги']==5:
                continue
            mass2=[]
            com=[]
            # вызываем твою функцию проверки
            if not(row.isna().any()):
                com=full_chek2(row)

                if len(com)>0:
                    mass2=com
                
                if not _ov_flag:
                    mass2 = [m for m in mass2 if not (isinstance(m, str) and str(m).startswith("Завышен параметр"))]

            if mass2:
                svc = row['Наименование услуги']
                prod = row['Контур использования']
                status = row['Статус услуги']
                lines.append(f"Строка {row['№ п/п']} ({svc} {status}, {prod}):")
                for m in mass2:
                    lines.append(f" - {m}")
                lines.extend(['', '', ''])
        return '\n'.join(lines)