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
        f4_value = self.proc.get_cell_value(target_path, cell="F4", sheet_name="Титул")
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
        final_report = f"{f4_value}\n\n{missing_report}\n\n\n{detailed_report}"
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
        import re

        services_all = df_all["service_name"].astype(str).tolist()

        def _extract_code(service_name: str) -> str | None:
            m = re.search(r"\(услуга\s*([0-9.]+)\)", str(service_name))
            return m.group(1) if m else None

        def _is_vitrin_contour(df_all: pd.DataFrame, contour_name: str) -> bool:
            allowed_codes = {"1.1.13", "1.1.14", "1.1.15", "1.1.16", "1.1.18", "1.1.31"}

            sub = df_all[
                df_all["usage_contour"].astype(str).str.strip().str.upper() ==
                str(contour_name).strip().upper()
                ]

            if sub.empty:
                return False

            codes = {
                _extract_code(s) for s in sub["service_name"].astype(str).tolist()
                if _extract_code(s)
            }

            return ("1.1.18" in codes) and codes.issubset(allowed_codes)


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
        vitrin_rows_errors = check_vitrin_fixed_params_rows(df_all)
        if vitrin_rows_errors:
            for e in vitrin_rows_errors:
                lines.append(f" - {e}")
            lines.append("")
        kontur_for_1_18 = check_service_118_by_contours(df_all)
        # 5) Печатаем результаты
        if remarks:
            for r in remarks:
                lines.append(f" - {r}")


        def _norm_text(s):
            return " ".join(str(s).replace("\xa0", " ").split()).strip()

        valid_statuses = {"Новая услуга", "Заказанная услуга", "Обновленная услуга" , "Продление услуги"}

        # 1.1.9 из первой таблицы
        df_19 = df_all.copy()
        df_19["service_name"] = df_19["service_name"].astype(str).map(_norm_text)
        df_19["usage_contour"] = df_19["usage_contour"].astype(str).map(_norm_text)
        df_19["gis_name"] = df_19["gis_name"].astype(str).map(_norm_text)
        df_19["service_status"] = df_19["service_status"].astype(str).map(_norm_text)

        df_19 = df_19[
            (df_19["service_name"] == "Сервисы интеграционного взаимодействия (услуга 1.1.9)") &
            (df_19["service_status"].isin(valid_statuses))
            ]

        count_19_by_pair = (
            df_19.groupby(["usage_contour", "gis_name"])
            .size()
            .to_dict()
        )

        # 1.2.1.2 из второй таблицы
        df_212 = df_2list.copy()
        df_212["Наименование услуги"] = df_212["Наименование услуги"].astype(str).map(_norm_text)
        df_212["Контур использования"] = df_212["Контур использования"].astype(str).map(_norm_text)
        df_212["Наименование ГИС (Сервиса)"] = df_212["Наименование ГИС (Сервиса)"].astype(str).map(_norm_text)
        df_212["Статус услуги"] = df_212["Статус услуги"].astype(str).map(_norm_text)

        df_212 = df_212[
            (df_212["Наименование услуги"] == "Система управления контейнерами (услуга 1.2.1.2)") &
            (df_212["Статус услуги"].isin(valid_statuses))
            ]

        count_212_by_pair = (
            df_212.groupby(["Контур использования", "Наименование ГИС (Сервиса)"])
            .size()
            .to_dict()
        )

        all_pairs = set(count_19_by_pair.keys()) | set(count_212_by_pair.keys())

        for contour, gis in sorted(all_pairs):
            count_19 = count_19_by_pair.get((contour, gis), 0)
            count_212 = count_212_by_pair.get((contour, gis), 0)

            if count_19 != count_212:
                lines.append(
                    f" - на контуре {contour}, ГИС {gis}, количество "
                    f"Сервисы интеграционного взаимодействия (услуга 1.1.9): {count_19}, "
                    f"Система управления контейнерами (услуга 1.2.1.2): {count_212}. "
                    f"Количество не соответствует"
                )

        if all_pairs:
            lines.append("")

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
            is_vitrin_current_contour = _is_vitrin_contour(df_all, kontur)
            gis    = _canon(gis_raw)

            pair_key = (kontur, gis)
            quant = count_212_by_pair.get(pair_key, 0)

            row_num = row.get('№ п/п', '<n/a>')
            msgs = []
            if row['service_name']=='Сервис управления процессами (услуга 1.1.12)':
                if ((pd.isna(row['comment_min']))):
                    continue
            r = ('Новая услуга', 'Заказанная услуга', 'Обновленная услуга' , "Продление услуги")
            if row['service_status'] in r:

                # Ошибки, собранные валидаторами
                for param in rename_map.keys():
                    if should_skip_row_errors(row, kontur_for_1_18):
                        continue
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

                    _current_contour = str(row.get("usage_contour", "")).strip().upper()

                    # В контуре с 1.1.18: обычную проверку 1.1.13 не запускаем (её делает check_1_18)
                    if kontur_for_1_18.get(_current_contour, False) and row.get(
                            "service_name") == "Сервис IAM (услуга 1.1.13)":
                        continue

                    # Для витринного заказа: обычную проверку 1.1.16 не запускаем (её делает построчная витринная проверка)
                    if is_vitrin_current_contour and row.get("service_name") == "Сервис мониторинга (услуга 1.1.16)":
                        continue
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
            if row.dropna().empty:
                continue

            com = full_chek2(row)

            mass2 = com if com else []
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