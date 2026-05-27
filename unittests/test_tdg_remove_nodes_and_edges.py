"""
tests for removing nodes and edges from the TDG
"""

# pylint:disable=protected-access
import copy
import uuid
from typing import cast

import pytest

from taskdependencygraph.models import (
    RemoveEdgeFromGraphPreviewResponse,
    RemoveNodeFromGraphPreviewResponse,
)
from taskdependencygraph.models.ids import TaskDependencyId, TaskId
from taskdependencygraph.models.task_node_as_artificial_endnode import ID_OF_ARTIFICIAL_ENDNODE
from taskdependencygraph.models.task_node_as_artificial_startnode import ID_OF_ARTIFICIAL_STARTNODE
from taskdependencygraph.task_dependency_graph import TaskDependencyGraph

from .example_tdgs import graph_anna, graph_bernd, task_A, task_B, task_B_with_fixed_start_2024_01_02, task_C, task_D


def _get_edge_id(graph: TaskDependencyGraph, u: TaskId, v: TaskId) -> TaskDependencyId:
    return cast(TaskDependencyId, graph._graph.edges[u, v]["domain_model"].id)


class TestCanTaskBeRemoved:
    def test_returns_true_for_existing_task(self) -> None:
        graph = copy.deepcopy(graph_anna)
        result = graph.can_task_be_removed(task_A.id)
        assert isinstance(result, RemoveNodeFromGraphPreviewResponse)
        assert result.can_be_removed is True
        assert result.error_message is None

    def test_returns_false_for_unknown_task_id(self) -> None:
        graph = copy.deepcopy(graph_anna)
        missing_id = TaskId(uuid.uuid4())
        result = graph.can_task_be_removed(missing_id)
        assert result.can_be_removed is False
        assert result.error_message is not None
        assert str(missing_id) in result.error_message

    def test_returns_false_for_artificial_start_node(self) -> None:
        graph = copy.deepcopy(graph_anna)
        result = graph.can_task_be_removed(ID_OF_ARTIFICIAL_STARTNODE)
        assert result.can_be_removed is False
        assert result.error_message is not None

    def test_returns_false_for_artificial_end_node(self) -> None:
        graph = copy.deepcopy(graph_anna)
        result = graph.can_task_be_removed(ID_OF_ARTIFICIAL_ENDNODE)
        assert result.can_be_removed is False
        assert result.error_message is not None


class TestRemoveTask:
    def test_removes_task_from_graph(self) -> None:
        graph = copy.deepcopy(graph_anna)
        graph.remove_task(task_C.id)
        assert not graph._graph.has_node(task_C.id)

    def test_removing_task_also_removes_its_edges(self) -> None:
        # graph_anna: A→B, A→C, B→D
        # removing B removes edges A→B and B→D
        graph = copy.deepcopy(graph_anna)
        graph.remove_task(task_B.id)
        assert not graph._graph.has_node(task_B.id)
        assert not graph._graph.has_edge(task_A.id, task_B.id)
        assert not graph._graph.has_edge(task_B.id, task_D.id)

    def test_artificial_start_edge_added_after_removal(self) -> None:
        # After removing B, D has no real predecessor and should gain an artificial start edge.
        graph = copy.deepcopy(graph_anna)
        graph.remove_task(task_B.id)
        assert graph._graph.has_edge(ID_OF_ARTIFICIAL_STARTNODE, task_D.id)

    def test_raises_for_unknown_task(self) -> None:
        graph = copy.deepcopy(graph_anna)
        with pytest.raises(ValueError):
            graph.remove_task(TaskId(uuid.uuid4()))

    def test_raises_for_artificial_start_node(self) -> None:
        graph = copy.deepcopy(graph_anna)
        with pytest.raises(ValueError):
            graph.remove_task(ID_OF_ARTIFICIAL_STARTNODE)

    def test_raises_for_artificial_end_node(self) -> None:
        graph = copy.deepcopy(graph_anna)
        with pytest.raises(ValueError):
            graph.remove_task(ID_OF_ARTIFICIAL_ENDNODE)

    def test_second_remove_raises(self) -> None:
        graph = copy.deepcopy(graph_anna)
        graph.remove_task(task_C.id)
        with pytest.raises(ValueError):
            graph.remove_task(task_C.id)

    def test_remaining_graph_is_still_valid(self) -> None:
        graph = copy.deepcopy(graph_anna)
        graph.remove_task(task_C.id)
        report = graph.create_schedule_report()
        task_ids = {e.task_id for e in report.entries}
        assert task_C.id not in task_ids
        assert task_A.id in task_ids


