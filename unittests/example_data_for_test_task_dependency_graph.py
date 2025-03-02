"""
example data for task dependency graph tests
"""

import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from taskdependencygraph.models.ids import TaskDependencyId, TaskId
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge
from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.task_dependency_graph import TaskDependencyGraph

starting_time_of_run_1 = datetime(year=2024, month=3, day=12, hour=12, minute=10, tzinfo=timezone.utc)
starting_time_of_run_2 = datetime(year=2024, month=3, day=12, hour=5, minute=0, tzinfo=timezone.utc)

task_example_1 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="1234",
    name="name1",
    phase="phase name1",
    tags=["tag1"],
    planned_duration=timedelta(minutes=5),
)
task_example_2 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="234",
    name="name2",
    phase="phase name2",
    tags=["tag2"],
    planned_duration=timedelta(minutes=20),
)
task_example_3 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="34",
    name="name3",
    phase="phase name3",
    tags=["tag3"],
    planned_duration=timedelta(minutes=1),
)
task_example_4 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="4",
    name="name4",
    phase="phase name4",
    tags=["tag4"],
    planned_duration=timedelta(minutes=4),
)

task_list_1 = [task_example_1, task_example_2, task_example_3, task_example_4]

task_dependency_12 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_1.id, task_successor=task_example_2.id
)
task_dependency_13 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_1.id, task_successor=task_example_3.id
)
task_dependency_34 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_3.id, task_successor=task_example_4.id
)

dependency_list_1 = [task_dependency_12, task_dependency_13, task_dependency_34]


task_dependency_24 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_2.id, task_successor=task_example_4.id
)

dependency_list_1b = [task_dependency_12, task_dependency_13, task_dependency_34, task_dependency_24]


task_example_5 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="1234",
    name="name1",
    phase="phase name1",
    tags=["tag1"],
    planned_duration=timedelta(minutes=5),
)
task_example_6 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="234",
    name="name2",
    phase="phase name2",
    tags=["tag2"],
    planned_duration=timedelta(minutes=2),
)
task_example_7 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="34",
    name="name3",
    phase="phase name3",
    tags=["tag3"],
    planned_duration=timedelta(minutes=30),
)
task_example_8 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="4",
    name="name4",
    phase="phase name4",
    tags=["tag4"],
    planned_duration=timedelta(minutes=4),
)
task_example_9 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="5",
    name="name5",
    phase="phase name5",
    tags=["tag5"],
    planned_duration=timedelta(minutes=4),
)
task_example_10 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="6",
    name="name6",
    phase="phase name6",
    tags=["tag6"],
    planned_duration=timedelta(minutes=30),
)
task_example_11 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="7",
    name="name7",
    phase="phase name7",
    tags=["tag7"],
    planned_duration=timedelta(minutes=7),
)

task_list_2 = [
    task_example_5,
    task_example_6,
    task_example_7,
    task_example_8,
    task_example_9,
    task_example_10,
    task_example_11,
]
task_list_2b = [
    task_example_8,
    task_example_7,
    task_example_11,
    task_example_6,
    task_example_5,
    task_example_10,
    task_example_9,
]  # task_list not sorted by starting time to test, whether list is sorted by starting time with the method
# create_list_of_task_node_copies_with_planned_starting_time

task_dependency_56 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_5.id, task_successor=task_example_6.id
)
task_dependency_57 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_5.id, task_successor=task_example_7.id
)
task_dependency_78 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_7.id, task_successor=task_example_8.id
)
task_dependency_68 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_6.id, task_successor=task_example_8.id
)
task_dependency_89 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_8.id, task_successor=task_example_9.id
)
task_dependency_810 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_8.id, task_successor=task_example_10.id
)
task_dependency_911 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_9.id, task_successor=task_example_11.id
)
task_dependency_1011 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_10.id, task_successor=task_example_11.id
)

