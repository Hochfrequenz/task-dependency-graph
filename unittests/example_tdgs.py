import uuid
from datetime import datetime, timedelta, timezone

from taskdependencygraph.models.ids import TaskDependencyId, TaskId
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge
from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.task_dependency_graph import TaskDependencyGraph

# pylint:disable=anomalous-backslash-in-string

task_A = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="A",
    name="A",
    planned_duration=timedelta(minutes=5),
)
task_A_with_fixed_start_2024_01_01_23_56_00 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="A-fixed",
    name="A",
    planned_duration=timedelta(minutes=5),
    earliest_starttime=datetime(2024, 1, 1, 23, 56, 0, tzinfo=timezone.utc),
)
task_B = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="B",
    name="B",
    phase="phase name2",
    planned_duration=timedelta(minutes=20),
)
task_B_with_fixed_start_2024_01_02 = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="B-fixed",
    name="B",
    planned_duration=timedelta(minutes=20),
    earliest_starttime=datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
)
task_C = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="C",
    name="C",
    planned_duration=timedelta(minutes=1),
)
task_D = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="D",
    name="D",
    planned_duration=timedelta(minutes=4),
)


graph_anna = TaskDependencyGraph(
    task_list=[task_A, task_B, task_C, task_D],
    dependency_list=[
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_A.id, task_successor=task_B.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_A.id, task_successor=task_C.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_B.id, task_successor=task_D.id),
    ],
    starting_time_of_run=datetime.now(timezone.utc),
)
"""
    B(20)--->D(4)
   /
A(5)--->C(1)
"""

graph_bernd = TaskDependencyGraph(
    task_list=[task_A, task_B_with_fixed_start_2024_01_02, task_C, task_D],
    dependency_list=[
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()),
            task_predecessor=task_A.id,
            task_successor=task_B_with_fixed_start_2024_01_02.id,
        ),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_A.id, task_successor=task_C.id),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()),
            task_predecessor=task_B_with_fixed_start_2024_01_02.id,
            task_successor=task_D.id,
        ),
    ],
    starting_time_of_run=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
)
"""
    B(20, but not before 2024-01-02)--->D(4)
   /
A(5)--->C(1)
"""

graph_carmen = TaskDependencyGraph(
    task_list=[task_A_with_fixed_start_2024_01_01_23_56_00, task_B_with_fixed_start_2024_01_02, task_C, task_D],
    dependency_list=[
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()),
            task_predecessor=task_A_with_fixed_start_2024_01_01_23_56_00.id,
            task_successor=task_B_with_fixed_start_2024_01_02.id,
        ),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()),
            task_predecessor=task_A_with_fixed_start_2024_01_01_23_56_00.id,
            task_successor=task_C.id,
        ),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()),
            task_predecessor=task_B_with_fixed_start_2024_01_02.id,
            task_successor=task_D.id,
        ),
    ],
    starting_time_of_run=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
)
"""
    B(20, but not before 2024-01-02)--->D(4)
   /
A(5, but not before 2024-01-01T23:59:56)--->C(1)
"""


task_G = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="G",
    name="G",
    planned_duration=timedelta(minutes=1),
)
task_H = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="H",
    name="H",
    planned_duration=timedelta(minutes=10),
)
task_I = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="I",
    name="I",
    planned_duration=timedelta(minutes=10),
)
task_L = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="L",
    name="L",
    planned_duration=timedelta(minutes=5),
)
task_J = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="J",
    name="J",
    planned_duration=timedelta(minutes=20),
)
task_K = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="K",
    name="K",
    planned_duration=timedelta(minutes=20),
)
graph_daniel = TaskDependencyGraph(
    task_list=[task_G, task_H, task_I, task_J, task_K, task_L],
    dependency_list=[
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_G.id, task_successor=task_H.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_H.id, task_successor=task_I.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_I.id, task_successor=task_L.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_G.id, task_successor=task_J.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_J.id, task_successor=task_K.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_K.id, task_successor=task_L.id),
    ],
    starting_time_of_run=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
)
"""
Daniel has two parallel paths, none of its tasks has an earliest possible start.
     H(10)----I(10)
    /             \
G(1)               L(5)
   \              /
    J(20)----K(20)

Note, that the critical path is G->J->K->L.
"""

task_H_with_fixed_start_2024_01_02 = task_H.model_copy(
    update={"earliest_starttime": datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)}, deep=True
)
graph_emily = TaskDependencyGraph(
    task_list=[task_G, task_H_with_fixed_start_2024_01_02, task_I, task_J, task_K, task_L],
    dependency_list=[
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()),
            task_predecessor=task_G.id,
            task_successor=task_H_with_fixed_start_2024_01_02.id,
        ),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()),
            task_predecessor=task_H_with_fixed_start_2024_01_02.id,
            task_successor=task_I.id,
        ),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_I.id, task_successor=task_L.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_G.id, task_successor=task_J.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_J.id, task_successor=task_K.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_K.id, task_successor=task_L.id),
    ],
    starting_time_of_run=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
)
"""
Emily has a similar structure as Daniel, but the H node has an earliest possible start:
     H(10, but not before 2024-01-02)----I(10)
    /                                         \
G(1)                                           L(5)
   \                                          /
    J(20)----K(20)---------------------------
"""

