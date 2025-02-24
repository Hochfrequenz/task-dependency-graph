import copy
import uuid
from datetime import datetime, timedelta, timezone

import networkx as nx  # type: ignore[import-untyped]
import pytest
from pydantic import AwareDatetime

from taskdependencygraph.task_dependency_graph import TaskDependencyGraph
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge
from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.models.task_node_as_artificial_endnode import task_node_as_artificial_endnode
from taskdependencygraph.models.task_node_as_artificial_startnode import task_node_as_artificial_startnode
from taskdependencygraph.models.ids import TaskDependencyId, TaskId

from .example_data_for_test_task_dependency_graph import (
    build_another_complex_graph_with_unsorted_task_list_and_different_starting_time,
    build_complex_graph,
    build_complex_graph_made_from_unsorted_task_list_and_with_different_starting_time,
    build_simple_graph,
    build_simple_graph_closed,
    dependency_list_1,
    dependency_list_1b,
    dependency_list_2,
    dependency_list_3,
    non_existent_task_id_1,
    non_existent_task_id_2,
    starting_time_of_run_1,
    starting_time_of_run_2,
    task_example_4,
    task_example_8,
    task_example_9,
    task_example_11,
    task_list_1,
    task_list_2,
    task_list_2b,
)
from .example_tdgs import (
    graph_bernd,
    graph_carmen,
    graph_daniel,
    graph_emily,
    graph_ferdinand,
    graph_ferdinand_with_milestones,
    task_B_with_fixed_start_2024_01_02,
    task_C,
    task_D,
    task_G,
    task_H_with_fixed_start_2024_01_02,
    task_I,
    task_J,
    task_K,
    task_L,
    task_M,
    task_N,
    task_O,
    task_P,
    task_Q,
    task_R,
    task_S,
    task_S_milestone,
    task_T,
    task_U,
    task_V,
    task_W,
    task_W_milestone,
    task_X,
    task_Y,
)

# pylint:disable=anomalous-backslash-in-string
# The backslashes are part of an ASCII art embedded into a docstring.

# pylint:disable=too-many-arguments
assert task_H_with_fixed_start_2024_01_02.earliest_starttime is not None  # to please mypy
assert task_Q.earliest_starttime is not None  # to please mypy


class TestIfNodesAndEdgesAreCombinedToBuildPaths:
    """
    This test tests, if nodes and edges are not only added to the Task Dependency Graph,
    but also connected to build paths between nodes.

    Simple graph: Using task_list_1 and dependency_list_1 the nodes and edges should be connected like this
    (1-4 are the numbers of the task_examples):
          1
         /  \
         2   3
              \
              4

    Complex_graph: Using task_list_2 and dependency_list_2 the nodes and edges should be connected like this
    (5-11 are the numbers of the task_examples):
           5
         /  \
         6   7
         \   /
           8
          /  \
         9   10
         \   /
           11

    """

    @pytest.mark.parametrize(
        "graph, task_1, task_2",
        [
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1),
                task_list_1[0],
                task_list_1[3],
                id="test 1 for existing path",
            ),
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1),
                task_list_1[0],
                task_list_1[1],
                id="test 2 for existing path",
            ),
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1),
                task_list_1[0],
                task_node_as_artificial_endnode,
                id="test 3 for path between a task and the artificial endnode",
            ),
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1),
                task_node_as_artificial_startnode,
                task_node_as_artificial_endnode,
                id="test 3 for path between artificial startnode and endnode",
            ),
            pytest.param(
                build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1),
                task_node_as_artificial_startnode,
                task_node_as_artificial_endnode,
                id="test 4 for path between artificial startnode and endnode in second graph",
            ),
        ],
    )
    def test_if_graph_has_paths(
        self,
        graph: TaskDependencyGraph,
        task_1: TaskNode,
        task_2: TaskNode,
    ):
        # pylint: disable=protected-access
        assert nx.has_path(graph._graph, task_1.id, task_2.id) is True