dependency_list_2 = [
    task_dependency_56,
    task_dependency_57,
    task_dependency_78,
    task_dependency_68,
    task_dependency_89,
    task_dependency_810,
    task_dependency_911,
    task_dependency_1011,
]


task_dependency_56 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_5.id, task_successor=task_example_6.id
)
task_dependency_69 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_5.id, task_successor=task_example_7.id
)
task_dependency_57 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_7.id, task_successor=task_example_8.id
)
task_dependency_78 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_6.id, task_successor=task_example_8.id
)
task_dependency_89 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_8.id, task_successor=task_example_9.id
)
task_dependency_910 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_8.id, task_successor=task_example_10.id
)
task_dependency_911 = TaskDependencyEdge(
    id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_example_9.id, task_successor=task_example_11.id
)

dependency_list_3 = [
    task_dependency_56,
    task_dependency_69,
    task_dependency_57,
    task_dependency_78,
    task_dependency_89,
    task_dependency_69,
    task_dependency_910,
    task_dependency_911,
]
non_existent_task_id_1 = TaskId(UUID("99999933-9999-9999-9999-999999999999"))
non_existent_task_id_2 = TaskId(UUID("99999933-9993-9999-9999-999999999999"))


def build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1):
    simple_graph = TaskDependencyGraph(task_list_1, dependency_list_1, starting_time_of_run_1)
    return simple_graph
    # Graph created with task_list_1 and dependency_list_1
    # (1-4 are the numbers of the task_examples):
    #           1
    #          //  \          / = not critical path
    #          2   3          // = critical path
    #               \
    #               4


def build_simple_graph_closed(task_list_1, dependency_list_1b, starting_time_of_run_1):
    simple_graph_cosed = TaskDependencyGraph(task_list_1, dependency_list_1b, starting_time_of_run_1)
    return simple_graph_cosed
    # With task_list_1 and dependency_list_1b the following graph is created:
    #            1
    #          //  \          / = not critical path
    #          2   3          // = critical path
    #         \\  /
    #           4


def build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1):
    complex_graph = TaskDependencyGraph(task_list_2, dependency_list_2, starting_time_of_run_1)
    return complex_graph
    # Graph created with task_list_2 and dependency_list_2
    # (5-11 are the numbers of the task_examples):
    #            5
    #          /  \\
    #          6   7
    #          \   //
    #            8
    #           /  \\
    #          9   10
    #          \   //
    #            11


def build_complex_graph_made_from_unsorted_task_list_and_with_different_starting_time(
    task_list_2, dependency_list_2, starting_time_of_run_2
):
    complex_graph_made_from_unsorted_task_list_and_with_different_starting_time = TaskDependencyGraph(
        task_list_2, dependency_list_2, starting_time_of_run_2
    )
    return complex_graph_made_from_unsorted_task_list_and_with_different_starting_time
    # With unsorted task_list_2b (not sorted by starting time) and dependency_list_2 the following graph is created:
    #           5                 the run starts at: year=2024, month=3, day=12, hour=5, minute=0
    #          /  \\
    #          6   7
    #          \   //
    #            8                task example 8 starts at: year=2024, month=3, day=12, hour=5, minute=35
    #           /  \\
    #          9   10
    #          \   //
    #            11


def build_another_complex_graph_with_unsorted_task_list_and_different_starting_time(
    task_list_2b, dependency_list_3, starting_time_of_run_2
):
    another_complex_graph_with_unsorted_task_list_and_different_starting_time = TaskDependencyGraph(
        task_list_2b, dependency_list_3, starting_time_of_run_2
    )
    return another_complex_graph_with_unsorted_task_list_and_different_starting_time
    # With unsorted task_list_2b (not sorted by starting time) and dependency_list_3 the following graph is created:
    #             5
    #            // \
    #           7    6
    #         //     /
    #        8      /
    #        \\    /
    #           9
    #        //   \
    #       10     11
