import random
from constraints import is_hard_feasible

def greedy_schedule(courses, teachers, rooms, timeslots, max_attempts=5000):
    schedule = []
    
    # --- BƯỚC 1: ĐỒNG BỘ DỮ LIỆU ---
    for c in courses:
        if 'class_size' not in c and 'classSize' in c:
            c['class_size'] = c['classSize']
        if 'need_lab' not in c and 'needLab' in c:
            c['need_lab'] = c['needLab']
        c['duration'] = int(c.get('duration', 1))
            
    for r in rooms:
        if 'is_lab' not in r and 'isLab' in r:
            r['is_lab'] = r['isLab']
        r['campus'] = int(r.get('campus', 0))
    courses_sorted = sorted(courses, key=lambda x: 0 if x.get('type') == 'Core' else 1)

    # --- BƯỚC 2: TIẾN HÀNH XẾP LỊCH ---
    for course in courses_sorted:
        valid_assignment = False
        attempts = 0

        course_major = str(course.get('major', ''))
        course_subject = str(course.get('subject', ''))
        
        eligible_teachers = [
            t for t in teachers 
            if course_major in str(t.get('majors', '')) and course_subject in str(t.get('subjects', ''))
        ]
        
        if not eligible_teachers:
            print(f"[-] BỎ QUA: Không tìm thấy GV ngành {course_major} dạy môn {course_subject} ({course['name']}).")
            continue

        # 2.2 AUTO-LOCATION: Lọc phòng phù hợp Campus (Y1 ở Hòa Lạc 1,2,3 | Y2,3,4 ở Mỹ Đình 0)
        cohort = course.get('cohort', 'Y1')
        need_lab = course.get('need_lab', False)

        if need_lab:
            eligible_rooms = [r for r in rooms if r['is_lab'] and r['campus'] in [1, 2, 3]]
        else:
            if cohort == 'Y1':
                eligible_rooms = [r for r in rooms if r['campus'] in [1, 2, 3] and not r['is_lab']]
            else:
                eligible_rooms = [r for r in rooms if r['campus'] == 0]

        # 2.3 VÒNG LẶP TÌM KHE TRỐNG (Chỉ cần 1 vòng lặp duy nhất)
        while not valid_assignment and attempts < max_attempts:
            timeslot = random.choice(timeslots)
            room = random.choice(eligible_rooms) 
            teacher = random.choice(eligible_teachers)

            assignment = {
                'course': course,
                'teacher': teacher,
                'room': room,
                'timeslot': timeslot
            }

            if is_hard_feasible(assignment, schedule):
                schedule.append(assignment)
                valid_assignment = True
            else:
                attempts += 1

        if not valid_assignment:
            print(f"[-] THẤT BẠI: Không thể xếp {course['name']} sau {max_attempts} lần thử.")

    return schedule