class TestIfTasksAreIdentifiedAsBeingOnCriticalPath:
    """
    This test makes sure, that tasks, that are on the critical path, are identified as such and vice versa by the
    method "check_if_task_is_on_critical_path"

    The tests create and use the following graphs:
    Simple graph: Graph created with task_list_1 and dependency_list_1
    (1-4 are the numbers of the task_examples):
          1
         //  \          / = not critical path
         2   3          // = critical path
              \
              4

    Complex graph: Graph created with task_list_2 and dependency_list_2
    (5-11 are the numbers of the task_examples):
           5
         /  \\
         6   7
         \   //
           8
          /  \\
         9   10
         \   //
           11

    """

    @pytest.mark.parametrize(
        "graph, task_id, expected_result",
        [
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1), task_list_1[1].id, True
            ),
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1), task_list_1[0].id, True
            ),
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1), task_list_1[2].id, False
            ),
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1), task_list_1[3].id, False
            ),
            pytest.param(
                build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1), task_list_2[2].id, True
            ),
            pytest.param(
                build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1),
                task_node_as_artificial_startnode.id,
                True,
            ),
        ],
    )
    def test_identification_if_task_is_on_critical_path(
        self,
        graph: TaskDependencyGraph,
        task_id: TaskId,
        expected_result: bool,
    ):
        """
        This test checks if a task is correctly identified as being/as not being on the critical path.
        """
        assert graph.is_on_critical_path(task_id) is expected_result

    @pytest.mark.parametrize(
        "graph, non_existent_task_id",
        [
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1), non_existent_task_id_1
            ),
            pytest.param(
                build_simple_graph(task_list_1, dependency_list_1, starting_time_of_run_1), non_existent_task_id_2
            ),
        ],
    )
    def test_if_not_existent_task_id_causes_value_error(
        self,
        graph: TaskDependencyGraph,
        non_existent_task_id: TaskId,
    ):
        """
        This test checks if a non-existent task id causes a value error, when checking, whether it is on the
        critical path (instead of returning False)
        """
        with pytest.raises(ValueError):
            _ = graph.is_on_critical_path(non_existent_task_id)


class TestIfDurationOfCriticalPathBeforeTaskIsCalculatedCorrectly:
    """
    This test checks if the method "calculate_planned_duration_of_predecessor_tasks_on_critical_path" works the way
    it was intended to work.
    This test creates and uses a graph (complex graph), created with task_list_2 and dependency_list_2
    (5-11 are the numbers of the task_examples):
           5
         /  \\
         6   7
         \   //
           8
          /  \\
         9   10
         \   //
           11

    """

    @pytest.mark.parametrize(
        "task_id, graph, expected",
        [
            pytest.param(
                task_example_9.id,
                build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1),
                timedelta(minutes=39),
                id="test that method works with a task_id from the task_list",
            ),
            pytest.param(
                task_node_as_artificial_endnode.id,
                build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1),
                timedelta(minutes=76),
                id="test that method works, when task_id is id of task_node_as_artificial_endnode",
            ),
            pytest.param(
                task_node_as_artificial_startnode.id,
                build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1),
                timedelta(minutes=0),
                id="test that method works, when task_id is id of task_node_as_artificial_startnode",
            ),
        ],
    )
    def test_if_duration_of_critical_path_before_task_is_calculated_correctly(
        self,
        task_id: TaskId,
        graph: TaskDependencyGraph,
        expected: timedelta,
    ):
        planned_duration_of_predecessor_tasks_on_critical_path = (
            graph.calculate_planned_duration_of_predecessor_tasks_on_critical_path(task_id)
        )
        assert planned_duration_of_predecessor_tasks_on_critical_path == expected

    @pytest.mark.parametrize(
        "task_id, graph",
        [
            pytest.param(
                uuid.uuid4(),
                build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1),
                id="test that method works, when task_id is invalid",
            )
        ],
    )
    def test_if_validation_error_is_raised_for_invalid_task_id(
        self,
        task_id: TaskId,
        graph: TaskDependencyGraph,
    ):
        with pytest.raises(ValueError):
            _ = graph.calculate_planned_duration_of_predecessor_tasks_on_critical_path(task_id)


