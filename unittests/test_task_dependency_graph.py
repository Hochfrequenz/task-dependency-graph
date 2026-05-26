import copy
import uuid
from datetime import datetime, timedelta, timezone

import networkx as nx  # type: ignore[import-untyped]
import pytest
import taskdependencygraph.models as tdg_models
from pydantic import AwareDatetime, ValidationError

from taskdependencygraph.models.graph_definition_validation import (
    ValidationCode,
)
from taskdependencygraph.models.ids import TaskDependencyId, TaskId
from taskdependencygraph.models.mermaid_gantt_config import MermaidGanttConfig
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge
from taskdependencygraph.models.task_execution_status import TaskExecutionStatus
from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.models.task_node_as_artificial_endnode import (
    ID_OF_ARTIFICIAL_ENDNODE,
    task_node_as_artificial_endnode,
)
from taskdependencygraph.models.task_node_as_artificial_startnode import (
    ID_OF_ARTIFICIAL_STARTNODE,
    task_node_as_artificial_startnode,
)
from taskdependencygraph.task_dependency_graph import TaskDependencyGraph

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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
def test_planned_starting_time_with_fixed_start(
    tdg: TaskDependencyGraph, task_id: TaskId, expected: AwareDatetime
) -> None:
    actual = tdg.calculate_planned_starting_time_of_task(task_id)
    assert actual == expected


def test_planned_starting_time_is_calculated_after_modifying_a_graph() -> None:
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


def test_extract_subgraph_only_accepts_milestones() -> None:
    full_graph = copy.deepcopy(graph_ferdinand)
    with pytest.raises(ValueError) as raised_value_error:
        _ = full_graph.extract_sub_graph(task_S.id, task_W.id)
    assert "not a milestone" in str(raised_value_error.value)


def test_extract_subgraph_only_accepts_known_tasks() -> None:
    full_graph = copy.deepcopy(graph_ferdinand)
    with pytest.raises(ValueError) as raised_value_error:
        _ = full_graph.extract_sub_graph(TaskId(uuid.uuid4()), task_W.id)
    assert "(start) does not exist in the graph" in str(raised_value_error.value)


def test_extract_subgraph_if_end_is_before_start() -> None:
    full_graph = copy.deepcopy(graph_ferdinand_with_milestones)
    with pytest.raises(ValueError) as raised_value_error:
        _ = full_graph.extract_sub_graph(task_W_milestone.id, task_S_milestone.id)
    assert "There is no path between" in str(raised_value_error.value)


def test_extract_subgraph() -> None:
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
    ) -> None:
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

    def test_labels(self) -> None:
        tdg = build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1)
        actual = tdg.labels()
        assert len(actual) == len(task_list_2) + 2
        assert "START" in actual.values()
        assert "END" in actual.values()

    def test_deep_copy(self) -> None:
        tdg = build_complex_graph(task_list_2, dependency_list_2, starting_time_of_run_1)
        digraph = tdg.get_digraph_copy()
        assert digraph is not tdg._graph  # pylint:disable=protected-access
        for ext_node, int_node in zip(digraph.nodes, tdg._graph.nodes, strict=True):  # pylint:disable=protected-access
            assert ext_node == int_node
            assert ext_node is not int_node
        for ext_edge, int_edge in zip(digraph.edges, tdg._graph.edges, strict=True):  # pylint:disable=protected-access
            assert ext_edge == int_edge
            assert ext_edge is not int_edge


# ---------------------------------------------------------------------------
# Issue #84 – planned finish time APIs
# ---------------------------------------------------------------------------

_T0 = datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc)


def _node(
    external_id: str,
    duration_minutes: int,
    *,
    milestone: bool = False,
    earliest_start: datetime | None = None,
    phase: str | None = None,
) -> TaskNode:
    return TaskNode(
        id=TaskId(uuid.uuid4()),
        external_id=external_id,
        name=external_id,
        planned_duration=timedelta(minutes=duration_minutes),
        is_milestone=milestone,
        earliest_starttime=earliest_start,
        phase=phase,
    )


def _edge(pred: TaskNode, succ: TaskNode) -> TaskDependencyEdge:
    return TaskDependencyEdge(id=TaskDependencyId(uuid.uuid4()), task_predecessor=pred.id, task_successor=succ.id)


class TestPlannedFinishTimeOfTask:
    """Tests for calculate_planned_finish_time_of_task (issue #84)."""

    def test_single_task_finish_time(self) -> None:
        """A single task finishes at start + duration."""
        task = _node("A", 30)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        expected = _T0 + timedelta(minutes=30)
        assert tdg.calculate_planned_finish_time_of_task(task.id) == expected

    def test_zero_duration_milestone_finish_equals_start(self) -> None:
        """A zero-duration milestone finishes exactly at its planned start time."""
        ms = _node("MS", 0, milestone=True)
        tdg = TaskDependencyGraph(task_list=[ms], dependency_list=[], starting_time_of_run=_T0)
        assert tdg.calculate_planned_finish_time_of_task(ms.id) == _T0

    def test_task_on_longer_parallel_path(self) -> None:
        """The task on the longer parallel path finishes after the task on the shorter path."""
        short = _node("short", 5)
        long_ = _node("long", 20)
        join = _node("join", 10)
        tdg = TaskDependencyGraph(
            task_list=[short, long_, join],
            dependency_list=[_edge(short, join), _edge(long_, join)],
            starting_time_of_run=_T0,
        )
        # short finishes at T0+5, long finishes at T0+20
        assert tdg.calculate_planned_finish_time_of_task(short.id) == _T0 + timedelta(minutes=5)
        assert tdg.calculate_planned_finish_time_of_task(long_.id) == _T0 + timedelta(minutes=20)
        # join starts after the longer path: T0+20, finishes T0+30
        assert tdg.calculate_planned_finish_time_of_task(join.id) == _T0 + timedelta(minutes=30)

    def test_earliest_starttime_delays_finish(self) -> None:
        """A task with earliest_starttime finishes at earliest_starttime + duration."""
        early = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)  # 2h after T0
        task = _node("delayed", 15, earliest_start=early)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        assert tdg.calculate_planned_finish_time_of_task(task.id) == early + timedelta(minutes=15)

    def test_unknown_task_id_raises_value_error(self) -> None:
        """An unrecognised task ID must raise ValueError."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        with pytest.raises(ValueError):
            tdg.calculate_planned_finish_time_of_task(TaskId(uuid.uuid4()))

    def test_artificial_node_id_raises_value_error(self) -> None:
        """Artificial node IDs must be rejected — they are not part of the public API."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        with pytest.raises(ValueError):
            tdg.calculate_planned_finish_time_of_task(task_node_as_artificial_endnode.id)
        with pytest.raises(ValueError):
            tdg.calculate_planned_finish_time_of_task(task_node_as_artificial_startnode.id)


