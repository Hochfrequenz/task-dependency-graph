"""
tests for adding nodes and edges to the TDG
"""

# pylint:disable=protected-access
import copy
import uuid
from datetime import timedelta

import pytest

from taskdependencygraph.models import AddEdgeToGraphPreviewResponse, AddNodeToGraphPreviewResponse
from taskdependencygraph.models.ids import TaskDependencyId, TaskId
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge
from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.models.task_node_as_artificial_endnode import ID_OF_ARTIFICIAL_ENDNODE
from taskdependencygraph.models.task_node_as_artificial_startnode import ID_OF_ARTIFICIAL_STARTNODE
from taskdependencygraph.task_dependency_graph import TaskDependencyGraph

from .example_tdgs import graph_anna, task_A, task_B, task_C, task_D


@pytest.mark.parametrize(
    "graph,node",
    [
        pytest.param(
            copy.deepcopy(graph_anna),
            TaskNode(id=TaskId(uuid.uuid4()), external_id="E", name="E", planned_duration=timedelta(minutes=5)),
            id="add arbitrary node",
        ),
    ],
)
def test_add_ok_task(graph: TaskDependencyGraph, node: TaskNode) -> None:
    graph.add_task(node)
    assert graph._graph.has_node(node.id)


@pytest.mark.parametrize(
    "graph,node",
    [
        pytest.param(
            copy.deepcopy(graph_anna),
            TaskNode(id=TaskId(uuid.uuid4()), external_id="A", name="A", planned_duration=timedelta(minutes=5)),
            id="add node which ID exists",
        ),
        pytest.param(
            copy.deepcopy(graph_anna),
            TaskNode(id=ID_OF_ARTIFICIAL_STARTNODE, external_id="E", name="E", planned_duration=timedelta(minutes=5)),
            id="add node which ID exists",
        ),
        pytest.param(
            copy.deepcopy(graph_anna),
            TaskNode(id=ID_OF_ARTIFICIAL_ENDNODE, external_id="E", name="E", planned_duration=timedelta(minutes=5)),
            id="add node which ID exists",
        ),
    ],
)
def test_add_bad_task(graph: TaskDependencyGraph, node: TaskNode) -> None:
    with pytest.raises(ValueError):
        graph.add_task(node)


def test_add_new_edge_for_two_existing_nodes() -> None:
    # we add a new node between C and D
    graph = copy.deepcopy(graph_anna)
    assert graph._graph.has_edge(task_C.id, ID_OF_ARTIFICIAL_ENDNODE)
    new_edge = TaskDependencyEdge(
        id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_C.id, task_successor=task_D.id
    )
    graph.add_edge(new_edge)
    assert graph._graph.has_edge(task_C.id, task_D.id)
    assert not graph._graph.has_edge(task_C.id, ID_OF_ARTIFICIAL_ENDNODE)


def test_adding_a_cycle_fails() -> None:
    # we add a new node between C and D
    graph = copy.deepcopy(graph_anna)
    new_edge_which_causes_a_cycle = TaskDependencyEdge(
        id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_D.id, task_successor=task_A.id
    )
    with pytest.raises(ValueError) as value_error_info:
        graph.add_edge(new_edge_which_causes_a_cycle)
    assert "cycle" in str(value_error_info.value)
    assert not graph._graph.has_edge(task_D.id, task_A.id)