class TestIfPlannedStartingTimeOfTaskIsCalculatedCorrectly:
    """
    With the following tests the method "calculate_planned_starting_time_of_task" is tested.
    Simple graph closed: With task_list_1 and dependency_list_1b the following graph is created and then used:
           1
         //  \          / = not critical path
         2   3          // = critical path
        \\  /
          4
    Complex graph: With task_list_2 and dependency_list_2 the following graph is created and then used:
          5
         /  \\
         6   7
         \   //
           8
          /  \\
         9   10
         \   //
           11
    """

    @pytest.mark.parametrize(
        "graph, task_id, expected",
        [
            pytest.param(
                build_simple_graph_closed(task_list_1, dependency_list_1b, starting_time_of_run_1),
                task_example_4.id,
                datetime(year=2024, month=3, day=12, hour=12, minute=35, tzinfo=timezone.utc),
            ),
            pytest.param(
                build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1),
                task_example_9.id,
                datetime(year=2024, month=3, day=12, hour=12, minute=49, tzinfo=timezone.utc),
            ),
        ],
    )
    def test_if_planned_starting_time_of_task_is_calculated_correctly(
        self,
        graph: TaskDependencyGraph,
        task_id: TaskId,
        expected: AwareDatetime,
    ):
        planned_starting_time_of_task = graph.calculate_planned_starting_time_of_task(task_id)
        assert planned_starting_time_of_task == expected


@pytest.mark.parametrize(
    "tdg, task_id, expected",
    [
        pytest.param(
            graph_bernd,
            task_B_with_fixed_start_2024_01_02.id,
            datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            id="B must not start before its own earliest start",
        ),
        pytest.param(
            graph_bernd,
            task_D.id,
            datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc) + task_B_with_fixed_start_2024_01_02.planned_duration,
            id="D must not start before B earliest start + B's duration",
        ),
        pytest.param(
            graph_carmen,
            task_B_with_fixed_start_2024_01_02.id,
            datetime(2024, 1, 2, 0, 1, 0, tzinfo=timezone.utc),
            id="B's start depends on the start of A+A's duration which is 1 minute after the earliest start of B",
        ),
        pytest.param(
            graph_carmen,
            task_D.id,
            datetime(2024, 1, 2, 0, 1, 0, tzinfo=timezone.utc) + task_B_with_fixed_start_2024_01_02.planned_duration,
            id="D's start is B's start + B duration",
        ),
        pytest.param(
            graph_carmen,
            task_C.id,
            datetime(2024, 1, 2, 0, 1, 0, tzinfo=timezone.utc),
            id="C's start is A's start + A duration",
        ),
        pytest.param(
            graph_daniel,
            task_G.id,
            graph_daniel._starting_time_of_run,  # pylint:disable=protected-access
            id="G's start is the start of the run",
        ),
        pytest.param(
            graph_daniel,
            task_L.id,
            graph_daniel._starting_time_of_run  # pylint:disable=protected-access
            + task_G.planned_duration
            + task_J.planned_duration
            + task_K.planned_duration,
            id="In Daniels case, L's start is only defined by the critical path",
        ),
        pytest.param(
            graph_emily,
            task_H_with_fixed_start_2024_01_02.id,
            task_H_with_fixed_start_2024_01_02.earliest_starttime,
            id="Emily: H start is only defined but its earliest start",
        ),
        pytest.param(
            graph_emily,
            task_I.id,
            task_H_with_fixed_start_2024_01_02.earliest_starttime + task_H_with_fixed_start_2024_01_02.planned_duration,
            id="Emily: I start is only defined by H's start and duration",
        ),
        pytest.param(
            graph_emily,
            task_I.id,
            task_H_with_fixed_start_2024_01_02.earliest_starttime + task_H_with_fixed_start_2024_01_02.planned_duration,
            id="Emily: the start of I is defined by the start of H",
        ),
        pytest.param(
            graph_emily,
            task_L.id,
            task_H_with_fixed_start_2024_01_02.earliest_starttime
            + task_H_with_fixed_start_2024_01_02.planned_duration
            + task_I.planned_duration,
            id="Emily: the L start depends mainly on the earliest start of H (which is not on the critical path)",
        ),
        pytest.param(
            graph_emily,
            task_J.id,
            graph_emily._starting_time_of_run + task_G.planned_duration,  # pylint:disable=protected-access
            id="Emily: the J start is independent of H",
        ),
        pytest.param(
            graph_emily,
            task_K.id,
            graph_emily._starting_time_of_run  # pylint:disable=protected-access
            + task_G.planned_duration
            + task_J.planned_duration,
            id="Emily: the K start is independent of H",
        ),
        pytest.param(
            graph_ferdinand,
            task_O.id,
            graph_ferdinand._starting_time_of_run  # pylint:disable=protected-access
            + task_M.planned_duration
            + task_N.planned_duration,
            id="Ferdinand: the O start is easy to calculate",
        ),
        pytest.param(
            graph_ferdinand,
            task_P.id,
            task_P.earliest_starttime,
            id="Ferdinand: the P start is easy to calculate",
        ),
        pytest.param(
            graph_ferdinand,
            task_R.id,
            task_Q.earliest_starttime + task_Q.planned_duration + task_X.planned_duration + task_Y.planned_duration,
            id="Ferdinand: R",
        ),
        pytest.param(
            graph_ferdinand,
            task_U.id,
            task_Q.earliest_starttime
            + task_Q.planned_duration
            + task_X.planned_duration
            + task_Y.planned_duration
            + task_R.planned_duration
            + task_S.planned_duration,
            id="Ferdinand: the U depends on Q",
        ),
        pytest.param(
            graph_ferdinand,
            task_W.id,
            task_Q.earliest_starttime
            + task_Q.planned_duration
            + task_X.planned_duration
            + task_Y.planned_duration
            + task_R.planned_duration
            + task_S.planned_duration
            + task_T.planned_duration
            + task_V.planned_duration,
            id="Ferdinand: the W depends on V",
        ),
    ],
)
def test_planned_starting_time_with_fixed_start(tdg: TaskDependencyGraph, task_id: TaskId, expected: AwareDatetime):
    actual = tdg.calculate_planned_starting_time_of_task(task_id)
    assert actual == expected