class TestPlannedFinishTimeOfGraph:
    """Tests for calculate_planned_finish_time_of_graph (issue #84)."""

    def test_graph_finish_single_task(self) -> None:
        """Graph with one task finishes at T0 + task duration."""
        task = _node("A", 45)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        assert tdg.calculate_planned_finish_time_of_graph() == _T0 + timedelta(minutes=45)

    def test_graph_finish_equals_artificial_endnode_start(self) -> None:
        """Graph finish must equal calculate_planned_starting_time_of_task(ID_OF_ARTIFICIAL_ENDNODE)."""
        a = _node("A", 10)
        b = _node("B", 25)
        tdg = TaskDependencyGraph(task_list=[a, b], dependency_list=[_edge(a, b)], starting_time_of_run=_T0)
        assert tdg.calculate_planned_finish_time_of_graph() == tdg.calculate_planned_starting_time_of_task(
            ID_OF_ARTIFICIAL_ENDNODE
        )

    def test_graph_finish_parallel_paths_takes_longer(self) -> None:
        """Graph finish is determined by the longest path."""
        short = _node("short", 5)
        long_ = _node("long", 40)
        tdg = TaskDependencyGraph(task_list=[short, long_], dependency_list=[], starting_time_of_run=_T0)
        assert tdg.calculate_planned_finish_time_of_graph() == _T0 + timedelta(minutes=40)


# ---------------------------------------------------------------------------
# Issue #85 – ordered critical path data
# ---------------------------------------------------------------------------


class TestGetCriticalPathTaskIds:
    """Tests for get_critical_path_task_ids (issue #85)."""

    def test_linear_graph_all_tasks_on_critical_path(self) -> None:
        """In a linear chain every task is on the critical path, in order."""
        a = _node("A", 10)
        b = _node("B", 20)
        c = _node("C", 5)
        tdg = TaskDependencyGraph(
            task_list=[a, b, c],
            dependency_list=[_edge(a, b), _edge(b, c)],
            starting_time_of_run=_T0,
        )
        ids = tdg.get_critical_path_task_ids()
        assert ids == [a.id, b.id, c.id]

    def test_parallel_paths_longer_path_wins(self) -> None:
        """When two paths diverge, the longer one is on the critical path."""
        start = _node("start", 5)
        short = _node("short", 3)
        long_ = _node("long", 30)
        end = _node("end", 5)
        tdg = TaskDependencyGraph(
            task_list=[start, short, long_, end],
            dependency_list=[_edge(start, short), _edge(start, long_), _edge(short, end), _edge(long_, end)],
            starting_time_of_run=_T0,
        )
        ids = tdg.get_critical_path_task_ids()
        assert start.id in ids
        assert long_.id in ids
        assert end.id in ids
        assert short.id not in ids

    def test_milestone_on_critical_path_is_included(self) -> None:
        """A zero-duration milestone that lies on the critical path appears in the result."""
        a = _node("A", 20)
        ms = _node("MS", 0, milestone=True)
        b = _node("B", 10)
        tdg = TaskDependencyGraph(
            task_list=[a, ms, b],
            dependency_list=[_edge(a, ms), _edge(ms, b)],
            starting_time_of_run=_T0,
        )
        ids = tdg.get_critical_path_task_ids()
        assert ms.id in ids

    def test_default_excludes_artificial_nodes(self) -> None:
        """Artificial start/end nodes must not appear by default."""
        a = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[a], dependency_list=[], starting_time_of_run=_T0)
        ids = tdg.get_critical_path_task_ids()
        assert ID_OF_ARTIFICIAL_STARTNODE not in ids
        assert ID_OF_ARTIFICIAL_ENDNODE not in ids

    def test_include_artificial_nodes_flag(self) -> None:
        """Passing include_artificial_nodes=True makes artificial nodes appear at the boundaries."""
        a = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[a], dependency_list=[], starting_time_of_run=_T0)
        ids = tdg.get_critical_path_task_ids(include_artificial_nodes=True)
        assert ids[0] == ID_OF_ARTIFICIAL_STARTNODE
        assert ids[-1] == ID_OF_ARTIFICIAL_ENDNODE

    def test_tie_behavior_is_deterministic(self) -> None:
        """Equal-length parallel paths produce a deterministic (NetworkX-ordered) result.

        NetworkX picks the path whose first differing node was inserted into the graph first,
        which is `a` here. Two calls on the same graph must return the same list.
        """
        a = _node("A", 10)
        b = _node("B", 10)
        tdg = TaskDependencyGraph(task_list=[a, b], dependency_list=[], starting_time_of_run=_T0)
        ids1 = tdg.get_critical_path_task_ids()
        ids2 = tdg.get_critical_path_task_ids()
        assert ids1 == ids2
        assert ids1 == [a.id]  # first-inserted node wins the tie

    def test_empty_task_list_returns_empty_path(self) -> None:
        """A graph with no real tasks returns an empty critical path."""
        tdg = TaskDependencyGraph(task_list=[], dependency_list=[], starting_time_of_run=_T0)
        assert tdg.get_critical_path_task_ids() == []

    def test_earliest_starttime_stretches_onto_critical_path(self) -> None:
        """A task delayed by earliest_starttime gets a stretched edge weight, pushing it onto the path."""
        a = _node("A", 10)  # finishes at T0+10min, path weight 10
        early = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)  # T0 + 60min
        b = _node("B", 10, earliest_start=early)  # edge stretched to 60min, path weight 70
        tdg = TaskDependencyGraph(task_list=[a, b], dependency_list=[], starting_time_of_run=_T0)
        ids = tdg.get_critical_path_task_ids()
        assert b.id in ids
        assert a.id not in ids


