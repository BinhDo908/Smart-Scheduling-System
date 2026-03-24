import os
import time
import random
import pandas as pd
import concurrent.futures

from greedy import greedy_schedule
from hill_climbing import hill_climbing_schedule
from fitness import calculate_fitness


def run_optimization_pipeline(args):
    run_id, courses, teachers, rooms, timeslots = args
    
    random.seed(time.time() + run_id)
    
    print(f"[Luồng {run_id}] Bắt đầu xếp lịch...")
    initial_schedule = greedy_schedule(courses, teachers, rooms, timeslots, max_attempts=5000)
    
    if not initial_schedule:
        print(f"[Luồng {run_id}] Thất bại ở bước Greedy (Kẹt phòng/Giảng viên).")
        return float('inf'), []
        
    optimized_schedule = hill_climbing_schedule(initial_schedule, rooms, timeslots, max_iterations=200, max_neighbors=50)
    
    # Tính điểm phạt cuối cùng của luồng này
    score = calculate_fitness(optimized_schedule)
    print(f"[Luồng {run_id}] Hoàn thành! Điểm phạt (Fitness Penalty): {score}")
    
    return score, optimized_schedule

def main():
    current_dir = os.getcwd()
    base_dir = os.path.join(current_dir, 'data')
    
    try:
        teachers  = pd.read_csv(os.path.join(base_dir, 'teachers.csv')).to_dict(orient='records')
        rooms     = pd.read_csv(os.path.join(base_dir, 'rooms.csv')).to_dict(orient='records')
        courses   = pd.read_csv(os.path.join(base_dir, 'courses.csv')).to_dict(orient='records')
        timeslots = pd.read_csv(os.path.join(base_dir, 'timeslots.csv')).to_dict(orient='records')
    except FileNotFoundError as e:
        print(f"[-] Lỗi đọc dữ liệu: Không tìm thấy file tại {e.filename}")
        return

    NUM_RUNS = 10 #or 5
    start_total = time.time()
    
    args_list = [(i, courses, teachers, rooms, timeslots) for i in range(1, NUM_RUNS + 1)]
    
    best_schedule = []
    best_score = float('inf')

    with concurrent.futures.ProcessPoolExecutor(max_workers=NUM_RUNS) as executor:
        results = executor.map(run_optimization_pipeline, args_list)
        
        for score, schedule in results:
            if score < best_score and schedule:
                best_score = score
                best_schedule = schedule

    end_total = time.time()

    if not best_schedule:
        print("\n[-] TOÀN BỘ CÁC LUỒNG ĐỀU THẤT BẠI. Vui lòng kiểm tra lại sự xung đột trong Dữ liệu.")
        return

    print("="*60)
    print(f"[+] TÌM THẤY LỊCH TRÌNH TỐI ƯU NHẤT! Điểm phạt: {best_score}")
    print(f"[+] Tổng thời gian chạy đa luồng: {end_total - start_total:.2f} giây")
    print("="*60)

    schedule_sorted = sorted(
        best_schedule,
        key=lambda x: (int(x['timeslot'].get('day')), int(x['timeslot'].get('period')))
    )

    export_path = os.path.join(current_dir, 'final_schedule.csv')
    export_schedule_to_csv(schedule_sorted, export_path)
    generate_analytical_report(schedule_sorted)
    interactive_search(schedule_sorted)

def export_schedule_to_csv(schedule_sorted, filepath):
    schedule_data = []
    for assignment in schedule_sorted:
        ts = assignment['timeslot']
        start_p = int(ts.get('period'))
        duration = int(assignment['course'].get('duration', 1))
        end_p = start_p + duration - 1
        period_str = f"{start_p}-{end_p}" if duration > 1 else f"{start_p}"

        schedule_data.append({
            "Course ID": assignment['course']['name'],       # Mã môn (VD: BCSE101)
            "Subject": assignment['course'].get('subject', ''), # Tên môn học (VD: Programming)
            "Cohort": assignment['course'].get('cohort', ''),   # Năm học (VD: Y1)
            "Type": assignment['course'].get('type', ''),
            "Major": assignment['course'].get('major', ''),
            "Teacher": assignment['teacher']['name'],
            "Room": assignment['room']['name'],
            "TimeSlot": f"Day {ts.get('day')} Period {period_str}",
        })

    schedule_df = pd.DataFrame(schedule_data)
    
    try:
        schedule_df.to_csv(filepath, index=False)
        print(f"\n[+] Đã xuất file lịch trình thành công tại: {filepath}")
        print(f"Tổng số môn học đã xếp: {len(schedule_sorted)}")
    except PermissionError:
        print(f"\n[-] LỖI LƯU FILE: Không thể ghi đè lên file '{filepath}' do đang mở ở phần mềm khác.")