def test_planned_starting_time_is_calculated_after_modifying_a_graph():
    """
    make sure that the weights are re-calculated after adding a node or an edge
    """
    graph_emily_copy = copy.deepcopy(graph_emily)
    new_task = TaskNode(
        id=TaskId(uuid.uuid4()),
        external_id="before F",
        name="before F",
        planned_duration=timedelta(minutes=7),
        earliest_starttime=datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc),
    )
    graph_emily_copy.add_task(new_task)
    graph_emily_copy.add_edge(
        TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=new_task.id, task_successor=task_G.id)
    )
    assert graph_emily_copy.calculate_planned_starting_time_of_task(task_G.id) == datetime(
        2024, 1, 10, 0, 7, 0, tzinfo=timezone.utc
    )
    assert graph_emily_copy.calculate_planned_starting_time_of_task(task_I.id) == datetime(
        2024, 1, 10, 0, 18, 0, tzinfo=timezone.utc
    )


def test_extract_subgraph_only_accepts_milestones():
    full_graph = copy.deepcopy(graph_ferdinand)
    with pytest.raises(ValueError) as raised_value_error:
        _ = full_graph.extract_sub_graph(task_S.id, task_W.id)
    assert "not a milestone" in str(raised_value_error.value)


def test_extract_subgraph_only_accepts_known_tasks():
    full_graph = copy.deepcopy(graph_ferdinand)
    with pytest.raises(ValueError) as raised_value_error:
        _ = full_graph.extract_sub_graph(TaskId(uuid.uuid4()), task_W.id)
    assert "(start) does not exist in the graph" in str(raised_value_error.value)


def test_extract_subgraph_if_end_is_before_start():
    full_graph = copy.deepcopy(graph_ferdinand_with_milestones)
    with pytest.raises(ValueError) as raised_value_error:
        _ = full_graph.extract_sub_graph(task_W_milestone.id, task_S_milestone.id)
    assert "There is no path between" in str(raised_value_error.value)