class TestGetCriticalPathTasks:
    """Tests for get_critical_path_tasks (issue #85)."""

    def test_returns_task_nodes_in_order(self) -> None:
        """get_critical_path_tasks returns TaskNode objects matching the ordered IDs."""
        a = _node("A", 5)
        b = _node("B", 15)
        tdg = TaskDependencyGraph(
            task_list=[a, b],
            dependency_list=[_edge(a, b)],
            starting_time_of_run=_T0,
        )
        tasks = tdg.get_critical_path_tasks()
        assert [t.id for t in tasks] == tdg.get_critical_path_task_ids()

    def test_default_excludes_artificial_task_nodes(self) -> None:
        """Artificial TaskNode objects must not appear by default."""
        a = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[a], dependency_list=[], starting_time_of_run=_T0)
        tasks = tdg.get_critical_path_tasks()
        task_ids = [t.id for t in tasks]
        assert ID_OF_ARTIFICIAL_STARTNODE not in task_ids
        assert ID_OF_ARTIFICIAL_ENDNODE not in task_ids

    def test_include_artificial_nodes_flag(self) -> None:
        """With include_artificial_nodes=True the first and last nodes are the artificial ones."""
        a = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[a], dependency_list=[], starting_time_of_run=_T0)
        tasks = tdg.get_critical_path_tasks(include_artificial_nodes=True)
        assert tasks[0].id == ID_OF_ARTIFICIAL_STARTNODE
        assert tasks[-1].id == ID_OF_ARTIFICIAL_ENDNODE

    def test_parallel_paths_longer_path_wins(self) -> None:
        """TaskNode objects on the longer parallel path are returned, not the shorter one."""
        short = _node("short", 5)
        long_ = _node("long", 30)
        end = _node("end", 5)
        tdg = TaskDependencyGraph(
            task_list=[short, long_, end],
            dependency_list=[_edge(short, end), _edge(long_, end)],
            starting_time_of_run=_T0,
        )
        tasks = tdg.get_critical_path_tasks()
        task_ids = [t.id for t in tasks]
        assert long_.id in task_ids
        assert end.id in task_ids
        assert short.id not in task_ids


# ---------------------------------------------------------------------------
# Issue #86 – structured schedule report
# ---------------------------------------------------------------------------


