def get_occupied_periods(assignment):
    """Lấy danh sách các tiết học bị chiếm dụng bởi môn học dựa trên duration"""
    day = int(assignment['timeslot']['day'])
    start_period = int(assignment['timeslot']['period'])
    duration = int(assignment['course'].get('duration', 1))
    return [(day, start_period + i) for i in range(duration)]


def violates_hard_constraints(assignment, schedule):
    """
    Kiểm tra Ràng buộc cứng: Bao gồm Trùng lịch, Quá tải GV, 
    Xung đột Sinh viên và Vị trí Campus theo Năm học.
    """
    course = assignment['course']
    teacher = assignment['teacher']
    room = assignment['room']

    # Khởi tạo bảng lỗi - Đảm bảo có đủ các key cần thiết
    violations = {
        'room_double_booked': False,
        'teacher_double_booked': False,
        'student_conflict': False,
        'teacher_overload': False,
        'capacity': False,
        'lab_requirement': False,
        'time_overflow': False,
        'campus_location_violation': False, # Key quan trọng cho logic số 5
    }

    # 1. Ràng buộc tràn ngày (Check đầu tiên để tiết kiệm tài nguyên)
    start_period = int(assignment['timeslot']['period'])
    duration = int(course.get('duration', 1))
    if start_period + duration - 1 > 10:
        violations['time_overflow'] = True
        return violations 

    # 2. Ràng buộc vị trí Campus theo Năm học (Có ngoại lệ cho phòng Lab)
    cohort = course.get('cohort', 'Y1')
    room_campus = int(room.get('campus', 0))
    need_lab = course.get('need_lab', course.get('needLab', False))

    if need_lab:
        # NẾU LÀ MÔN LAB: Bắt buộc phải ở Hòa Lạc (Campus 1, 2, 3) không kể năm học
        if room_campus not in [1, 2, 3]:
            violations['campus_location_violation'] = True
    else:
        # NẾU LÀ MÔN LÝ THUYẾT: Tuân thủ đúng phân vùng địa lý
        if cohort == 'Y1':
            if room_campus not in [1, 2, 3]: # Y1 ở Hòa Lạc
                violations['campus_location_violation'] = True
        else:
            if room_campus != 0: # Y2, 3, 4 ở Mỹ Đình
                violations['campus_location_violation'] = True
    

    # 3. Kiểm tra các xung đột về Thời gian (Overlap)
    my_periods = set(get_occupied_periods(assignment))
    day = int(assignment['timeslot']['day'])
    teacher_daily_lessons = duration

    for other in schedule:
        other_course = other['course']
        
        # Tính tổng số tiết trong ngày của giáo viên
        if str(other['teacher']['id']) == str(teacher['id']) and int(other['timeslot']['day']) == day:
            teacher_daily_lessons += int(other_course.get('duration', 1))

        other_periods = set(get_occupied_periods(other))
        
        # Nếu trùng khung giờ học
        if my_periods.intersection(other_periods):
            if str(other['room']['id']) == str(room['id']):
                violations['room_double_booked'] = True
                
            if str(other['teacher']['id']) == str(teacher['id']):
                violations['teacher_double_booked'] = True
                
            # Chống trùng lịch môn CORE cho sinh viên cùng ngành/khóa
            if (course.get('type') == 'Core' and other_course.get('type') == 'Core' and 
                course.get('major') == other_course.get('major') and 
                course.get('cohort') == other_course.get('cohort')):
                violations['student_conflict'] = True

    # 4. Kiểm tra Quá tải Giảng viên (Max lessons per day)
    max_lessons = int(teacher.get('maxLessonsPerDay', 6))
    if teacher_daily_lessons > max_lessons:
        violations['teacher_overload'] = True

    # 5. Sức chứa phòng
    class_size = int(course.get('class_size', course.get('classSize', 0)))
    capacity = int(room.get('capacity', 0))
    if class_size > capacity:
        violations['capacity'] = True

    # 6. Yêu cầu phòng Lab
    need_lab = course.get('need_lab', course.get('needLab', False))
    is_lab = room.get('is_lab', room.get('isLab', False))
    # Chấp nhận nhiều định dạng dữ liệu (Boolean hoặc String)
    if need_lab in [1, True, 'True', '1'] and not (is_lab in [1, True, 'True', '1']):
        violations['lab_requirement'] = True

    return violations # CHỈ RETURN Ở ĐÂY để đảm bảo mọi check ở trên đều được thực hiện


def is_hard_feasible(assignment, schedule):
    """Trả về True nếu không có bất kỳ vi phạm ràng buộc cứng nào"""
    v = violates_hard_constraints(assignment, schedule)
    return not any(v.values())