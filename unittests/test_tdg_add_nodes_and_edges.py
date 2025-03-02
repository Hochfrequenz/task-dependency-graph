"""
tests for adding nodes and edges to the TDG
"""

# pylint:disable=protected-access
import copy
import uuid
from datetime import timedelta

import pytest

from taskdependencygraph.models.ids import TaskDependencyId, TaskId
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge
from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.models.task_node_as_artificial_endnode import ID_OF_ARTIFICIAL_ENDNODE
from taskdependencygraph.models.task_node_as_artificial_startnode import ID_OF_ARTIFICIAL_STARTNODE
from taskdependencygraph.task_dependency_graph import TaskDependencyGraph

from .example_tdgs import graph_anna, task_A, task_C, task_D


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
def test_add_ok_task(graph: TaskDependencyGraph, node: TaskNode):
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
def test_add_bad_task(graph: TaskDependencyGraph, node: TaskNode):
    with pytest.raises(ValueError):
        graph.add_task(node)


def test_add_new_edge_for_two_existing_nodes():
    # we add a new node between C and D
    graph = copy.deepcopy(graph_anna)
    assert graph._graph.has_edge(task_C.id, ID_OF_ARTIFICIAL_ENDNODE)
    new_edge = TaskDependencyEdge(
        id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_C.id, task_successor=task_D.id
    )
    graph.add_edge(new_edge)
    assert graph._graph.has_edge(task_C.id, task_D.id)
    assert not graph._graph.has_edge(task_C.id, ID_OF_ARTIFICIAL_ENDNODE)


def test_adding_a_cycle_fails():
    # we add a new node between C and D
    graph = copy.deepcopy(graph_anna)
    new_edge_which_causes_a_cycle = TaskDependencyEdge(
        id=TaskDependencyId(uuid.uuid4()), task_predecessor=task_D.id, task_successor=task_A.id
    )
    with pytest.raises(ValueError) as value_error_info:
        graph.add_edge(new_edge_which_causes_a_cycle)
    assert "cycle" in str(value_error_info.value)
    assert not graph._graph.has_edge(task_D.id, task_A.id)