class TestScheduleReport:
    """Tests for create_schedule_report (issue #86)."""

    def test_report_contains_all_non_artificial_tasks(self) -> None:
        """All real tasks appear in the report and no artificial nodes appear by default."""
        a = _node("A", 10)
        b = _node("B", 20)
        tdg = TaskDependencyGraph(
            task_list=[a, b],
            dependency_list=[_edge(a, b)],
            starting_time_of_run=_T0,
        )
        report = tdg.create_schedule_report()
        entry_ids = {e.task_id for e in report.entries}
        assert entry_ids == {a.id, b.id}
        assert ID_OF_ARTIFICIAL_STARTNODE not in entry_ids
        assert ID_OF_ARTIFICIAL_ENDNODE not in entry_ids

    def test_report_planned_start_finish_correct(self) -> None:
        """Each entry has the correct planned_start and planned_finish."""
        a = _node("A", 10)
        b = _node("B", 20)
        tdg = TaskDependencyGraph(
            task_list=[a, b],
            dependency_list=[_edge(a, b)],
            starting_time_of_run=_T0,
        )
        report = tdg.create_schedule_report()
        by_id = {e.task_id: e for e in report.entries}
        assert by_id[a.id].planned_start == _T0
        assert by_id[a.id].planned_finish == _T0 + timedelta(minutes=10)
        assert by_id[b.id].planned_start == _T0 + timedelta(minutes=10)
        assert by_id[b.id].planned_finish == _T0 + timedelta(minutes=30)

    def test_report_critical_path_flags(self) -> None:
        """is_on_critical_path flags match get_critical_path_task_ids output."""
        short = _node("short", 5)
        long_ = _node("long", 30)
        end = _node("end", 5)
        tdg = TaskDependencyGraph(
            task_list=[short, long_, end],
            dependency_list=[_edge(short, end), _edge(long_, end)],
            starting_time_of_run=_T0,
        )
        report = tdg.create_schedule_report()
        cp_ids = set(tdg.get_critical_path_task_ids())
        for entry in report.entries:
            assert entry.is_on_critical_path == (entry.task_id in cp_ids)

    def test_report_predecessor_successor_ids_exclude_artificial(self) -> None:
        """Predecessor and successor lists never contain artificial node IDs by default."""
        a = _node("A", 10)
        b = _node("B", 5)
        c = _node("C", 15)
        tdg = TaskDependencyGraph(
            task_list=[a, b, c],
            dependency_list=[_edge(a, c), _edge(b, c)],
            starting_time_of_run=_T0,
        )
        report = tdg.create_schedule_report()
        for entry in report.entries:
            assert ID_OF_ARTIFICIAL_STARTNODE not in entry.predecessor_task_ids
            assert ID_OF_ARTIFICIAL_ENDNODE not in entry.predecessor_task_ids
            assert ID_OF_ARTIFICIAL_STARTNODE not in entry.successor_task_ids
            assert ID_OF_ARTIFICIAL_ENDNODE not in entry.successor_task_ids

    def test_report_predecessor_and_successor_ids_correct(self) -> None:
        """Each entry's predecessor/successor lists contain the correct task IDs."""
        a = _node("A", 10)
        b = _node("B", 5)
        c = _node("C", 15)
        tdg = TaskDependencyGraph(
            task_list=[a, b, c],
            dependency_list=[_edge(a, c), _edge(b, c)],
            starting_time_of_run=_T0,
        )
        report = tdg.create_schedule_report()
        by_id = {e.task_id: e for e in report.entries}
        assert by_id[a.id].predecessor_task_ids == []
        assert by_id[b.id].predecessor_task_ids == []
        assert set(by_id[c.id].predecessor_task_ids) == {a.id, b.id}
        assert by_id[a.id].successor_task_ids == [c.id]
        assert by_id[b.id].successor_task_ids == [c.id]
        assert by_id[c.id].successor_task_ids == []

    def test_report_entry_ordering(self) -> None:
        """Entries are sorted by planned_start, then external_id, then name."""
        a = _node("A", 10)
        b = _node("B", 10)
        c = _node("C", 5)
        tdg = TaskDependencyGraph(
            task_list=[a, b, c],
            dependency_list=[_edge(a, c), _edge(b, c)],
            starting_time_of_run=_T0,
        )
        report = tdg.create_schedule_report()
        starts = [e.planned_start for e in report.entries]
        assert starts == sorted(starts)
        # A and B both start at T0; sorted alphabetically by external_id
        assert report.entries[0].external_id == "A"
        assert report.entries[1].external_id == "B"

    def test_report_predecessor_ordering_is_deterministic(self) -> None:
        """Predecessor list is sorted by planned_start, then external_id, then name."""
        pred_a = _node("PA", 5)
        pred_b = _node("PB", 10)
        succ = _node("S", 5)
        tdg = TaskDependencyGraph(
            task_list=[pred_a, pred_b, succ],
            dependency_list=[_edge(pred_a, succ), _edge(pred_b, succ)],
            starting_time_of_run=_T0,
        )
        report = tdg.create_schedule_report()
        by_id = {e.task_id: e for e in report.entries}
        # Both predecessors start at T0; sorted alphabetically: PA < PB
        assert by_id[succ.id].predecessor_task_ids == [pred_a.id, pred_b.id]

    def test_report_graph_level_fields(self) -> None:
        """graph_start, graph_finish, total_duration, and critical_path_task_ids are correct."""
        a = _node("A", 20)
        b = _node("B", 10)
        tdg = TaskDependencyGraph(
            task_list=[a, b],
            dependency_list=[_edge(a, b)],
            starting_time_of_run=_T0,
        )
        report = tdg.create_schedule_report()
        assert report.graph_start == _T0
        assert report.graph_finish == _T0 + timedelta(minutes=30)
        assert report.total_duration == timedelta(minutes=30)
        assert report.critical_path_task_ids == tdg.get_critical_path_task_ids()

    def test_include_artificial_nodes_flag(self) -> None:
        """With include_artificial_nodes=True artificial nodes appear in entries and boundary ID lists."""
        a = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[a], dependency_list=[], starting_time_of_run=_T0)
        report = tdg.create_schedule_report(include_artificial_nodes=True)
        entry_ids = {e.task_id for e in report.entries}
        assert ID_OF_ARTIFICIAL_STARTNODE in entry_ids
        assert ID_OF_ARTIFICIAL_ENDNODE in entry_ids
        # The real task's predecessor list should include the artificial start
        by_id = {e.task_id: e for e in report.entries}
        assert ID_OF_ARTIFICIAL_STARTNODE in by_id[a.id].predecessor_task_ids
        assert ID_OF_ARTIFICIAL_ENDNODE in by_id[a.id].successor_task_ids

    def test_earliest_starttime_respected_in_report(self) -> None:
        """A task with earliest_starttime has its delayed planned_start and planned_finish in the report."""
        early = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)  # T0 + 2h
        a = _node("A", 30, earliest_start=early)
        tdg = TaskDependencyGraph(task_list=[a], dependency_list=[], starting_time_of_run=_T0)
        report = tdg.create_schedule_report()
        entry = report.entries[0]
        assert entry.planned_start == early
        assert entry.planned_finish == early + timedelta(minutes=30)


# ---------------------------------------------------------------------------
# Issue #87 – pre-construction graph definition validation
# ---------------------------------------------------------------------------