def interactive_search(schedule):
    while True:
        print("\n" + "="*50)
        print("   HỆ THỐNG TRA CỨU THỜI KHÓA BIỂU THÔNG MINH")
        print("="*50)
        print("1. Tìm kiếm theo Cơ sở (Campus - VD: C1, C2)")
        print("2. Tìm kiếm theo Môn học/Ngành học (VD: BCSE, Core)")
        print("3. Tìm kiếm theo Giảng viên")
        print("4. Lọc theo Phòng học")
        print("5. Xem lịch theo Ngày")
        print("x. Thoát chương trình")
        print("-" * 50)
        
        choice = input("Vui lòng chọn chức năng (1-5 hoặc x): ").strip().lower()
        if choice == 'x': break
            
        filtered_schedule = []
        if choice == '1':
            q = input("Nhập ký hiệu Campus: ").strip().upper()
            filtered_schedule = [a for a in schedule if str(a['room'].get('campus', '')).upper() == q or q in a['room']['name'].upper()]
        elif choice == '2':
            q = input("Nhập Tên môn học, Ngành (BCSE) hoặc Loại (Core): ").strip().lower()
            filtered_schedule = [a for a in schedule if q in a['course']['name'].lower() or q in str(a['course'].get('major')).lower() or q in str(a['course'].get('type')).lower()]
        elif choice == '3':
            q = input("Nhập tên Giảng viên: ").strip().lower()
            filtered_schedule = [a for a in schedule if q in a['teacher']['name'].lower()]
        elif choice == '4':
            q = input("Nhập tên Phòng học: ").strip().upper()
            filtered_schedule = [a for a in schedule if q in a['room']['name'].upper()]
        elif choice == '5':
            q = input("Nhập số Ngày (VD: 0, 1, 2, 3, 4): ").strip()
            filtered_schedule = [a for a in schedule if str(a['timeslot'].get('day')) == q]

        if filtered_schedule:
            for assignment in filtered_schedule:
                ts = assignment['timeslot']
                start_p = int(ts.get('period'))
                duration = int(assignment['course'].get('duration', 1))
                end_p = start_p + duration - 1
                period_str = f"{start_p}-{end_p}" if duration > 1 else f"{start_p}"

                c_name = assignment['course']['name']
                t_name = assignment['teacher']['name']
                r_name = assignment['room']['name']
                print(f" > Day {ts.get('day')} - P.{period_str:<5} | Course: {c_name:<8} | Teacher: {t_name:<18} | Room: {r_name:<8}")
            print(f"[*] Tìm thấy: {len(filtered_schedule)} ca học.")
        else:
            print("[-] Không tìm thấy dữ liệu phù hợp!")

def generate_analytical_report(schedule):
    print("\n" + "="*25 + " BÁO CÁO PHÂN TÍCH HỆ THỐNG " + "="*25)
    # 1. Thống kê Giảng viên
    teacher_loads = {}
    disliked_violation_count = 0
    for a in schedule:
        t_name = a['teacher']['name']
        duration = int(a['course'].get('duration', 1))
        teacher_loads[t_name] = teacher_loads.get(t_name, 0) + duration
        
        # Kiểm tra dính giờ ghét
        disliked_raw = str(a['teacher'].get('dislikedSlots', ''))
        disliked_slots = [s.strip() for s in disliked_raw.split(',') if s.strip()]
        start_p = int(a['timeslot']['period'])
        for i in range(duration):
            if str(start_p + i) in disliked_slots:
                disliked_violation_count += 1
                break

    # 2. Thống kê Phòng học
    room_usage = {}
    total_waste = 0
    for a in schedule:
        r_name = a['room']['name']
        duration = int(a['course'].get('duration', 1))
        room_usage[r_name] = room_usage.get(r_name, 0) + duration
        
        cap = int(a['room']['capacity'])
        size = int(a['course'].get('classSize', a['course'].get('class_size', 0)))
        total_waste += (cap - size) * duration

    # --- IN KẾT QUẢ ---
    
    print(f"\n[1] HIỆU SUẤT SỬ DỤNG PHÒNG (Room Utilization):")
    lab_rooms = [r for r in room_usage.keys() if "C2" in r or "C3" in r] # Nhận diện nhanh Lab qua mã phòng
    for r, hours in sorted(room_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
        util_rate = (hours / 50) * 100
        print(f" > Phòng {r:<8}: {hours:>2}/50 tiết ({util_rate:.1f}%)")

    print(f"\n[2] TOP 5 GIẢNG VIÊN CÓ KHỐI LƯỢNG CAO NHẤT:")
    for name, hours in sorted(teacher_loads.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f" > Giảng viên {name:<18}: {hours:>2} tiết/tuần")

    avg_waste = total_waste / len(schedule)
    print(f"\n[3] CHỈ SỐ CHẤT LƯỢNG LỊCH TRÌNH:")
    print(f" > Tổng số tiết vi phạm giờ ghét của GV: {disliked_violation_count}")
    print(f" > Trung bình ghế trống mỗi ca học    : {avg_waste:.1f} ghế")
    
    # Đánh giá tổng quát
    status = "Rất Tốt" if disliked_violation_count < 5 else "Khá"
    print(f"\n=> ĐÁNH GIÁ CHUNG: Hệ thống hoạt động {status}!")
    print("="*78)

if __name__ == "__main__":
    main()