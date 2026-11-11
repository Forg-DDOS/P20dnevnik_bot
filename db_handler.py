import os
import pandas as pd
from config import DB_PATH


class ExcelDatabase:
    def __init__(self):
        self.db_path = DB_PATH
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)

    def get_available_months(self):
        if not os.path.exists(self.db_path):
            return []
        months = [name for name in os.listdir(self.db_path) if os.path.isdir(os.path.join(self.db_path, name))]
        return sorted(months)

    def get_all_students(self):
        months = self.get_available_months()
        if not months:
            return []

        file_path = os.path.join(self.db_path, months[0], 'Пропуски.xlsx')
        if not os.path.exists(file_path):
            return []

        try:
            df = pd.read_excel(file_path, sheet_name=0, header=None)

            name_col = 1
            for col in df.columns:
                for idx in range(5):
                    val = str(df.iloc[idx, col]).upper()
                    if "ФИО" in val or "Ф.И.О." in val:
                        name_col = col
                        break

            names = df.iloc[:, name_col].dropna().tolist()
            clean_names = [n for n in names if
                           "Ф.И.О." not in str(n) and "ФИО" not in str(n) and not str(n).isnumeric()]
            return clean_names
        except Exception as e:
            print(f"Ошибка при получении списка: {e}")
            return []

    def get_student_absences(self, student_name, month):
        file_path = os.path.join(self.db_path, month, 'Пропуски.xlsx')
        if not os.path.exists(file_path):
            return "Файл не найден"

        try:
            xls = pd.ExcelFile(file_path)
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet, header=None)

                header_row_idx = None
                name_col = None
                for col in df.columns:
                    for idx in range(10):
                        val = str(df.iloc[idx, col]).upper()
                        if "ФИО" in val or "Ф.И.О." in val:
                            header_row_idx = idx
                            name_col = col
                            break
                    if header_row_idx is not None:
                        break

                if name_col is None:
                    name_col = 1

                student_row = df[df[name_col].astype(str).str.contains(student_name, case=False, na=False)]

                if not student_row.empty:
                    row = student_row.iloc[0]
                    uvazh = ne_uvazh = total = 0
                    for col in df.columns:
                        head_vals = str(df[col].head(6).values).lower()
                        val = row[col]

                        if pd.notna(val) and isinstance(val, (int, float)):
                            if "не- уважи" in head_vals or "неуваж" in head_vals:
                                ne_uvazh = int(val)
                            elif "уважи-тельно" in head_vals or "уваж" in head_vals:
                                uvazh = int(val)
                            elif "всего" in head_vals:
                                total = int(val)

                    return f"{total} (Уваж: {uvazh}, Неуваж: {ne_uvazh})"

            return "Нет данных по пропускам"
        except Exception as e:
            return f"Ошибка: {e}"

    def get_student_grades(self, student_name, month):
        file_path = os.path.join(self.db_path, month, 'Оценки.xlsx')
        if not os.path.exists(file_path):
            return "---", "0.0", {}

        try:
            xls = pd.ExcelFile(file_path)
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet, header=None)

                header_row_idx = None
                name_col = None
                for col in df.columns:
                    for idx in range(10):
                        val = str(df.iloc[idx, col]).upper()
                        if "ФИО" in val or "Ф.И.О." in val:
                            header_row_idx = idx
                            name_col = col
                            break
                    if header_row_idx is not None:
                        break

                if name_col is None:
                    name_col = 1
                    header_row_idx = 2

                student_row = df[df[name_col].astype(str).str.contains(student_name, case=False, na=False)]

                if not student_row.empty:
                    row = student_row.iloc[0]
                    subject_grades = {}
                    all_grades = []
                    current_subject = None

                    for col in df.columns:
                        header_val = str(df.iloc[header_row_idx, col]).strip()
                        top_vals = str(df[col].head(6).values).lower()

                        if "вс. оц." in top_vals or "средний балл" in top_vals:
                            break

                        if header_val != 'nan' and header_val.upper() not in ['№', 'ФИО', 'Ф.И.О.']:
                            current_subject = header_val

                        if current_subject:
                            student_val = row[col]
                            if pd.notna(student_val) and isinstance(student_val,
                                                                    (int, float)) and 1 <= student_val <= 10:
                                all_grades.append(int(student_val))
                                if current_subject not in subject_grades:
                                    subject_grades[current_subject] = []
                                subject_grades[current_subject].append(int(student_val))

                    if all_grades:
                        avg_grade = round(sum(all_grades) / len(all_grades), 2)
                        grades_str = ", ".join(map(str, all_grades))
                        formatted_subject_grades = {subj: ", ".join(map(str, grades)) for subj, grades in
                                                    subject_grades.items()}
                        return grades_str, str(avg_grade), formatted_subject_grades

            return "Нет оценок", "0.0", {}
        except Exception as e:
            return f"Ошибка: {e}", "0.0", {}

    def get_student_contacts(self, student_name):
        file_path = os.path.join(self.db_path, 'Контакты.xlsx')
        if not os.path.exists(file_path):
            return "Файл Контакты.xlsx не найден."

        try:
            df = pd.read_excel(file_path)

            name_col = None
            for col in df.columns:
                if "ФИО" in str(col).upper() or "Ф.И.О." in str(col).upper():
                    name_col = col
                    break

            if name_col is None:
                name_col = df.columns[0]

            student_row = df[df[name_col].astype(str).str.contains(student_name, case=False, na=False)]

            if student_row.empty:
                return "Контакты не найдены."

            row = student_row.iloc[0]
            contacts_info = []

            for col in df.columns:
                if col != name_col:
                    val = row[col]
                    if pd.notna(val):
                        if isinstance(val, float) and val.is_integer():
                            val = int(val)
                        contacts_info.append(f"{col}: {val}")

            if not contacts_info:
                return "Нет данных."

            return "\n".join(contacts_info)

        except Exception as e:
            return f"Ошибка чтения контактов: {e}"