class TestValidateDefinition:
    """Tests for TaskDependencyGraph.validate_definition (issue #87)."""

    def test_valid_definition_has_no_findings(self) -> None:
        """A well-formed graph definition returns is_valid=True with an empty findings tuple."""
        a = _node("A", 10)
        b = _node("B", 20)
        result = TaskDependencyGraph.validate_definition([a, b], [_edge(a, b)])
        assert result.is_valid is True
        assert result.findings == ()

    def test_duplicate_task_id_is_reported(self) -> None:
        """Two TaskNode objects sharing the same id produce a DUPLICATE_TASK_ID finding."""
        a = _node("A", 10)
        a_dup = a.model_copy(update={"external_id": "A2"})  # same id, different external_id
        result = TaskDependencyGraph.validate_definition([a, a_dup], [])
        assert result.is_valid is False
        assert any(f.code == ValidationCode.DUPLICATE_TASK_ID for f in result.findings)

    def test_duplicate_external_id_is_reported(self) -> None:
        """Two tasks with the same external_id produce a DUPLICATE_EXTERNAL_ID finding."""
        a = _node("A", 10)
        b = _node("A", 20)  # same external_id "A"
        result = TaskDependencyGraph.validate_definition([a, b], [])
        assert result.is_valid is False
        assert any(f.code == ValidationCode.DUPLICATE_EXTERNAL_ID for f in result.findings)

    def test_missing_predecessor_is_reported(self) -> None:
        """An edge whose predecessor is absent from task_list produces MISSING_EDGE_ENDPOINT."""
        a = _node("A", 10)
        ghost = _node("ghost", 5)
        result = TaskDependencyGraph.validate_definition([a], [_edge(ghost, a)])
        assert result.is_valid is False
        assert any(f.code == ValidationCode.MISSING_EDGE_ENDPOINT for f in result.findings)

    def test_missing_successor_is_reported(self) -> None:
        """An edge whose successor is absent from task_list produces MISSING_EDGE_ENDPOINT."""
        a = _node("A", 10)
        ghost = _node("ghost", 5)
        result = TaskDependencyGraph.validate_definition([a], [_edge(a, ghost)])
        assert result.is_valid is False
        assert any(f.code == ValidationCode.MISSING_EDGE_ENDPOINT for f in result.findings)

    def test_duplicate_dependency_id_is_reported(self) -> None:
        """Two edges sharing the same id produce a DUPLICATE_DEPENDENCY_ID finding."""
        a = _node("A", 10)
        b = _node("B", 10)
        c = _node("C", 10)
        e1 = _edge(a, b)
        e2 = e1.model_copy(update={"task_predecessor": b.id, "task_successor": c.id})
        result = TaskDependencyGraph.validate_definition([a, b, c], [e1, e2])
        assert result.is_valid is False
        assert any(f.code == ValidationCode.DUPLICATE_DEPENDENCY_ID for f in result.findings)

    def test_duplicate_edge_pair_is_reported(self) -> None:
        """Two edges with the same predecessor/successor pair produce DUPLICATE_EDGE_PAIR."""
        a = _node("A", 10)
        b = _node("B", 10)
        result = TaskDependencyGraph.validate_definition([a, b], [_edge(a, b), _edge(a, b)])
        assert result.is_valid is False
        assert any(f.code == ValidationCode.DUPLICATE_EDGE_PAIR for f in result.findings)

    def test_cycle_is_reported(self) -> None:
        """A dependency cycle produces a CYCLE finding."""
        a = _node("A", 10)
        b = _node("B", 10)
        result = TaskDependencyGraph.validate_definition([a, b], [_edge(a, b), _edge(b, a)])
        assert result.is_valid is False
        assert any(f.code == ValidationCode.CYCLE for f in result.findings)

    def test_invalid_milestone_duration_is_reported(self) -> None:
        """A milestone with non-zero planned_duration produces INVALID_MILESTONE_DURATION."""
        ms = _node("MS", 10, milestone=True)
        result = TaskDependencyGraph.validate_definition([ms], [])
        assert result.is_valid is False
        assert any(f.code == ValidationCode.INVALID_MILESTONE_DURATION for f in result.findings)

    def test_multiple_errors_returned_together(self) -> None:
        """All independent findings are collected in a single call rather than stopping at the first."""
        a = _node("A", 10)
        a_dup = a.model_copy(update={"external_id": "A2"})  # DUPLICATE_TASK_ID
        ms = _node("MS", 5, milestone=True)  # INVALID_MILESTONE_DURATION
        ghost = _node("ghost", 5)
        result = TaskDependencyGraph.validate_definition([a, a_dup, ms], [_edge(a, ghost)])
        assert result.is_valid is False
        codes = {f.code for f in result.findings}
        assert ValidationCode.DUPLICATE_TASK_ID in codes
        assert ValidationCode.INVALID_MILESTONE_DURATION in codes
        assert ValidationCode.MISSING_EDGE_ENDPOINT in codes

    def test_missing_endpoint_and_cycle_both_reported(self) -> None:
        """Missing endpoints and a cycle are reported together in one result."""
        a = _node("A", 10)
        b = _node("B", 10)
        ghost = _node("ghost", 5)
        result = TaskDependencyGraph.validate_definition([a, b], [_edge(a, b), _edge(b, a), _edge(a, ghost)])
        assert result.is_valid is False
        codes = {f.code for f in result.findings}
        assert ValidationCode.CYCLE in codes
        assert ValidationCode.MISSING_EDGE_ENDPOINT in codes

    def test_three_tasks_with_same_external_id_produce_one_finding(self) -> None:
        """Three tasks sharing the same external_id produce exactly one DUPLICATE_EXTERNAL_ID finding."""
        a = _node("EXT", 10)
        b = _node("EXT", 20)
        c = _node("EXT", 30)
        result = TaskDependencyGraph.validate_definition([a, b, c], [])
        assert result.is_valid is False
        dup_findings = [f for f in result.findings if f.code == ValidationCode.DUPLICATE_EXTERNAL_ID]
        assert len(dup_findings) == 1


# ---------------------------------------------------------------------------
# Issue #88 – total slack per task
# ---------------------------------------------------------------------------


