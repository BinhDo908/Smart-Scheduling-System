import random
import copy
from constraints import is_hard_feasible, violates_hard_constraints


def calculate_cost(schedule):
    cost = 0
    for assignment in schedule:
        violations = violates_hard_constraints(assignment, schedule)
        # Đếm số True trong dict violations
        cost += sum(1 for flag in violations.values() if flag)
    return cost


def hill_climbing_schedule(initial_schedule, rooms, timeslots,
                           max_iterations=200, max_neighbors=50):
    """
    Hill Climbing:
    - Bắt đầu từ schedule ban đầu (Greedy sinh ra).
    - Mỗi bước:
        + Chọn ngẫu nhiên 1 assignment (một lớp học phần).
        + Thử đổi sang room/timeslot khác để tạo neighbor.
        + Nếu neighbor:
             * KHÔNG vi phạm ràng buộc cứng (is_hard_feasible == True)
             * VÀ có cost < cost hiện tại
          => chấp nhận neighbor làm trạng thái mới.
    - Dừng khi:
        + Không tìm được neighbor tốt hơn trong 1 vòng lặp
        + Hoặc đạt max_iterations.
    """
    current_schedule = copy.deepcopy(initial_schedule)
    current_cost = calculate_cost(current_schedule)

    for _ in range(max_iterations):
        improved = False

        for _ in range(max_neighbors):
            neighbor_schedule = copy.deepcopy(current_schedule)

            idx = random.randrange(len(neighbor_schedule))
            old_assignment = neighbor_schedule[idx]

            new_room = random.choice(rooms)
            new_timeslot = random.choice(timeslots)

            if (new_room['id'] == old_assignment['room']['id'] and
                new_timeslot['id'] == old_assignment['timeslot']['id']):
                continue

            new_assignment = {
                **old_assignment,
                'room': new_room,
                'timeslot': new_timeslot
            }

            neighbor_schedule[idx] = new_assignment

            if not is_hard_feasible(new_assignment, neighbor_schedule):
                continue

            new_cost = calculate_cost(neighbor_schedule)

            if new_cost < current_cost:
                current_schedule = neighbor_schedule
                current_cost = new_cost
                improved = True
                break 

        if not improved:
            break

    return current_schedule