task_M = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="M",
    name="M",
    planned_duration=timedelta(minutes=1),
)
task_N = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="N",
    name="N",
    planned_duration=timedelta(minutes=2),
)
task_N_milestone = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="N",
    name="N",
    planned_duration=timedelta(minutes=2),
    is_milestone=True,
)
task_O = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="O",
    name="O",
    planned_duration=timedelta(minutes=2),
)
task_P = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="P",
    name="P",
    planned_duration=timedelta(minutes=5),
    earliest_starttime=datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
)
task_Q = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="Q",
    name="Q",
    planned_duration=timedelta(minutes=3),
    earliest_starttime=datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
)
task_R = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="R",
    name="R",
    planned_duration=timedelta(minutes=4),
)
task_S = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="S",
    name="S",
    planned_duration=timedelta(minutes=20),
)
task_S_milestone = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="S",
    name="S",
    planned_duration=timedelta(minutes=20),
    is_milestone=True,
)
task_T = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="T",
    name="T",
    planned_duration=timedelta(minutes=21),
)
task_U = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="U",
    name="U",
    planned_duration=timedelta(minutes=22),
    earliest_starttime=datetime(2024, 1, 3, 0, 26, 0, tzinfo=timezone.utc),
)
task_V = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="V",
    name="V",
    planned_duration=timedelta(minutes=23),
    earliest_starttime=datetime(2024, 1, 4, 0, 0, 0, tzinfo=timezone.utc),
)
task_W = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="W",
    name="W",
    planned_duration=timedelta(minutes=17),
)
task_W_milestone = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="W",
    name="W",
    planned_duration=timedelta(minutes=17),
    is_milestone=True,
)
task_X = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="X",
    name="X",
    planned_duration=timedelta(minutes=10),
)
task_Y = TaskNode(
    id=TaskId(uuid.uuid4()),
    external_id="Y",
    name="Y",
    planned_duration=timedelta(days=1),
)
graph_ferdinand = TaskDependencyGraph(
    task_list=[task_M, task_N, task_O, task_P, task_Q, task_R, task_S, task_T, task_U, task_V, task_W, task_X, task_Y],
    dependency_list=[
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_M.id, task_successor=task_N.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_N.id, task_successor=task_O.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_O.id, task_successor=task_P.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_P.id, task_successor=task_S.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_S.id, task_successor=task_T.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_T.id, task_successor=task_V.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_V.id, task_successor=task_W.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_N.id, task_successor=task_Q.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_Q.id, task_successor=task_R.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_R.id, task_successor=task_S.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_S.id, task_successor=task_U.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_U.id, task_successor=task_W.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_Q.id, task_successor=task_X.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_X.id, task_successor=task_Y.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_Y.id, task_successor=task_R.id),
    ],
    starting_time_of_run=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
)


"""
           O(2)-P(5, not before 2024-01-02)      T(21)--V(23, not before 2024-01-04)
          /                               \     /                                   \
M(1)---N(2)                                S(20)                                     W(17)
         \                                /    \                                    /
          Q(3, not before 2024-01-03)-R(4)      U(22, not before 2024-01-03+26m)----
           \                         /
            X(10)-----Y(1day)-------
Ferdinand contains 2x2 parallel paths
"""

graph_ferdinand_with_milestones = TaskDependencyGraph(
    task_list=[
        task_M,
        task_N_milestone,
        task_O,
        task_P,
        task_Q,
        task_R,
        task_S_milestone,
        task_T,
        task_U,
        task_V,
        task_W_milestone,
        task_X,
        task_Y,
    ],
    dependency_list=[
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_M.id, task_successor=task_N_milestone.id
        ),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_N_milestone.id, task_successor=task_O.id
        ),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_O.id, task_successor=task_P.id),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_P.id, task_successor=task_S_milestone.id
        ),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_S_milestone.id, task_successor=task_T.id
        ),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_T.id, task_successor=task_V.id),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_V.id, task_successor=task_W_milestone.id
        ),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_N_milestone.id, task_successor=task_Q.id
        ),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_Q.id, task_successor=task_R.id),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_R.id, task_successor=task_S_milestone.id
        ),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_S_milestone.id, task_successor=task_U.id
        ),
        TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_U.id, task_successor=task_W_milestone.id
        ),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_Q.id, task_successor=task_X.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_X.id, task_successor=task_Y.id),
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_Y.id, task_successor=task_R.id),
    ],
    starting_time_of_run=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
)
"""
same as graph_ferdindand but with milestones at N, S and W
"""