class TestCanTaskBeAdded:
    """Direct tests of the can_task_be_added preview API — verifies the response object, not just exceptions."""

    def test_returns_true_for_valid_task(self) -> None:
        graph = copy.deepcopy(graph_anna)
        new_task = TaskNode(id=TaskId(uuid.uuid4()), external_id="Z", name="Z", planned_duration=timedelta(minutes=1))
        result = graph.can_task_be_added(new_task)
        assert isinstance(result, AddNodeToGraphPreviewResponse)
        assert result.can_be_added is True
        assert result.error_message is None

    def test_returns_false_for_duplicate_task_id(self) -> None:
        graph = copy.deepcopy(graph_anna)
        duplicate = TaskNode(id=task_A.id, external_id="Z", name="Z", planned_duration=timedelta(minutes=1))
        result = graph.can_task_be_added(duplicate)
        assert result.can_be_added is False
        assert result.error_message is not None
        assert str(task_A.id) in result.error_message

    def test_returns_false_for_duplicate_external_id(self) -> None:
        graph = copy.deepcopy(graph_anna)
        duplicate = TaskNode(
            id=TaskId(uuid.uuid4()), external_id=task_A.external_id, name="Z", planned_duration=timedelta(minutes=1)
        )
        result = graph.can_task_be_added(duplicate)
        assert result.can_be_added is False
        assert result.error_message is not None
        assert str(task_A.external_id) in result.error_message


class TestCanEdgeBeAdded:
    """Direct tests of the can_edge_be_added preview API — verifies all error branches and the success path."""

    def test_returns_true_for_valid_edge(self) -> None:
        graph = copy.deepcopy(graph_anna)
        # graph_anna has A→B, A→C, B→D; no C→D edge exists
        new_edge = TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_C.id, task_successor=task_D.id
        )
        result = graph.can_edge_be_added(new_edge)
        assert isinstance(result, AddEdgeToGraphPreviewResponse)
        assert result.can_be_added is True
        assert result.error_message is None

    def test_returns_false_when_successor_not_in_graph(self) -> None:
        graph = copy.deepcopy(graph_anna)
        missing_id = TaskId(uuid.uuid4())
        edge = TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_A.id, task_successor=missing_id
        )
        result = graph.can_edge_be_added(edge)
        assert result.can_be_added is False
        assert result.error_message is not None
        assert "successor" in result.error_message

    def test_returns_false_when_predecessor_not_in_graph(self) -> None:
        graph = copy.deepcopy(graph_anna)
        missing_id = TaskId(uuid.uuid4())
        edge = TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=missing_id, task_successor=task_A.id
        )
        result = graph.can_edge_be_added(edge)
        assert result.can_be_added is False
        assert result.error_message is not None
        assert "predecessor" in result.error_message

    def test_returns_false_for_duplicate_edge_id(self) -> None:
        graph = copy.deepcopy(graph_anna)
        existing_id = graph._graph.edges[task_A.id, task_B.id]["domain_model"].id
        edge = TaskDependencyEdge(id=existing_id, task_predecessor=task_C.id, task_successor=task_D.id)
        result = graph.can_edge_be_added(edge)
        assert result.can_be_added is False
        assert result.error_message is not None
        assert str(existing_id) in result.error_message

    def test_returns_false_for_duplicate_edge_pair(self) -> None:
        graph = copy.deepcopy(graph_anna)
        # A→B already exists; use a new ID to bypass the duplicate-ID check
        duplicate = TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_A.id, task_successor=task_B.id
        )
        result = graph.can_edge_be_added(duplicate)
        assert result.can_be_added is False
        assert result.error_message is not None
        assert str(task_A.id) in result.error_message

    def test_returns_false_for_opposite_edge(self) -> None:
        graph = copy.deepcopy(graph_anna)
        # A→B exists; adding B→A is the "opposite" direction
        opposite = TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_B.id, task_successor=task_A.id
        )
        result = graph.can_edge_be_added(opposite)
        assert result.can_be_added is False
        assert result.error_message is not None
        assert "Opposite" in result.error_message

    def test_returns_false_when_edge_would_create_cycle(self) -> None:
        graph = copy.deepcopy(graph_anna)
        # A→B→D exists; D→A would form a cycle
        cycle_edge = TaskDependencyEdge(
            id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_D.id, task_successor=task_A.id
        )
        result = graph.can_edge_be_added(cycle_edge)
        assert result.can_be_added is False
        assert result.error_message is not None
        assert "cycle" in result.error_message