class TestTotalSlack:
    """Tests for calculate_total_slack_of_task (issue #88)."""

    def test_linear_graph_all_tasks_have_zero_slack(self) -> None:
        """In a linear chain every task is on the critical path and has zero slack."""
        a = _node("A", 10)
        b = _node("B", 20)
        c = _node("C", 5)
        tdg = TaskDependencyGraph(
            task_list=[a, b, c],
            dependency_list=[_edge(a, b), _edge(b, c)],
            starting_time_of_run=_T0,
        )
        assert tdg.calculate_total_slack_of_task(a.id) == timedelta(0)
        assert tdg.calculate_total_slack_of_task(b.id) == timedelta(0)
        assert tdg.calculate_total_slack_of_task(c.id) == timedelta(0)

    def test_parallel_paths_shorter_has_positive_slack(self) -> None:
        """The task on the shorter parallel path has positive total slack."""
        short = _node("short", 5)
        long_ = _node("long", 30)
        end = _node("end", 5)
        tdg = TaskDependencyGraph(
            task_list=[short, long_, end],
            dependency_list=[_edge(short, end), _edge(long_, end)],
            starting_time_of_run=_T0,
        )
        # critical path: long (30) + end (5) = 35 min total
        # short finishes at T0+5, end's LS = 30, so short has slack = 30 - 5 = 25 min
        assert tdg.calculate_total_slack_of_task(long_.id) == timedelta(0)
        assert tdg.calculate_total_slack_of_task(end.id) == timedelta(0)
        assert tdg.calculate_total_slack_of_task(short.id) == timedelta(minutes=25)

    def test_equal_length_parallel_paths_both_have_zero_slack(self) -> None:
        """Two independent tasks of equal duration both lie on a longest path and have zero slack.

        Note: NetworkX's dag_longest_path picks only one path when lengths are tied (insertion
        order wins), so is_on_critical_path may return False for task B even though its total
        slack is zero. This test documents that deliberate behaviour: zero slack and
        is_on_critical_path are not equivalent when paths are tied.
        """
        a = _node("A", 10)
        b = _node("B", 10)
        tdg = TaskDependencyGraph(task_list=[a, b], dependency_list=[], starting_time_of_run=_T0)
        assert tdg.calculate_total_slack_of_task(a.id) == timedelta(0)
        assert tdg.calculate_total_slack_of_task(b.id) == timedelta(0)
        # Confirm the deliberate divergence: B has zero slack but is not on the NetworkX critical path
        assert tdg.is_on_critical_path(b.id) is False

    def test_milestone_on_critical_path_has_zero_slack(self) -> None:
        """A zero-duration milestone on the critical path has zero total slack."""
        a = _node("A", 20)
        ms = _node("MS", 0, milestone=True)
        b = _node("B", 10)
        tdg = TaskDependencyGraph(
            task_list=[a, ms, b],
            dependency_list=[_edge(a, ms), _edge(ms, b)],
            starting_time_of_run=_T0,
        )
        assert tdg.calculate_total_slack_of_task(ms.id) == timedelta(0)

    def test_milestone_off_critical_path_has_positive_slack(self) -> None:
        """A zero-duration milestone on the shorter parallel path has positive total slack."""
        long_ = _node("long", 30)
        ms = _node("MS", 0, milestone=True)
        short = _node("short", 5)
        # ms → short is the short path; long is independent; graph finish = 30 min
        tdg = TaskDependencyGraph(
            task_list=[long_, ms, short],
            dependency_list=[_edge(ms, short)],
            starting_time_of_run=_T0,
        )
        # short LS = 30 - 5 = 25; ms LF = LS(short) = 25; ms LS = 25 - 0 = 25
        assert tdg.calculate_total_slack_of_task(ms.id) == timedelta(minutes=25)
        assert tdg.calculate_total_slack_of_task(short.id) == timedelta(minutes=25)

    def test_earliest_starttime_wait_gives_slack_to_predecessor(self) -> None:
        """When a successor has earliest_starttime, its predecessor gains slack from the wait."""
        early = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)  # T0 + 60 min
        a = _node("A", 10)
        b = _node("B", 20, earliest_start=early)
        tdg = TaskDependencyGraph(task_list=[a, b], dependency_list=[_edge(a, b)], starting_time_of_run=_T0)
        # A finishes at T0+10, B waits until T0+60, finishes at T0+80
        # LS(B) = 80 - 20 = 60 → LF(A) = 60 → LS(A) = 60 - 10 = 50
        assert tdg.calculate_total_slack_of_task(a.id) == timedelta(minutes=50)
        assert tdg.calculate_total_slack_of_task(b.id) == timedelta(0)

    def test_unknown_task_id_raises_value_error(self) -> None:
        """An unrecognised task ID raises ValueError."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        with pytest.raises(ValueError):
            tdg.calculate_total_slack_of_task(TaskId(uuid.uuid4()))

    def test_artificial_node_id_raises_value_error(self) -> None:
        """Artificial node IDs are not part of the public API and raise ValueError."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        with pytest.raises(ValueError):
            tdg.calculate_total_slack_of_task(task_node_as_artificial_endnode.id)
        with pytest.raises(ValueError):
            tdg.calculate_total_slack_of_task(task_node_as_artificial_startnode.id)


class TestScheduleEntryTotalSlack:
    """Tests that total_slack is correctly included in ScheduleReport entries (issue #88)."""

    def test_entry_total_slack_matches_calculate_total_slack(self) -> None:
        """Each ScheduleEntry.total_slack matches calculate_total_slack_of_task."""
        short = _node("short", 5)
        long_ = _node("long", 30)
        end = _node("end", 5)
        tdg = TaskDependencyGraph(
            task_list=[short, long_, end],
            dependency_list=[_edge(short, end), _edge(long_, end)],
            starting_time_of_run=_T0,
        )
        report = tdg.create_schedule_report()
        by_id = {e.task_id: e for e in report.entries}
        for task in [short, long_, end]:
            assert by_id[task.id].total_slack == tdg.calculate_total_slack_of_task(task.id)


# ---------------------------------------------------------------------------
# Issue #89 – configurable Mermaid Gantt output
# ---------------------------------------------------------------------------


