import pandas as pd
import sys
import subprocess

def check_and_install_libraries():
    required_packages = ['pandas', 'xlsxwriter']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"[*] Thư viện '{package}' chưa được cài đặt. Đang tự động cài đặt...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])
            print(f"[+] Đã cài đặt xong '{package}'!")

check_and_install_libraries()
DAY_MAP = {
    0: 'Hai',
    1: 'Ba',
    2: 'Tư',
    3: 'Năm',
    4: 'Sáu'
}

PERIOD_MAP = {
    1: {'start': '07:00', 'end': '08:00'},
    2: {'start': '08:00', 'end': '09:00'},
    3: {'start': '09:00', 'end': '10:00'},
    4: {'start': '10:00', 'end': '11:00'},
    5: {'start': '11:00', 'end': '12:00'},
    6: {'start': '12:00', 'end': '13:00'},
    7: {'start': '13:00', 'end': '14:00'},
    8: {'start': '14:00', 'end': '15:00'},
    9: {'start': '15:00', 'end': '16:00'},
    10: {'start': '16:00', 'end': '17:00'}
}


def export_schedule_to_excel(schedule_sorted, filepath):
    filepath = filepath.replace('.csv', '.xlsx')
    
    excel_data = []
    for assignment in schedule_sorted:
        ts = assignment['timeslot']
        
        
        day_id = int(ts.get('day'))
        thu_name = DAY_MAP.get(day_id, f"Unknown (ID:{day_id})")
        
        start_p = int(ts.get('period'))
        duration = int(assignment['course'].get('duration', 1))
        end_p = start_p + duration - 1
        
        start_time_info = PERIOD_MAP.get(start_p)
        end_time_info = PERIOD_MAP.get(end_p)

        if start_time_info and end_time_info:
            time_range = f"{start_time_info['start']} - {end_time_info['end']}"
        else:
            time_range = f"P.{start_p}-{end_p}" # Fallback if ID is missing

        
        excel_data.append({
            "Thứ": thu_name,         # (New Column)
            "Time Range": time_range, # (New Column)
            "Course ID": assignment['course']['name'],
            "Subject": assignment['course'].get('subject', ''),
            "Cohort": assignment['course'].get('cohort', ''),
            "Type": assignment['course'].get('type', ''),
            "Major": assignment['course'].get('major', ''),
            "Teacher": assignment['teacher']['name'],
            "Room": assignment['room']['name']
        })

    column_order = ["Thứ", "Time Range", "Course ID", "Subject", "Cohort", "Type", "Major", "Teacher", "Room"]
    schedule_df = pd.DataFrame(excel_data, columns=column_order)
    
    try:
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        
        sheet_name = 'Master Schedule'
        schedule_df.to_excel(writer, index=False, sheet_name=sheet_name)

        workbook  = writer.book
        worksheet = writer.sheets[sheet_name]

        
        standard_cell_format = workbook.add_format({
            'border': 1, 'valign': 'vcenter', 'align': 'center'
        })
        
        header_row_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter',
            'align': 'center', 'fg_color': '#4F81BD', 'font_color': 'white', 'border': 1
        })

        max_row = len(schedule_df.index)
        max_col = len(schedule_df.columns)
        worksheet.conditional_format(1, 0, max_row, max_col - 1, {
            'type': 'no_blanks', 'format': standard_cell_format
        })

        column_widths = [10, 18, 12, 28, 10, 15, 15, 20, 12]
        for i, width in enumerate(column_widths):
            worksheet.set_column(i, i, width)

        for col_num, value in enumerate(schedule_df.columns.values):
            worksheet.write(0, col_num, value, header_row_format)

        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, max_row, max_col - 1)

        writer.close()
        print(f"\n[+] Đã xuất file lịch trình Excel thành công tại: {filepath}")
        
    except PermissionError:
        print(f"\n[-] LỖI LƯU FILE: Không thể ghi đè lên file '{filepath}' do đang mở ở phần mềm khác.")
    except Exception as e:
        print(f"\n[-] LỖI XUẤT EXCEL: {e}")