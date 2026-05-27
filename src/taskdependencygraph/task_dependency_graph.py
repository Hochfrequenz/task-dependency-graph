"""
TaskDependencyGraph
"""

# pylint:disable=anomalous-backslash-in-string
# pylint:disable=too-many-lines
# pylint:disable=too-many-public-methods
# The backslashes are part of an ASCII art embedded into a docstring.
# pylint:disable=too-many-lines
# pylint:disable=too-many-public-methods
import copy
import uuid
from datetime import datetime, timedelta
from itertools import pairwise
from typing import Literal, Mapping

import networkx as nx  # type: ignore[import-untyped]
from networkx import DiGraph, dag_longest_path, dag_longest_path_length
from pydantic import AwareDatetime

from taskdependencygraph.models.delay_impact import DelayImpact
from taskdependencygraph.models.graph_definition_validation import (
    GraphDefinitionValidationFinding,
    GraphDefinitionValidationResult,
    ValidationCode,
)
from taskdependencygraph.models.ids import TaskDependencyId, TaskId
from taskdependencygraph.models.mermaid_gantt_config import MermaidGanttConfig
from taskdependencygraph.models.schedule_report import ScheduleEntry, ScheduleReport
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge
from taskdependencygraph.models.task_dependency_update import (
    AddEdgeToGraphPreviewResponse,
    AddNodeToGraphPreviewResponse,
    RemoveEdgeFromGraphPreviewResponse,
    RemoveNodeFromGraphPreviewResponse,
)
from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.models.task_node_as_artificial_endnode import task_node_as_artificial_endnode
from taskdependencygraph.models.task_node_as_artificial_startnode import task_node_as_artificial_startnode

_ARTIFICIAL_NODE_IDS: frozenset[TaskId] = frozenset(
    {task_node_as_artificial_startnode.id, task_node_as_artificial_endnode.id}
)