class TestCanEdgeBeRemoved:
    def test_returns_true_for_existing_real_edge(self) -> None:
        graph = copy.deepcopy(graph_anna)
        edge_id = _get_edge_id(graph, task_A.id, task_B.id)
        result = graph.can_edge_be_removed(edge_id)
        assert isinstance(result, RemoveEdgeFromGraphPreviewResponse)
        assert result.can_be_removed is True
        assert result.error_message is None

    def test_returns_false_for_unknown_edge_id(self) -> None:
        graph = copy.deepcopy(graph_anna)
        missing_id = TaskDependencyId(uuid.uuid4())
        result = graph.can_edge_be_removed(missing_id)
        assert result.can_be_removed is False
        assert result.error_message is not None
        assert str(missing_id) in result.error_message

    def test_returns_false_for_artificial_start_edge(self) -> None:
        graph = copy.deepcopy(graph_anna)
        artificial_edge_id = _get_edge_id(graph, ID_OF_ARTIFICIAL_STARTNODE, task_A.id)
        result = graph.can_edge_be_removed(artificial_edge_id)
        assert result.can_be_removed is False
        assert result.error_message is not None

    def test_returns_false_for_artificial_end_edge(self) -> None:
        # C has no real successors so it has an auto-generated → END edge
        graph = copy.deepcopy(graph_anna)
        artificial_edge_id = _get_edge_id(graph, task_C.id, ID_OF_ARTIFICIAL_ENDNODE)
        result = graph.can_edge_be_removed(artificial_edge_id)
        assert result.can_be_removed is False
        assert result.error_message is not None


class TestRemoveEdge:
    def test_removes_edge_from_graph(self) -> None:
        graph = copy.deepcopy(graph_anna)
        edge_id = _get_edge_id(graph, task_A.id, task_C.id)
        graph.remove_edge(edge_id)
        assert not graph._graph.has_edge(task_A.id, task_C.id)

    def test_removing_edge_readjusts_artificial_nodes(self) -> None:
        # Removing A→C means C has no real predecessor; it should gain an artificial start edge.
        graph = copy.deepcopy(graph_anna)
        edge_id = _get_edge_id(graph, task_A.id, task_C.id)
        graph.remove_edge(edge_id)
        assert graph._graph.has_edge(ID_OF_ARTIFICIAL_STARTNODE, task_C.id)

    def test_raises_for_unknown_edge_id(self) -> None:
        graph = copy.deepcopy(graph_anna)
        with pytest.raises(ValueError):
            graph.remove_edge(TaskDependencyId(uuid.uuid4()))

    def test_raises_for_artificial_edge(self) -> None:
        graph = copy.deepcopy(graph_anna)
        artificial_edge_id = _get_edge_id(graph, ID_OF_ARTIFICIAL_STARTNODE, task_A.id)
        with pytest.raises(ValueError):
            graph.remove_edge(artificial_edge_id)

    def test_second_remove_raises(self) -> None:
        graph = copy.deepcopy(graph_anna)
        edge_id = _get_edge_id(graph, task_A.id, task_B.id)
        graph.remove_edge(edge_id)
        with pytest.raises(ValueError):
            graph.remove_edge(edge_id)

    def test_remaining_graph_is_still_schedulable(self) -> None:
        # Remove B→D; D becomes isolated (only connected via artificial nodes)
        graph = copy.deepcopy(graph_anna)
        edge_id = _get_edge_id(graph, task_B.id, task_D.id)
        graph.remove_edge(edge_id)
        report = graph.create_schedule_report()
        task_ids = {e.task_id for e in report.entries}
        assert task_D.id in task_ids

    def test_remove_edge_on_graph_with_earliest_starttime(self) -> None:
        # graph_bernd: A→B_fixed, A→C, B_fixed→D; B_fixed has earliest_starttime=2024-01-02
        # Removing A→C should not disturb the earliest_starttime scheduling for B_fixed and D.
        graph = copy.deepcopy(graph_bernd)
        edge_id = _get_edge_id(graph, task_A.id, task_C.id)
        graph.remove_edge(edge_id)
        report = graph.create_schedule_report()
        b_entry = next(e for e in report.entries if e.task_id == task_B_with_fixed_start_2024_01_02.id)
        assert b_entry.planned_start >= task_B_with_fixed_start_2024_01_02.earliest_starttime  # type: ignore[operator]
