def get_occupied_periods(assignment):
    day = int(assignment['timeslot']['day'])
    start_period = int(assignment['timeslot']['period'])
    duration = int(assignment['course'].get('duration', 1))
    return [(day, start_period + i) for i in range(duration)]


def calculate_fitness(schedule):
    if not schedule:
        return float('inf')

    penalty = 0
    teacher_day_schedule = {}
    cohort_day_schedule = {} 

    for assignment in schedule:
        # Gom nhóm theo Giảng viên
        t_name = assignment['teacher']['name']
        day = int(assignment['timeslot']['day'])
        
        if t_name not in teacher_day_schedule:
            teacher_day_schedule[t_name] = {}
        if day not in teacher_day_schedule[t_name]:
            teacher_day_schedule[t_name][day] = []
        teacher_day_schedule[t_name][day].append(assignment)

        course = assignment['course']
        if course.get('type') == 'Elective':
            cohort_key = f"{course.get('major')}_{course.get('cohort')}"
            if cohort_key not in cohort_day_schedule:
                cohort_day_schedule[cohort_key] = {}
            if day not in cohort_day_schedule[cohort_key]:
                cohort_day_schedule[cohort_key][day] = []
            cohort_day_schedule[cohort_key][day].append(assignment)

    # --- TIÊU CHÍ 1 & 2: SỨC CHỨA VÀ SỞ THÍCH GIẢNG VIÊN ---
    for assignment in schedule:
        cap = int(assignment['room']['capacity'])
        size = int(assignment['course'].get('class_size', assignment['course'].get('classSize', 0)))
        waste = cap - size
        if waste > 0:
            penalty += (waste * 1)

        # 2. Vi phạm sở thích giờ dạy
        disliked_raw = str(assignment['teacher'].get('dislikedSlots', ''))
        disliked_slots = [s.strip() for s in disliked_raw.split(',') if s.strip()]
        
        my_periods = get_occupied_periods(assignment)
        for _, period in my_periods:
            if str(period) in disliked_slots:
                penalty += 50 # Phạt nặng nếu rơi vào giờ GV không thích

    # --- TIÊU CHÍ 3: DI CHUYỂN CAMPUS ---
    for t_name, days in teacher_day_schedule.items():
        for day, assignments in days.items():
            assignments.sort(key=lambda x: int(x['timeslot']['period']))
            
            for i in range(len(assignments) - 1):
                ca_truoc = assignments[i]
                ca_sau = assignments[i+1]
                
                if str(ca_truoc['room'].get('campus')) != str(ca_sau['room'].get('campus')):
                    penalty += 100 

    # --- TIÊU CHÍ 4: TRÙNG LỊCH MÔN TỰ CHỌN CỦA SINH VIÊN ---
    for cohort_key, days in cohort_day_schedule.items():
        for day, assignments in days.items():
            for i in range(len(assignments)):
                for j in range(i + 1, len(assignments)):
                    periods_i = set(get_occupied_periods(assignments[i]))
                    periods_j = set(get_occupied_periods(assignments[j]))
                    
                    if periods_i.intersection(periods_j):
                        penalty += 20 

    return penalty