def test_extract_subgraph():
    full_graph = copy.deepcopy(graph_ferdinand_with_milestones)
    actual = full_graph.extract_sub_graph(task_S_milestone.id, task_W_milestone.id)
    assert isinstance(actual, TaskDependencyGraph)
    # pylint:disable=protected-access
    assert actual._graph.has_edge(task_S_milestone.id, task_T.id)
    assert actual._graph.has_edge(task_S_milestone.id, task_U.id)
    # an... the other will exist. I'm sure, because:
    assert nx.has_path(actual._graph, task_S_milestone.id, task_W_milestone.id)
    assert all(actual._graph.nodes[node]["domain_model"] is not None for node in actual._graph.nodes)


class TestIfListIsCorrectlySortedByStartingTime:
    """
    Complex graph made from unsorted task_list and with different starting time: With task_list_2b and
    dependency_list_2 the following graph is created and then used:
          5                 the run starts at: year=2024, month=3, day=12, hour=5, minute=0
         /  \\
         6   7
         \   //
           8                task example 8 starts at: year=2024, month=3, day=12, hour=5, minute=35
          /  \\
         9   10
         \   //
           11
    Another complex graph with unsorted task_list and different starting time: With task_list_2b and
    dependency_list_3 the following graph is created and then used:
            5               the run starts at: year=2024, month=3, day=12, hour=5, minute=0
           /  \
          7    6
        /     /
       8     /              task example 8 starts at: year=2024, month=3, day=12, hour=5, minute=35
       \   /
        9
       /   \
    10     11

    """

    @pytest.mark.parametrize(
        "graph, expected_0, expected_1, expected_2",
        [
            pytest.param(
                build_complex_graph_made_from_unsorted_task_list_and_with_different_starting_time(
                    task_list_2, dependency_list_2, starting_time_of_run_2
                ),
                datetime(year=2024, month=3, day=12, hour=5, minute=35, tzinfo=timezone.utc),
                task_example_8,
                task_example_11,
            ),
            pytest.param(
                build_another_complex_graph_with_unsorted_task_list_and_different_starting_time(
                    task_list_2b, dependency_list_3, starting_time_of_run_2
                ),
                datetime(year=2024, month=3, day=12, hour=5, minute=35, tzinfo=timezone.utc),
                task_example_8,
                task_example_11,
            ),
        ],
    )
    def test_if_list_of_task_node_copies_is_created_correctly(
        self,
        graph: TaskDependencyGraph,
        expected_0: AwareDatetime,
        expected_1: TaskNode,
        expected_2: TaskNode,
    ):
        new_task_list = graph.create_list_of_task_node_copies_with_planned_starting_time()
        assert (
            new_task_list[3].planned_starting_time == expected_0
        ), "The planned starting time hasn't been calculated correctly or the list hasn't been sorted correctly."
        assert (
            new_task_list[3].id == expected_1.id
        ), "The planned starting time hasn't been calculated correctly or the list hasn't been sorted correctly."
        assert (
            new_task_list[6].id == expected_2.id
        ), "The planned starting time hasn't been calculated correctly or the list hasn't been sorted correctly."

    def test_labels(self):
        tdg = build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1)
        actual = tdg.labels()
        assert len(actual) == len(task_list_2) + 2
        assert "START" in actual.values()
        assert "END" in actual.values()

    def test_deep_copy(self):
        tdg = build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1)
        digraph = tdg.get_digraph_copy()
        assert digraph is not tdg._graph  # pylint:disable=protected-access
        for ext_node, int_node in zip(digraph.nodes, tdg._graph.nodes, strict=True):  # pylint:disable=protected-access
            assert ext_node == int_node
            assert ext_node is not int_node
        for ext_edge, int_edge in zip(digraph.edges, tdg._graph.edges, strict=True):  # pylint:disable=protected-access
            assert ext_edge == int_edge
            assert ext_edge is not int_edge