class TaskDependencyGraph:
    """
    This class is a wrapper around a directed graph. This means, that in this digraph class instances are instantiated,
    which have the digraph as an attribute.

    Directed graphs are graphs, in which one node, for example task 2, has a relation to another, for example task 1,
    but not necessarily vice versa (in this example: task 2, which is the successor, depends on task 1 as a predecessor.
    But task 1 doesn't depend on task 2: there is no consequence for task 1 if task 2 is for example not completed).

    This digraph contains tasks as nodes, which are connected by task dependencies as edges.

    Note that the actual DiGraph is only an attribute of an instance of TaskDependencyGraph. So, if you want to use the
    TaskDependencyGraph, you need to refer to its attribute ("_graph") first.
    But you shouldn't access it in the first place, except for some tests.
    There is a reason why it's "private"/"protected".
    """

    @staticmethod
    def _validate_tasks(
        task_list: list[TaskNode],
    ) -> tuple[list[GraphDefinitionValidationFinding], set[TaskId]]:
        findings: list[GraphDefinitionValidationFinding] = []
        valid_task_ids: set[TaskId] = set()
        seen_ids: set[TaskId] = set()
        reported_dup_ids: set[TaskId] = set()
        seen_external_ids: dict[str, TaskId] = {}
        reported_dup_external_ids: set[str] = set()

        for task in task_list:
            if task.id in seen_ids:
                if task.id not in reported_dup_ids:
                    findings.append(
                        GraphDefinitionValidationFinding(
                            code=ValidationCode.DUPLICATE_TASK_ID,
                            message=f"Duplicate task id: {task.id!r}",
                            task_id=task.id,
                        )
                    )
                    reported_dup_ids.add(task.id)
            else:
                seen_ids.add(task.id)
                valid_task_ids.add(task.id)

            if task.external_id in seen_external_ids:
                if task.external_id not in reported_dup_external_ids:
                    findings.append(
                        GraphDefinitionValidationFinding(
                            code=ValidationCode.DUPLICATE_EXTERNAL_ID,
                            message=(
                                f"Duplicate external_id {task.external_id!r}: "
                                f"first seen at task {seen_external_ids[task.external_id]!r}"
                            ),
                            task_id=task.id,
                        )
                    )
                    reported_dup_external_ids.add(task.external_id)
            else:
                seen_external_ids[task.external_id] = task.id

            if task.is_milestone and task.planned_duration.total_seconds() > 0:
                findings.append(
                    GraphDefinitionValidationFinding(
                        code=ValidationCode.INVALID_MILESTONE_DURATION,
                        message=(
                            f"Milestone {task.external_id!r} has non-zero planned duration: {task.planned_duration}"
                        ),
                        task_id=task.id,
                    )
                )

        return findings, valid_task_ids

    @staticmethod
    def _validate_edges(
        dependency_list: list[TaskDependencyEdge],
        valid_task_ids: set[TaskId],
    ) -> tuple[list[GraphDefinitionValidationFinding], list[TaskDependencyEdge]]:
        findings: list[GraphDefinitionValidationFinding] = []
        valid_edges: list[TaskDependencyEdge] = []
        seen_dep_ids: set[TaskDependencyId] = set()
        reported_dup_dep_ids: set[TaskDependencyId] = set()
        seen_edge_pairs: set[tuple[TaskId, TaskId]] = set()

        for edge in dependency_list:
            if edge.id in seen_dep_ids:
                if edge.id not in reported_dup_dep_ids:
                    findings.append(
                        GraphDefinitionValidationFinding(
                            code=ValidationCode.DUPLICATE_DEPENDENCY_ID,
                            message=f"Duplicate dependency id: {edge.id!r}",
                            dependency_id=edge.id,
                        )
                    )
                    reported_dup_dep_ids.add(edge.id)
            else:
                seen_dep_ids.add(edge.id)

            if edge.task_predecessor not in valid_task_ids:
                findings.append(
                    GraphDefinitionValidationFinding(
                        code=ValidationCode.MISSING_EDGE_ENDPOINT,
                        message=f"Edge {edge.id!r} references unknown predecessor {edge.task_predecessor!r}",
                        task_id=edge.task_predecessor,
                        dependency_id=edge.id,
                    )
                )

            if edge.task_successor not in valid_task_ids:
                findings.append(
                    GraphDefinitionValidationFinding(
                        code=ValidationCode.MISSING_EDGE_ENDPOINT,
                        message=f"Edge {edge.id!r} references unknown successor {edge.task_successor!r}",
                        task_id=edge.task_successor,
                        dependency_id=edge.id,
                    )
                )

            pair = (edge.task_predecessor, edge.task_successor)
            if pair in seen_edge_pairs:
                findings.append(
                    GraphDefinitionValidationFinding(
                        code=ValidationCode.DUPLICATE_EDGE_PAIR,
                        message=f"Duplicate edge pair: {edge.task_predecessor!r} -> {edge.task_successor!r}",
                        dependency_id=edge.id,
                    )
                )
            else:
                seen_edge_pairs.add(pair)

            if edge.task_predecessor in valid_task_ids and edge.task_successor in valid_task_ids:
                valid_edges.append(edge)

        return findings, valid_edges

    @staticmethod
    def _detect_cycle_findings(
        task_list: list[TaskNode],
        valid_edges: list[TaskDependencyEdge],
    ) -> list[GraphDefinitionValidationFinding]:
        """Returns a CYCLE finding if valid_edges form a cycle, otherwise an empty list."""
        if not valid_edges:
            return []
        temp: nx.DiGraph = nx.DiGraph()
        for task in task_list:
            temp.add_node(task.id)
        for edge in valid_edges:
            if not temp.has_edge(edge.task_predecessor, edge.task_successor):
                temp.add_edge(edge.task_predecessor, edge.task_successor)
        if nx.is_directed_acyclic_graph(temp):
            return []
        try:
            cycle = nx.find_cycle(temp)
            cycle_node_ids = [str(u) for u, _ in cycle]
            return [
                GraphDefinitionValidationFinding(
                    code=ValidationCode.CYCLE,
                    message=f"Cycle detected: {' -> '.join(cycle_node_ids)} -> {cycle_node_ids[0]}",
                    task_id=TaskId(cycle[0][0]),
                )
            ]
        except nx.NetworkXNoCycle:  # pragma: no cover
            return []

    @classmethod
    def validate_definition(
        cls, task_list: list[TaskNode], dependency_list: list[TaskDependencyEdge]
    ) -> GraphDefinitionValidationResult:
        """
        Validates raw task and dependency lists before constructing a TaskDependencyGraph.

        Returns a GraphDefinitionValidationResult containing all findings discovered.
        Findings are collected in a single pass rather than stopping at the first problem,
        so callers receive the complete picture in one call without catching exceptions.

        Checks performed (in order):
        - Duplicate TaskNode.id values
        - Duplicate TaskNode.external_id values
        - Milestones with non-zero planned_duration
        - Missing edge endpoints (predecessor or successor not in task_list)
        - Duplicate TaskDependencyEdge.id values
        - Duplicate predecessor/successor edge pairs
        - Cycles (using only edges whose both endpoints exist)
        """
        task_findings, valid_task_ids = cls._validate_tasks(task_list)
        edge_findings, valid_edges = cls._validate_edges(dependency_list, valid_task_ids)
        cycle_findings = cls._detect_cycle_findings(task_list, valid_edges)
        all_findings = task_findings + edge_findings + cycle_findings
        return GraphDefinitionValidationResult(is_valid=not all_findings, findings=tuple(all_findings))

    def __init__(
        self, task_list: list[TaskNode], dependency_list: list[TaskDependencyEdge], starting_time_of_run: AwareDatetime
    ):
        """
        With this method task dependency graphs can be initialized.
        """
        di_graph = nx.DiGraph()
        self._graph = di_graph  # The digraph is a protected attribute of the task dependency graph
        for task in task_list:
            di_graph.add_node(task.id, domain_model=task)
        # As the task_instance.id, is the key in the resulting dictionary;
        # the edges need to link the task_instance.ids (and not the task_instances themselves).
        for edge in dependency_list:
            self._graph.add_edge(
                edge.task_predecessor,
                edge.task_successor,
                weight=self._graph.nodes[edge.task_predecessor]["domain_model"].planned_duration.total_seconds() / 60,
                domain_model=edge,
            )
        self._starting_time_of_run = starting_time_of_run
        self._add_artificial_nodes_and_edges()
        self._account_for_earliest_start()

    def _add_artificial_endnodes_and_edges(self) -> None:
        r"""
        This method adds a task node (with a duration of 0 minutes) as an artificial endnode to the task dependency
        graph. This artificial endnode is then connected to the former final nodes (tasks without successor) by
        artificial edges.

        Thus this hack converts
             (A)
              | \
              |  \
             (B)  \
            /   \  \
          (C)   (D) \
                 |  (F)
                (E)

        to
              (A)
              | \
              |  \
             (B)  \
            /   \  \
          (C)   (D) \
           |     |  (F)
           |    (E)  /
            \    |  /
             \   | /
              \  |/
               (Z)
        where (Z) is the artificial endnode with duration 0.

        This artificial construction has practical reasons: it is needed in order to include the duration of the
        former final nodes into the count, when identifying the critical path. The reason why the duration of the
        former final tasks otherwise isn't included into the count is, that only the duration of the predecessor
        tasks is counted - and the former final tasks are no predecessors. By adding the artificial final task the
        former final tasks become predecessors and thus are included into the count.
        """
        artificial_dependency_list = [
            (task_without_successor, task_node_as_artificial_endnode.id)
            for task_without_successor in self._graph.nodes()
            if not any(DiGraph.successors(self._graph, task_without_successor))
        ]
        self._graph.add_node(task_node_as_artificial_endnode.id, domain_model=task_node_as_artificial_endnode)
        for artificial_edge in artificial_dependency_list:
            self._graph.add_edge(
                artificial_edge[0],
                artificial_edge[1],
                weight=self._graph.nodes[artificial_edge[0]]["domain_model"].planned_duration.total_seconds() / 60,
                domain_model=TaskDependencyEdge(
                    id=TaskDependencyId(uuid.uuid4()),
                    task_predecessor=artificial_edge[0],
                    task_successor=artificial_edge[1],
                ),
            )

    def _add_artificial_startnode_and_edges(self) -> None:
        r"""
        This method adds a task node (with a duration of 0 minutes) as an artificial startnode to the task dependency
        graph. This artificial startnode is then connected to the former final nodes (tasks without successor) by
        artificial edges.

        Thus this hack converts

             (B)
            /   \
          (C)   (D)
           |     |  (F)
           |    (E)  /
            \    |  /
             \   | /
              \  |/
               (Z)

        to
              (A)
              | \
              |  \
             (B)  \
            /   \  \
          (C)   (D) \
           |     |  (F)
           |    (E)  /
            \    |  /
             \   | /
              \  |/
               (Z)
         where (A) is the artificial startnode with duration 0.

        This artificial construction has practical reasons: it makes calculations with Networkx easier.
        """
        artificial_dependency_list = [
            (task_node_as_artificial_startnode.id, task_without_predecessor)
            for task_without_predecessor in self._graph.nodes()
            if not any(DiGraph.predecessors(self._graph, task_without_predecessor))
        ]
        self._graph.add_node(task_node_as_artificial_startnode.id, domain_model=task_node_as_artificial_startnode)
        for artificial_edge in artificial_dependency_list:
            self._graph.add_edge(
                artificial_edge[0],
                artificial_edge[1],
                weight=0,
                domain_model=TaskDependencyEdge(
                    id=TaskDependencyId(uuid.uuid4()),
                    task_predecessor=artificial_edge[0],
                    task_successor=artificial_edge[1],
                ),
            )

    def _add_artificial_nodes_and_edges(self) -> None:
        """
        This method adds the artificial startnode and endnode and their edges to the task dependency graph.
        """
        self._add_artificial_endnodes_and_edges()
        self._add_artificial_startnode_and_edges()

    def _remove_artificial_nodes_and_edges(self) -> None:
        """
        This method removes the artificial startnode and endnode and their edges from the task dependency graph.
        """
        # see networkx docs: if we remove a node, all edges connected to it are removed as well
        self._graph.remove_node(task_node_as_artificial_startnode.id)
        self._graph.remove_node(task_node_as_artificial_endnode.id)

    def _stretch_edges_with_successor_that_has_fixed_start(self) -> None:
        """
        extends the duration of those tasks, which have a successor with the earliest possible start set.
        Ideally, this should only be called if the edges are reset with self._reset_edges().
        Use self._account_for_earliest_start() to ensure this.
        """
        # Assume there are tasks A-->B-->C.
        # If B has an earliest possible start, then the weight of the edge between A and B has to be stretched to
        # account for the earliest possible start of B.
        # The stretch amount is defined by the difference between A's actual duration and the earliest start of B.
        # But if A itself is already delayed, then the stretch amount is defined by the difference between the actual
        # start.
        # The stretch amount/buffer length is returned by self._get_duration_or_buffer_length(...)
        for task_id in nx.topological_sort(self._graph):
            task = self._graph.nodes[task_id]["domain_model"]
            if task.earliest_starttime is not None:
                for predecessor_id in self._graph.predecessors(task.id):
                    # For this to work, it's important that we always start the iteration at the start node.
                    # Otherwise, the results from get_pseudo_duration might not account for the earliest start
                    # (of predecessors) yet.
                    # In other words: All tasks and respective edges, which are taken into consideration in
                    # _get_pseudo_duration have to have their weights adjusted already.
                    # This is guaranteed by the topological sort.
                    self._graph.edges[predecessor_id, task_id]["weight"] = (
                        self._get_duration_or_buffer_length(predecessor_id, task_id).total_seconds() / 60
                    )

    def _reset_edges(self) -> None:
        """
        (Re)sets the edge weights to the duration of the predecessor task.
        Does _not_ consider the earliest possible starts.
        This is used to reset the edge weights after nodes or edges have been modified.
        """
        for edge in self._graph.edges:
            predecessor_id = edge[0]
            self._graph.edges[edge]["weight"] = (
                self._graph.nodes[predecessor_id]["domain_model"].planned_duration.total_seconds() / 60
            )

    def _account_for_earliest_start(self) -> None:
        """
        Adjusts the edge weights to account for the earliest possible start of the successor task.
        """
        self._reset_edges()
        self._stretch_edges_with_successor_that_has_fixed_start()

    def _get_label_text(self, task_node: TaskNode) -> str:
        """
        returns the label text of this TaskNode in the dot representation based on the legacy visualization
        :return: the full label, example:
        EC2210|SAP PI Puffer stoppen (Kommunikation IS-U starten)|Tom Büsche - Dauer 15min|Start 10.10.2023 10:OO:OO"
        """
        planned_start_str = datetime.strftime(
            self.calculate_planned_starting_time_of_task(task_node.id), "%d.%m.%Y %H:%M:%S%Z"
        )
        assignee_name_or_placeholder: str

        if task_node.assignee is None:
            assignee_name_or_placeholder = "(nobody)"
        else:
            assignee_name_or_placeholder = task_node.assignee.name
        parts: list[str] = [
            task_node.external_id,
            task_node.name,
            f"{assignee_name_or_placeholder} - duration {task_node.planned_duration}min",
            f"Start {planned_start_str}",
        ]
        return "|".join(parts)

    def labels(self) -> Mapping[TaskId, str]:
        """
        returns a mapping of the individual task ids to their name
        """
        result = {
            self._graph.nodes[x]["domain_model"].id: self._get_label_text(self._graph.nodes[x]["domain_model"])
            for x in self._graph.nodes
        }
        result.update({task_node_as_artificial_startnode.id: "START", task_node_as_artificial_endnode.id: "END"})
        return result

    def get_digraph_copy(self) -> DiGraph:
        """
        Returns a deep copy of the internal networkx DiGraph for external processing.
        The returned graph will be de-coupled from the TaskDependencyGraph instance.
        It may be used, e.g., to plot the graph with networkx directly (without going over the TaskDependencyGraph).
        """
        return copy.deepcopy(self._graph.copy())

    def is_on_critical_path(self, task_id: TaskId) -> bool:
        """
        With this method it can be checked if a task is on the overall critical path, i.e. on the longest path
        between the first task and last task of this run.
        """
        longest_path = dag_longest_path(self._graph, weight="weight")  # The weight of the edge is the duration
        # of the task predecessor.
        # The longest path is the path, the sum of whose task durations is the greatest.
        # The longest_path is a list of their task ids as keys.
        if task_id in longest_path:
            return True
        if (
            task_id not in self._graph.nodes
            and task_id != task_node_as_artificial_startnode.id
            and task_id != task_node_as_artificial_endnode.id
        ):
            raise ValueError(f"The task {task_id} is not part of the graph at all")
        return False

    def can_task_be_added(self, task_node: TaskNode) -> AddNodeToGraphPreviewResponse:
        """
        returns information on whether a task can be added to the graph
        """
        if task_node.id in self._graph.nodes:
            # probably this is covered by networkx itself, but I didn't check
            return AddNodeToGraphPreviewResponse(
                can_be_added=False, error_message=f"Node with id {task_node.id} already exists in the graph"
            )
        if any(t for t in self._graph.nodes.values() if t["domain_model"].external_id == task_node.external_id):
            return AddNodeToGraphPreviewResponse(
                can_be_added=False,
                error_message=f"Node with external id {task_node.external_id} already exists in the graph",
            )
        return AddNodeToGraphPreviewResponse(can_be_added=True, error_message=None)

    def add_task(self, task_node: TaskNode) -> None:
        """
        Adds a node to the graph.
        This is pretty straight forward and only fails if another node with the same (internal or external) id already
        exists.
        """
        check_result = self.can_task_be_added(task_node)
        if not check_result.can_be_added:
            raise ValueError(check_result.error_message)
        self._remove_artificial_nodes_and_edges()
        self._graph.add_node(task_node.id, domain_model=task_node)
        self._add_artificial_nodes_and_edges()
        self._account_for_earliest_start()

    # pylint:disable=too-many-return-statements
    def can_edge_be_added(self, task_dependency: TaskDependencyEdge) -> AddEdgeToGraphPreviewResponse:
        """
        raises an error if the edge can't be added; Does nothing else
        """
        if task_dependency.task_successor not in self._graph.nodes:
            return AddEdgeToGraphPreviewResponse(
                can_be_added=False,
                error_message=f"Node with id {task_dependency.task_successor} (successor) does not exist in the graph",
            )
        if task_dependency.task_predecessor not in self._graph.nodes:
            return AddEdgeToGraphPreviewResponse(
                can_be_added=False,
                # pylint:disable=line-too-long
                error_message=f"Node with id {task_dependency.task_predecessor} (predecessor) does not exist in the graph",
            )
        if task_dependency.id in {self._graph.edges[x, y]["domain_model"].id for x, y in self._graph.edges}:
            return AddEdgeToGraphPreviewResponse(
                can_be_added=False, error_message=f"Edge with id {task_dependency.id} already exists in the graph"
            )
        if self._graph.has_edge(task_dependency.task_predecessor, task_dependency.task_successor):
            conflict_edge = self._graph.edges[task_dependency.task_predecessor, task_dependency.task_successor][
                "domain_model"
            ]
            return AddEdgeToGraphPreviewResponse(
                can_be_added=False,
                # pylint:disable=line-too-long
                error_message=f"Edge between {task_dependency.task_predecessor} and {task_dependency.task_successor} already exists: {conflict_edge}",
            )
        if self._graph.has_edge(task_dependency.task_successor, task_dependency.task_predecessor):
            conflict_edge = self._graph.edges[task_dependency.task_successor, task_dependency.task_predecessor][
                "domain_model"
            ]
            return AddEdgeToGraphPreviewResponse(
                can_be_added=False,
                # pylint:disable=line-too-long
                error_message=f"Opposite edge between {task_dependency.task_successor} and {task_dependency.task_predecessor} already exists: {conflict_edge}",
            )
        if nx.has_path(self._graph, task_dependency.task_successor, task_dependency.task_predecessor):
            return AddEdgeToGraphPreviewResponse(
                can_be_added=False,
                # pylint:disable=line-too-long
                error_message=f"Adding this edge would create a cycle between {task_dependency.task_predecessor} and {task_dependency.task_successor}",
            )
        return AddEdgeToGraphPreviewResponse(can_be_added=True, error_message=None)

    def add_edge(self, task_dependency: TaskDependencyEdge) -> None:
        """
        Adds an edge to the graph.
        This checks that the graph is still consistent after adding the edge.
        """
        check_result = self.can_edge_be_added(task_dependency)
        if not check_result.can_be_added:
            raise ValueError(check_result.error_message)
        self._remove_artificial_nodes_and_edges()
        # there is lot's of stuff left todo: what if we want to add an edge without a successor or predecessor?
        self._graph.add_edge(
            task_dependency.task_predecessor,
            task_dependency.task_successor,
            weight=self._graph.nodes[task_dependency.task_predecessor]["domain_model"].planned_duration.total_seconds()
            / 60,
            domain_model=task_dependency,
        )
        self._add_artificial_nodes_and_edges()
        self._account_for_earliest_start()

    def can_task_be_removed(self, task_id: TaskId) -> RemoveNodeFromGraphPreviewResponse:
        """
        Returns information on whether a task can be removed from the graph.

        A task can be removed if it exists and is not an internal artificial node.
        Removing a task also removes all of its edges (predecessor and successor alike);
        the graph is automatically re-wired with fresh artificial start/end edges after removal.
        Use this method to check feasibility before calling remove_task.
        """
        if task_id in _ARTIFICIAL_NODE_IDS:
            return RemoveNodeFromGraphPreviewResponse(
                can_be_removed=False,
                error_message=f"Node with id {task_id} is an internal artificial node and cannot be removed",
            )
        if task_id not in self._graph.nodes:
            return RemoveNodeFromGraphPreviewResponse(
                can_be_removed=False,
                error_message=f"Node with id {task_id} does not exist in the graph",
            )
        return RemoveNodeFromGraphPreviewResponse(can_be_removed=True, error_message=None)

    def remove_task(self, task_id: TaskId) -> None:
        """
        Removes a task and all its edges from the graph.
        Raises ValueError if the task does not exist or is an artificial node.
        """
        check_result = self.can_task_be_removed(task_id)
        if not check_result.can_be_removed:
            raise ValueError(check_result.error_message)
        self._remove_artificial_nodes_and_edges()
        self._graph.remove_node(task_id)
        self._add_artificial_nodes_and_edges()
        self._account_for_earliest_start()

    def can_edge_be_removed(self, edge_id: TaskDependencyId) -> RemoveEdgeFromGraphPreviewResponse:
        """
        Returns information on whether an edge can be removed from the graph.

        An edge can be removed if it exists and connects two real (non-artificial) tasks.
        Removing an edge only removes the dependency between those two tasks; both tasks
        remain in the graph. The graph is automatically re-wired with fresh artificial
        start/end edges so that any task that loses its last real predecessor or successor
        is still reachable. Use this method to check feasibility before calling remove_edge.
        """
        for u, v in self._graph.edges:
            if self._graph.edges[u, v]["domain_model"].id == edge_id:
                if u in _ARTIFICIAL_NODE_IDS or v in _ARTIFICIAL_NODE_IDS:
                    return RemoveEdgeFromGraphPreviewResponse(
                        can_be_removed=False,
                        error_message=f"Edge with id {edge_id} is an internal artificial edge and cannot be removed",
                    )
                return RemoveEdgeFromGraphPreviewResponse(can_be_removed=True, error_message=None)
        return RemoveEdgeFromGraphPreviewResponse(
            can_be_removed=False,
            error_message=f"Edge with id {edge_id} does not exist in the graph",
        )

    def remove_edge(self, edge_id: TaskDependencyId) -> None:
        """
        Removes an edge from the graph by its ID.
        Raises ValueError if the edge does not exist or is an artificial edge.
        """
        check_result = self.can_edge_be_removed(edge_id)
        if not check_result.can_be_removed:
            raise ValueError(check_result.error_message)
        edge_to_remove: tuple[TaskId, TaskId] | None = None
        for u, v in self._graph.edges:
            if self._graph.edges[u, v]["domain_model"].id == edge_id:
                edge_to_remove = (u, v)
                break
        if edge_to_remove is None:  # pragma: no cover
            raise RuntimeError(f"Edge {edge_id} passed validation but could not be located — this is a bug")
        self._remove_artificial_nodes_and_edges()
        self._graph.remove_edge(*edge_to_remove)
        self._add_artificial_nodes_and_edges()
        self._account_for_earliest_start()

    def _get_duration_or_buffer_length(self, predecessor_id: TaskId, successor_id: TaskId) -> timedelta:
        """
        Returns either the duration of the task or the difference to a successor with earliest_starttime set.
        This is necessary to calculate start times of tasks where there is any task with the earliest starting time on
        the path.
        In case of the difference to a successor with earliest_starttime being larger than the duration of the task
        itself, the start time of the successor task as well as all following tasks on this path is later than the
        duration of previous tasks suggests (as the earliest starting time of the successor task makes every following
        task on the path start later...).
        To the outside caller, this shall be transparent.
        """
        if not self._graph.has_edge(predecessor_id, successor_id):
            raise ValueError(f"Edge between {predecessor_id} and {successor_id} does not exist")
        predecessor_duration: timedelta = self._graph.nodes[predecessor_id]["domain_model"].planned_duration
        successor_start: AwareDatetime | None = self._graph.nodes[successor_id]["domain_model"].earliest_starttime
        if successor_start is None:
            return predecessor_duration
        pseudo_duration = successor_start - self.calculate_planned_starting_time_of_task(predecessor_id)
        return max(pseudo_duration, predecessor_duration)

    def calculate_planned_duration_of_predecessor_tasks_on_critical_path(self, task_id: TaskId) -> timedelta:
        """
        With this method we can calculate the sum of the durations of those tasks, which are predecessors to the task
        in question and moreover, are on the critical path (only those tasks do not necessarily need to be on the
        critical path, which are on the last path towards the task in question, as the task in question might not be
        on the overall critical path).
        Thus, we can calculate how long it takes to get from the first task(s) to the task in question.
        """
        # In the following, we will need this dictionary to get from the node id to the node and then to its
        # planned duration.
        # gets the last and thus the longest path in the list
        if task_id not in self._graph.nodes():
            # 1st case: invalid task id
            raise ValueError("This task id is invalid.")
        if task_id == task_node_as_artificial_endnode.id:
            duration_of_tasks_on_overall_longest_path = dag_longest_path_length(self._graph, weight="weight")
            return timedelta(minutes=duration_of_tasks_on_overall_longest_path)
        generator_of_simple_paths_sorted_from_short_to_long = nx.shortest_simple_paths(
            self._graph, task_node_as_artificial_startnode.id, task_id, weight="weight"
        )
        list_of_simple_paths_sorted_from_short_to_long: list[list[TaskId]] = list(
            generator_of_simple_paths_sorted_from_short_to_long
        )
        longest_simple_path: list[TaskId] = list_of_simple_paths_sorted_from_short_to_long.pop()
        result = sum(
            (timedelta(minutes=self._graph.edges[edge]["weight"]) for edge in pairwise(longest_simple_path)),
            timedelta(seconds=0),
        )
        return result

    def calculate_planned_starting_time_of_task(self, task_id: TaskId) -> AwareDatetime:
        """
        With this method we can calculate the planned starting time of a task.
        """
        planned_duration_of_predecessor_tasks_on_critical_path = (
            self.calculate_planned_duration_of_predecessor_tasks_on_critical_path(task_id)
        )
        task_domain_model = self._graph.nodes[task_id]["domain_model"]
        own_earliest_start: AwareDatetime | None = task_domain_model.earliest_starttime
        starting_time_of_task = self._starting_time_of_run + planned_duration_of_predecessor_tasks_on_critical_path
        if own_earliest_start is None:
            return starting_time_of_task
        return max(starting_time_of_task, own_earliest_start)

    def calculate_planned_finish_time_of_task(self, task_id: TaskId) -> AwareDatetime:
        """
        Returns the planned finish time of a task: its planned start time plus its planned duration.

        For a zero-duration milestone the finish time equals the start time.
        Raises ValueError if task_id is not a real task in this graph (unknown or artificial node IDs are rejected).
        """
        if task_id not in self._graph.nodes or task_id in _ARTIFICIAL_NODE_IDS:
            raise ValueError(f"Task with id {task_id!r} is not a real task in this graph")
        task: TaskNode = self._graph.nodes[task_id]["domain_model"]
        return self.calculate_planned_starting_time_of_task(task_id) + task.planned_duration

    def get_critical_path_task_ids(self, include_artificial_nodes: bool = False) -> list[TaskId]:
        """
        Returns the ordered list of task IDs on the critical path, from graph start to graph finish.

        Uses the same weighted-DAG semantics as is_on_critical_path: each directed edge carries the
        duration of its predecessor node as weight. Tasks with an earliest_starttime may cause their
        incoming edge weight to be stretched beyond the raw predecessor duration (see
        _stretch_edges_with_successor_that_has_fixed_start), so wall-clock delays are reflected.

        Tie-breaking: when multiple paths share the same total weight, the result follows NetworkX's
        deterministic graph-insertion order (the path whose first differing node was inserted first
        wins). Use a separate get_critical_path_task_id_paths() API (not yet implemented) if all
        tied paths are needed.

        Note: is_on_critical_path() does not filter artificial nodes, so calling it with an
        artificial node ID may return True while that ID is absent from the default output here.

        By default artificial start/end node IDs are excluded. Pass include_artificial_nodes=True
        to include them (useful for debugging or advanced consumers).
        """
        path: list[TaskId] = dag_longest_path(self._graph, weight="weight")
        if include_artificial_nodes:
            return path
        return [tid for tid in path if tid not in _ARTIFICIAL_NODE_IDS]

    def get_critical_path_tasks(self, include_artificial_nodes: bool = False) -> list[TaskNode]:
        """
        Returns the ordered list of TaskNode objects on the critical path, from graph start to graph finish.

        Convenience wrapper around get_critical_path_task_ids that resolves IDs to their domain models.
        The include_artificial_nodes parameter has the same semantics as in get_critical_path_task_ids.
        """
        return [
            self._graph.nodes[tid]["domain_model"]
            for tid in self.get_critical_path_task_ids(include_artificial_nodes=include_artificial_nodes)
        ]

    def _compute_latest_start(self) -> dict[TaskId, timedelta]:
        """
        Backward pass: returns the latest-start offset (from graph start) for every node.

        Processes nodes in reverse topological order. For each node the latest finish is the
        minimum latest-start of all direct successors; latest start = latest finish − duration.
        Uses only planned_duration (not stretched edge weights) so that waiting time introduced
        by earliest_starttime on a successor is correctly reflected as slack for its predecessors.
        """
        graph_finish: timedelta = timedelta(minutes=dag_longest_path_length(self._graph, weight="weight"))
        latest_start: dict[TaskId, timedelta] = {}
        for node in reversed(list(nx.topological_sort(self._graph))):
            successors = list(self._graph.successors(node))
            if not successors:
                latest_start[node] = graph_finish
            else:
                latest_finish = min(latest_start[s] for s in successors)
                latest_start[node] = latest_finish - self._graph.nodes[node]["domain_model"].planned_duration
        return latest_start

    def calculate_total_slack_of_task(self, task_id: TaskId) -> timedelta:
        """
        Returns the total slack of a task: the maximum amount of time by which the task's
        planned start (or finish) can be delayed without pushing out the graph finish time.

        A value of zero means the task lies on a critical path — any delay immediately delays
        the whole graph. A positive value means the task can absorb that much delay without
        affecting the graph finish.

        Computed via a backward pass through the DAG (see _compute_latest_start): for each node
        the latest allowable finish (LF) equals the minimum of the latest starts of all direct
        successors, and latest start (LS) = LF − planned_duration. Total slack = LS − ES, where
        ES is the existing planned-start calculation. Crucially, the backward pass uses only
        planned_duration rather than the stretched edge weights, so waiting time introduced by an
        earliest_starttime constraint on a successor is correctly counted as slack for the
        predecessor rather than being consumed by the edge weight.

        Raises ValueError for unknown task IDs and for the internal artificial start/end nodes,
        which are not part of the public API.

        Note: each call runs a full backward pass (O(V+E)). For bulk queries over all tasks,
        prefer create_schedule_report() which amortises the backward pass across all entries.
        """
        if task_id not in self._graph.nodes or task_id in _ARTIFICIAL_NODE_IDS:
            raise ValueError(f"Task with id {task_id!r} is not a real task in this graph")
        latest_start = self._compute_latest_start()
        earliest_start = self.calculate_planned_starting_time_of_task(task_id) - self._starting_time_of_run
        return latest_start[task_id] - earliest_start

    def calculate_planned_finish_time_of_graph(self) -> AwareDatetime:
        """
        Returns the planned finish time of the entire graph — the moment the last task completes.

        Equivalent to the planned start time of the internal artificial end node, without requiring
        callers to import or know about ID_OF_ARTIFICIAL_ENDNODE.
        """
        return self.calculate_planned_starting_time_of_task(task_node_as_artificial_endnode.id)

    def create_schedule_report(self, include_artificial_nodes: bool = False) -> ScheduleReport:
        """
        Returns a ScheduleReport containing planning data for all tasks in the graph.

        Each ScheduleEntry carries the task's planned start, planned finish, duration,
        milestone and critical-path flags, and filtered predecessor/successor ID lists.
        Artificial start/end nodes are excluded by default; pass include_artificial_nodes=True
        to include them.

        Entries are sorted by planned_start, then external_id, then name.
        Predecessor and successor lists are sorted by the same key on the referenced task.
        """
        critical_path_ids = self.get_critical_path_task_ids(include_artificial_nodes=include_artificial_nodes)
        critical_path_set = set(critical_path_ids)

        # Pre-compute all start times and latest-start offsets once to avoid repeated DAG traversals.
        start_cache: dict[TaskId, AwareDatetime] = {
            tid: self.calculate_planned_starting_time_of_task(tid) for tid in self._graph.nodes
        }
        latest_start_cache: dict[TaskId, timedelta] = self._compute_latest_start()

        def _task_sort_key(tid: TaskId) -> tuple[AwareDatetime, str, str]:
            task: TaskNode = self._graph.nodes[tid]["domain_model"]
            return (start_cache[tid], task.external_id, task.name)

        entries: list[ScheduleEntry] = []
        for task_id in self._graph.nodes:
            if not include_artificial_nodes and task_id in _ARTIFICIAL_NODE_IDS:
                continue
            task: TaskNode = self._graph.nodes[task_id]["domain_model"]
            planned_start = start_cache[task_id]
            planned_finish = (
                self.calculate_planned_finish_time_of_task(task_id)
                if task_id not in _ARTIFICIAL_NODE_IDS
                else planned_start + task.planned_duration
            )
            predecessor_ids = sorted(
                [
                    pid
                    for pid in self._graph.predecessors(task_id)
                    if include_artificial_nodes or pid not in _ARTIFICIAL_NODE_IDS
                ],
                key=_task_sort_key,
            )
            successor_ids = sorted(
                [
                    sid
                    for sid in self._graph.successors(task_id)
                    if include_artificial_nodes or sid not in _ARTIFICIAL_NODE_IDS
                ],
                key=_task_sort_key,
            )

            entries.append(
                ScheduleEntry(
                    task_id=task_id,
                    external_id=task.external_id,
                    name=task.name,
                    phase=task.phase,
                    tags=task.tags,
                    planned_start=planned_start,
                    planned_finish=planned_finish,
                    planned_duration=task.planned_duration,
                    is_milestone=task.is_milestone,
                    is_on_critical_path=task_id in critical_path_set,
                    total_slack=latest_start_cache[task_id] - (planned_start - self._starting_time_of_run),
                    free_slack=min(
                        (start_cache[s] for s in self._graph.successors(task_id) if s not in _ARTIFICIAL_NODE_IDS),
                        default=start_cache[task_node_as_artificial_endnode.id],
                    )
                    - planned_finish,
                    late_start=self._starting_time_of_run + latest_start_cache[task_id],
                    late_finish=self._starting_time_of_run + latest_start_cache[task_id] + task.planned_duration,
                    predecessor_task_ids=predecessor_ids,
                    successor_task_ids=successor_ids,
                )
            )

        entries.sort(key=lambda e: (e.planned_start, e.external_id, e.name))
        graph_finish = self.calculate_planned_finish_time_of_graph()

        return ScheduleReport(
            graph_start=self._starting_time_of_run,
            graph_finish=graph_finish,
            total_duration=graph_finish - self._starting_time_of_run,
            critical_path_task_ids=critical_path_ids,
            entries=entries,
        )

    def calculate_delay_impact(self, task_id: TaskId, delay: timedelta) -> list[DelayImpact]:
        """
        Returns the tasks whose planned finish would be pushed past their late finish if the
        given task starts `delay` later than planned.

        The delayed task itself appears first when the delay exceeds its own total slack. Tasks
        whose total slack fully absorbs the propagated delay are omitted.

        Propagation uses edge gaps: the slack between a predecessor's planned finish and a
        successor's planned start absorbs part of the delay before it reaches the successor.

        Raises ValueError if task_id is not a real task in this graph or delay is non-positive.
        """
        if delay <= timedelta(0):
            raise ValueError(f"delay must be positive, got {delay}")
        if task_id not in self._graph.nodes or task_id in _ARTIFICIAL_NODE_IDS:
            raise ValueError(f"Task with id {task_id!r} is not a real task in this graph")
        start_cache: dict[TaskId, AwareDatetime] = {
            tid: self.calculate_planned_starting_time_of_task(tid) for tid in self._graph.nodes
        }
        latest_start_cache = self._compute_latest_start()
        task_total_slack = latest_start_cache[task_id] - (start_cache[task_id] - self._starting_time_of_run)
        if delay <= task_total_slack:
            return []
        prop_delay: dict[TaskId, timedelta] = {task_id: delay}
        result: list[DelayImpact] = [DelayImpact(task_id=task_id, additional_delay=delay - task_total_slack)]
        for node in nx.topological_sort(self._graph):
            if node == task_id or node in _ARTIFICIAL_NODE_IDS:
                continue
            incoming = timedelta(0)
            for p in self._graph.predecessors(node):
                if p not in prop_delay:
                    continue
                p_duration: timedelta = self._graph.nodes[p]["domain_model"].planned_duration
                edge_gap: timedelta = start_cache[node] - (start_cache[p] + p_duration)
                incoming = max(incoming, timedelta(0), prop_delay[p] - edge_gap)
            if incoming <= timedelta(0):
                continue
            prop_delay[node] = incoming
            node_total_slack = latest_start_cache[node] - (start_cache[node] - self._starting_time_of_run)
            node_additional_delay = max(timedelta(0), incoming - node_total_slack)
            if node_additional_delay > timedelta(0):
                result.append(DelayImpact(task_id=node, additional_delay=node_additional_delay))
        return result

    def create_list_of_task_node_copies_with_planned_starting_time(self) -> list[TaskNode]:
        """
        Returns a new task_list, in which tasks are sorted by their planned_starting_time.
        Note that, as in the task_list, artificial_startnode and -endnode are not included in the new_task_list.
        Info: Maybe we don't need this method anymore.
        """
        new_task_list = []

        for task_id in self._graph.nodes:
            if task_id in _ARTIFICIAL_NODE_IDS:
                continue
            task = self._graph.nodes[task_id]["domain_model"]
            copied_task = task.model_copy(
                update={"planned_starting_time": self.calculate_planned_starting_time_of_task(task.id)}
            )
            new_task_list.append(copied_task)
        assert all(x.planned_starting_time is not None for x in new_task_list), "The starting time should not be None"
        new_task_list.sort(key=lambda t: t.planned_starting_time)
        return new_task_list

    def extract_sub_graph(self, sub_start: TaskId, sub_end: TaskId) -> "TaskDependencyGraph":
        """
        Creates a new TaskDependencyGraph instance that only contains nodes between sub_start and sub_end
        (both inclusive).
        Raises a meaningful error if start node or end node is not a milestone.
        """
        if sub_start not in self._graph.nodes:
            raise ValueError(f"Node with id {sub_start} (start) does not exist in the graph")
        if sub_end not in self._graph.nodes:
            raise ValueError(f"Node with id {sub_end} (end) does not exist in the graph")
        if not self._graph.nodes[sub_start]["domain_model"].is_milestone:
            raise ValueError(f"Node with id {sub_start} (start) is not a milestone")
        if not self._graph.nodes[sub_end]["domain_model"].is_milestone:
            raise ValueError(f"Node with id {sub_end} (end) is not a milestone")
        if not nx.has_path(self._graph, sub_start, sub_end):
            raise ValueError(f"There is no path between {sub_start} and {sub_end}")

        # Collect all paths between sub_start and sub_end
        all_paths = list(nx.all_simple_paths(self._graph, source=sub_start, target=sub_end))

        # Extract all nodes and edges in these paths
        nodes_in_paths: set[TaskId] = set()
        edges_in_paths: set[tuple[TaskId, TaskId]] = set()
        for path in all_paths:
            nodes_in_paths.update(path)
            edges_in_paths.update((path[i], path[i + 1]) for i in range(len(path) - 1))

        # Create the subgraph from these nodes and edges
        sub_graph = self._graph.subgraph(nodes_in_paths).edge_subgraph(edges_in_paths).copy()

        result = TaskDependencyGraph(
            task_list=[sub_graph.nodes[x]["domain_model"] for x in sub_graph.nodes],
            dependency_list=[sub_graph.edges[x, y]["domain_model"] for x, y in sub_graph.edges],
            starting_time_of_run=self.calculate_planned_starting_time_of_task(sub_start),
        )
        # I'm not 100% sure we need this.
        # My intention was to de-couple the new graph as much from the original graph as possible.
        # If they still shared the same (identical, not only equal) nodes, then they might interfere in some scenarios.
        return copy.deepcopy(result)

    def _get_task_dot(self, task_id: TaskId) -> str:
        """
        Returns the dot-representation of a single task; This will be basically the dot-representation of the task node
        itself + the properties/attributes that can only be calculated from the TaskDependencyGraph in which the task
        is embedded.
        For details on the dot language see https://graphviz.org/doc/info/lang.html
        """
        node: TaskNode = self._graph.nodes[task_id]["domain_model"]
        node_attributes: dict[Literal["label", "color"], str] = {
            "label": self._get_label_text(node),
        }
        if self.is_on_critical_path(task_id=task_id):
            node_attributes["color"] = "red"
        result = node.to_dot(node_attributes)
        return result

    def _get_task_mermaid_gantt(self, task_id: TaskId) -> str:
        """
        Returns the mermaid-gantt-representation of a single task within the TDG.
        """
        # In the end we have to obey this syntax: https://mermaid.js.org/syntax/gantt.html#syntax
        node: TaskNode = self._graph.nodes[task_id]["domain_model"]
        attributes: list[str] = []
        # "Tags are optional, but if used, they must be specified first"
        if self.is_on_critical_path(task_id=task_id):
            attributes.append("crit")
        if node.is_milestone or task_id in {task_node_as_artificial_startnode.id, task_node_as_artificial_endnode.id}:
            attributes.append("milestone")
        attributes.append(str(task_id))
        if task_id == task_node_as_artificial_startnode.id:
            # todo: also use this if-branch if node has has frühstmöglicher startzeitpunkt
            # https://github.com/Hochfrequenz/cutover-tool/issues/377
            # <taskID>, <startDate>, <length>
            attributes.append(self._starting_time_of_run.isoformat())
        else:
            # <taskID>, after <otherTaskId>, <length>
            attributes.append("after " + " ".join(str(x) for x in DiGraph.predecessors(self._graph, task_id)))
        attributes.append(f"{int(node.planned_duration.total_seconds() // 60)}m")
        result = f"""
        {node.name} :{', '.join(attributes)}
        """
        return result

    def to_dot(self) -> str:
        """
        returns a dot representation of the graph.
        For details on the dot language see https://graphviz.org/doc/info/lang.html
        The style information (font, colors, labels ...) have been adapted from /legacy/legacy_visualization_example.dot
        """
        result: str = "digraph fahrplan{\nrankdir = LR;\nnode [shape=record fontname=Calibri];\n"
        result += "".join(self._get_task_dot(tid) for tid in self._graph.nodes().keys())
        result += "".join(
            self._graph[predecessor][successor]["domain_model"].to_dot()
            for predecessor, successor in self._graph.edges()
        )
        result += "}"
        # for debugging purposes you might copy the result from your IDE/Debugger and paste it here:
        # https://kroki.io/#try (select 'GraphViz' in the dropdown)
        return result

    def to_mermaid_gantt(self, config: MermaidGanttConfig | None = None) -> str:
        """
        Returns the Mermaid Gantt chart representation of the entire graph.

        Pass a MermaidGanttConfig to customise the title, date/axis/tick formats,
        section label, or phase grouping. Calling with no argument (or None) preserves
        the existing default output exactly.
        """
        if config is None:
            config = MermaidGanttConfig()

        header = (
            f"gantt\n"
            f"    title {config.title}\n"
            f"    dateFormat {config.date_format}\n"
            f"    axisFormat {config.axis_format}\n"
            f"    tickInterval {config.tick_interval}\n"
        )

        if not config.group_by_phase:
            body = f"    section {config.section_label}\n"
            body += "".join(self._get_task_mermaid_gantt(tid) for tid in self._graph.nodes().keys())
            return header + body

        # Group tasks by phase, preserving graph iteration order within each group.
        phases: dict[str | None, list[TaskId]] = {}
        for tid in self._graph.nodes():
            phase = self._graph.nodes[tid]["domain_model"].phase
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(tid)

        body = ""
        for phase, tids in phases.items():
            section_name = config.section_label if phase is None else phase
            body += f"    section {section_name}\n"
            body += "".join(self._get_task_mermaid_gantt(tid) for tid in tids)

        return header + body
