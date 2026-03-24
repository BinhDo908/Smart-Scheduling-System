def get_occupied_periods(assignment):
    day = int(assignment['timeslot']['day'])
    start_period = int(assignment['timeslot']['period'])
    duration = int(assignment['course'].get('duration', 1))
    return [(day, start_period + i) for i in range(duration)]


def violates_hard_constraints(assignment, schedule):
    course = assignment['course']
    teacher = assignment['teacher']
    room = assignment['room']

    violations = {
        'room_double_booked': False,
        'teacher_double_booked': False,
        'student_conflict': False,
        'teacher_overload': False,
        'capacity': False,
        'lab_requirement': False,
        'time_overflow': False,
        'campus_location_violation': False,
    }

    start_period = int(assignment['timeslot']['period'])
    duration = int(course.get('duration', 1))
    if start_period + duration - 1 > 10:
        violations['time_overflow'] = True
        return violations 

    cohort = course.get('cohort', 'Y1')
    room_campus = int(room.get('campus', 0))
    need_lab = course.get('need_lab', course.get('needLab', False))

    if need_lab:
        if room_campus not in [1, 2, 3]:
            violations['campus_location_violation'] = True
    else:
        if cohort == 'Y1':
            if room_campus not in [1, 2, 3]:
                violations['campus_location_violation'] = True
        else:
            if room_campus != 0: 
                violations['campus_location_violation'] = True
    

    my_periods = set(get_occupied_periods(assignment))
    day = int(assignment['timeslot']['day'])
    teacher_daily_lessons = duration

    for other in schedule:
        other_course = other['course']
        
        if str(other['teacher']['id']) == str(teacher['id']) and int(other['timeslot']['day']) == day:
            teacher_daily_lessons += int(other_course.get('duration', 1))

        other_periods = set(get_occupied_periods(other))
        
        if my_periods.intersection(other_periods):
            if str(other['room']['id']) == str(room['id']):
                violations['room_double_booked'] = True
                
            if str(other['teacher']['id']) == str(teacher['id']):
                violations['teacher_double_booked'] = True
                
            if (course.get('type') == 'Core' and other_course.get('type') == 'Core' and 
                course.get('major') == other_course.get('major') and 
                course.get('cohort') == other_course.get('cohort')):
                violations['student_conflict'] = True

    max_lessons = int(teacher.get('maxLessonsPerDay', 6))
    if teacher_daily_lessons > max_lessons:
        violations['teacher_overload'] = True

    class_size = int(course.get('class_size', course.get('classSize', 0)))
    capacity = int(room.get('capacity', 0))
    if class_size > capacity:
        violations['capacity'] = True

    need_lab = course.get('need_lab', course.get('needLab', False))
    is_lab = room.get('is_lab', room.get('isLab', False))
    if need_lab in [1, True, 'True', '1'] and not (is_lab in [1, True, 'True', '1']):
        violations['lab_requirement'] = True

    return violations 


def is_hard_feasible(assignment, schedule):
    v = violates_hard_constraints(assignment, schedule)
    return not any(v.values())