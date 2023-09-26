from sailing_robot.tasks import TasksRunner
from sailing_robot.navigation import Navigation
from sailing_robot.heading_planning_laylines import HeadingPlan
from sailing_robot.helming_converted import Helming

tasks_def_1 = [
    {'kind': 'to_waypoint',
     'waypoint_ll': [50.936981, -1.405315]
    },
    {'kind': 'to_waypoint',
     'waypoint_ll': [50.93716, -1.405683]
     },
    {'kind': 'to_waypoint',
     'waypoint_ll': [50.936908,  -1.406061]
    }
]

tasks_bad = tasks_def_1 + [
    {'kind': 'test_bad'},
]

def run_tests():
    try:
        tr = TasksRunner(tasks_def_1, Navigation(utm_zone=30))
        #assert isinstance(tr.tasks[0], HeadingPlan)

        # tr = TasksRunner(tasks_bad, Navigation(utm_zone=30))
        # raise ValueError("Should have raised an exception")
    
        tr = TasksRunner(tasks_def_1, Navigation(utm_zone=30))
        tr.start_next_task()
        #assert isinstance(tr.active_task, HeadingPlan)
    
        print("All tests passed.")
    except Exception as e:
        print(f"Test failed: {e}")
        print(f"test number: {tr.task_ix}")

if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        pass