class TestMermaidGanttConfig:
    """Tests for to_mermaid_gantt with MermaidGanttConfig (issue #89)."""

    def test_default_output_contains_hardcoded_defaults(self) -> None:
        """Calling with no config preserves the existing title/format/section defaults."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt()
        assert "title A Gantt Diagram" in output
        assert "dateFormat YYYY-MM-DDTHH:mm:SZ" in output
        assert "axisFormat %d.%m %H:%M" in output
        assert "tickInterval 15minute" in output
        assert "section Example Stream" in output

    def test_custom_title_appears_in_output(self) -> None:
        """A custom title is rendered in the chart header."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(title="My Project"))
        assert "title My Project" in output
        assert "title A Gantt Diagram" not in output

    def test_custom_date_format_appears_in_output(self) -> None:
        """A custom date_format is emitted in the chart header."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(date_format="YYYY-MM-DD"))
        assert "dateFormat YYYY-MM-DD" in output

    def test_custom_axis_format_appears_in_output(self) -> None:
        """A custom axis_format is emitted in the chart header."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(axis_format="%H:%M"))
        assert "axisFormat %H:%M" in output

    def test_custom_tick_interval_appears_in_output(self) -> None:
        """A custom tick_interval is emitted in the chart header."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(tick_interval="1hour"))
        assert "tickInterval 1hour" in output

    def test_custom_section_label_appears_in_output(self) -> None:
        """A custom section_label replaces the default section header."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(section_label="My Stream"))
        assert "section My Stream" in output
        assert "section Example Stream" not in output

    def test_critical_path_task_still_marked_crit(self) -> None:
        """Critical-path tasks are still marked with 'crit' when using a custom config."""
        a = _node("A", 10)
        b = _node("B", 20)
        tdg = TaskDependencyGraph(task_list=[a, b], dependency_list=[_edge(a, b)], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(title="Custom"))
        assert "crit" in output

    def test_milestone_still_marked_milestone(self) -> None:
        """Milestones are still marked with 'milestone' when using a custom config."""
        ms = _node("MS", 0, milestone=True)
        tdg = TaskDependencyGraph(task_list=[ms], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(title="Custom"))
        assert "milestone" in output

    def test_group_by_phase_creates_sections_per_phase(self) -> None:
        """When group_by_phase=True, tasks are grouped into Mermaid sections by phase."""
        a = _node("A", 10, phase="Phase 1")
        b = _node("B", 20, phase="Phase 2")
        c = _node("C", 5, phase="Phase 1")
        tdg = TaskDependencyGraph(task_list=[a, b, c], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(group_by_phase=True))
        assert "section Phase 1" in output
        assert "section Phase 2" in output

    def test_default_output_is_identical_to_hardcoded_baseline(self) -> None:
        """Passing no config produces byte-for-byte identical output to the old hardcoded version."""
        task = _node("A", 10)
        tdg = TaskDependencyGraph(task_list=[task], dependency_list=[], starting_time_of_run=_T0)
        # Build the expected header the same way the old triple-quoted string did.
        expected_header = (
            "gantt\n"
            "    title A Gantt Diagram\n"
            "    dateFormat YYYY-MM-DDTHH:mm:SZ\n"
            "    axisFormat %d.%m %H:%M\n"
            "    tickInterval 15minute\n"
            "    section Example Stream\n"
        )
        output = tdg.to_mermaid_gantt()
        assert output.startswith(expected_header)

    def test_group_by_phase_none_tasks_go_under_section_label(self) -> None:
        """Tasks with phase=None are placed under section_label when group_by_phase=True."""
        a = _node("A", 10)  # phase=None
        b = _node("B", 20, phase="Phase 1")
        tdg = TaskDependencyGraph(task_list=[a, b], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(group_by_phase=True, section_label="Ungrouped"))
        assert "section Ungrouped" in output
        assert "section Phase 1" in output

    def test_group_by_phase_all_none_phases_produces_single_section(self) -> None:
        """When every task has phase=None, group_by_phase=True emits a single section."""
        a = _node("A", 10)
        b = _node("B", 20)
        tdg = TaskDependencyGraph(task_list=[a, b], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(group_by_phase=True, section_label="All"))
        assert output.count("section ") == 1
        assert "section All" in output

    def test_group_by_phase_section_order_follows_first_encounter(self) -> None:
        """Phase sections appear in the order their phase is first encountered in graph iteration."""
        a = _node("A", 10, phase="Alpha")
        b = _node("B", 20, phase="Beta")
        c = _node("C", 5, phase="Alpha")
        tdg = TaskDependencyGraph(task_list=[a, b, c], dependency_list=[], starting_time_of_run=_T0)
        output = tdg.to_mermaid_gantt(MermaidGanttConfig(group_by_phase=True))
        # Artificial nodes (phase=None) appear first, then Alpha, then Beta in insertion order.
        alpha_pos = output.index("section Alpha")
        beta_pos = output.index("section Beta")
        assert alpha_pos < beta_pos

    def test_multiple_configs_each_produce_valid_charts(self) -> None:
        """Creating several config instances and generating charts from each all succeed."""
        a = _node("A", 10)
        b = _node("B", 20)
        tdg = TaskDependencyGraph(task_list=[a, b], dependency_list=[_edge(a, b)], starting_time_of_run=_T0)
        configs = [
            MermaidGanttConfig(),
            MermaidGanttConfig(title="Project X", tick_interval="1hour"),
            MermaidGanttConfig(axis_format="%H:%M", section_label="Stream A", group_by_phase=False),
        ]
        for cfg in configs:
            output = tdg.to_mermaid_gantt(cfg)
            assert output.startswith("gantt\n")
            assert f"title {cfg.title}" in output
            assert f"tickInterval {cfg.tick_interval}" in output


# ---------------------------------------------------------------------------


class TestMermaidGanttConfigValidation:
    """Tests for MermaidGanttConfig field validation (construction-time enforcement)."""

    def test_empty_title_raises_validation_error(self) -> None:
        """An empty title string is rejected at construction time."""
        with pytest.raises(ValidationError):
            MermaidGanttConfig(title="")

    def test_empty_date_format_raises_validation_error(self) -> None:
        """An empty date_format string is rejected at construction time."""
        with pytest.raises(ValidationError):
            MermaidGanttConfig(date_format="")

    def test_empty_axis_format_raises_validation_error(self) -> None:
        """An empty axis_format string is rejected at construction time."""
        with pytest.raises(ValidationError):
            MermaidGanttConfig(axis_format="")

    def test_empty_section_label_raises_validation_error(self) -> None:
        """An empty section_label string is rejected at construction time."""
        with pytest.raises(ValidationError):
            MermaidGanttConfig(section_label="")

    def test_invalid_tick_interval_raises_validation_error(self) -> None:
        """A tick_interval that doesn't match the Mermaid pattern is rejected at construction time."""
        with pytest.raises(ValidationError):
            MermaidGanttConfig(tick_interval="notaninterval")

    def test_tick_interval_missing_number_raises_validation_error(self) -> None:
        """A tick_interval without a leading integer is rejected at construction time."""
        with pytest.raises(ValidationError):
            MermaidGanttConfig(tick_interval="hour")

    def test_tick_interval_plural_unit_is_accepted(self) -> None:
        """tick_interval values with plural units (e.g. '30minutes') are accepted."""
        cfg = MermaidGanttConfig(tick_interval="30minutes")
        assert cfg.tick_interval == "30minutes"

    @pytest.mark.parametrize(
        "interval",
        ["1millisecond", "5seconds", "15minute", "1hour", "2hours", "1day", "1week", "1month"],
    )
    def test_valid_tick_intervals_are_accepted(self, interval: str) -> None:
        """All supported Mermaid tick_interval unit variants are accepted."""
        cfg = MermaidGanttConfig(tick_interval=interval)
        assert cfg.tick_interval == interval


# ---------------------------------------------------------------------------


class TestTaskNodeExecutionStatus:
    """Tests for the optional execution_status field on TaskNode (issue #90)."""

    def test_task_node_defaults_to_no_execution_status(self) -> None:
        """TaskNode can be constructed without providing execution_status; it defaults to None."""
        task = _node("A", 10)
        assert task.execution_status is None

    def test_task_node_accepts_each_execution_status_value(self) -> None:
        """TaskNode accepts every TaskExecutionStatus variant when explicitly provided."""
        for status in TaskExecutionStatus:
            task = TaskNode(
                id=TaskId(uuid.uuid4()),
                external_id="X",
                name="Task X",
                planned_duration=timedelta(minutes=10),
                execution_status=status,
            )
            assert task.execution_status is status

    def test_execution_status_does_not_affect_planned_start(self) -> None:
        """execution_status has no effect on the computed planned_starting_time."""
        base = _node("A", 30)
        with_status = TaskNode(
            id=base.id,
            external_id=base.external_id,
            name=base.name,
            planned_duration=base.planned_duration,
            execution_status=TaskExecutionStatus.STARTED,
        )
        tdg_base = TaskDependencyGraph(task_list=[base], dependency_list=[], starting_time_of_run=_T0)
        tdg_status = TaskDependencyGraph(task_list=[with_status], dependency_list=[], starting_time_of_run=_T0)
        report_base = tdg_base.create_schedule_report()
        report_status = tdg_status.create_schedule_report()
        entries_base = [e for e in report_base.entries if e.task_id == base.id]
        entries_status = [e for e in report_status.entries if e.task_id == with_status.id]
        assert entries_base[0].planned_start == entries_status[0].planned_start

    def test_execution_status_does_not_affect_critical_path(self) -> None:
        """execution_status has no effect on whether a task is on the critical path."""
        a = _node("A", 10)
        b = _node("B", 20)
        a_completed = TaskNode(
            id=a.id,
            external_id=a.external_id,
            name=a.name,
            planned_duration=a.planned_duration,
            execution_status=TaskExecutionStatus.COMPLETED,
        )
        tdg_no_status = TaskDependencyGraph(task_list=[a, b], dependency_list=[_edge(a, b)], starting_time_of_run=_T0)
        tdg_with_status = TaskDependencyGraph(
            task_list=[a_completed, b], dependency_list=[_edge(a_completed, b)], starting_time_of_run=_T0
        )
        assert tdg_no_status.get_critical_path_task_ids() == tdg_with_status.get_critical_path_task_ids()

    def test_execution_status_does_not_affect_validation(self) -> None:
        """execution_status does not cause or suppress graph definition findings."""
        a = _node("A", 10)
        a_with_status = TaskNode(
            id=a.id,
            external_id=a.external_id,
            name=a.name,
            planned_duration=a.planned_duration,
            execution_status=TaskExecutionStatus.NOT_YET_REQUESTED,
        )
        result_no_status = TaskDependencyGraph.validate_definition(task_list=[a], dependency_list=[])
        result_with_status = TaskDependencyGraph.validate_definition(task_list=[a_with_status], dependency_list=[])
        assert result_no_status.findings == result_with_status.findings

    def test_task_node_with_execution_status_is_hashable(self) -> None:
        """TaskNode with an execution_status can be used as a dict key (hashability is intact)."""
        task = TaskNode(
            id=TaskId(uuid.uuid4()),
            external_id="H",
            name="Hashable Task",
            planned_duration=timedelta(minutes=5),
            execution_status=TaskExecutionStatus.REQUESTED,
        )
        d = {task: "value"}
        assert d[task] == "value"

    def test_milestone_docstring_does_not_imply_mandatory_execution_status(self) -> None:
        """A milestone can be constructed without execution_status; the field remains optional."""
        ms = TaskNode(
            id=TaskId(uuid.uuid4()),
            external_id="MS1",
            name="Milestone 1",
            planned_duration=timedelta(0),
            is_milestone=True,
        )
        assert ms.execution_status is None

    def test_execution_status_exported_from_models(self) -> None:
        """TaskExecutionStatus is accessible via the top-level taskdependencygraph.models package."""
        assert tdg_models.TaskExecutionStatus is TaskExecutionStatus

    def test_execution_status_round_trips_through_pydantic_serialisation(self) -> None:
        """execution_status survives model_dump / model_validate round-trip as a StrEnum."""
        task = TaskNode(
            id=TaskId(uuid.uuid4()),
            external_id="RT",
            name="Round-trip Task",
            planned_duration=timedelta(minutes=15),
            execution_status=TaskExecutionStatus.OBSOLETE,
        )
        dumped = task.model_dump()
        restored = TaskNode.model_validate(dumped)
        assert restored.execution_status is TaskExecutionStatus.OBSOLETE

    def test_execution_status_does_not_appear_in_dot_output(self) -> None:
        """execution_status value is not leaked into the DOT representation of a task."""
        task = TaskNode(
            id=TaskId(uuid.uuid4()),
            external_id="D",
            name="Dot Task",
            planned_duration=timedelta(minutes=10),
            execution_status=TaskExecutionStatus.STARTED,
        )
        dot = task.to_dot({"label": "Dot Task", "color": "blue"})
        assert "STARTED" not in dot
        assert "execution_status" not in dot
