"""
TaskDependencyGraph
"""

# pylint:disable=anomalous-backslash-in-string
# The backslashes are part of an ASCII art embedded into a docstring.
import copy
import uuid
from datetime import datetime, timedelta
from itertools import pairwise
from typing import Literal, Mapping

import networkx as nx  # type: ignore[import-untyped]
from networkx import DiGraph, dag_longest_path_length
from pydantic import AwareDatetime

from taskdependencygraph.models.ids import TaskDependencyId, TaskId
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge
from taskdependencygraph.models.task_dependency_update import (
    AddEdgeToGraphPreviewResponse,
    AddNodeToGraphPreviewResponse,
)
from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.models.task_node_as_artificial_endnode import task_node_as_artificial_endnode
from taskdependencygraph.models.task_node_as_artificial_startnode import task_node_as_artificial_startnode


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
        longest_path = nx.dag_longest_path(self._graph, weight="weight")  # The weight of the edge is the duration
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

    def create_list_of_task_node_copies_with_planned_starting_time(self) -> list[TaskNode]:
        """
        Returns a new task_list, in which tasks are sorted by their planned_starting_time.
        Note that, as in the task_list, artificial_startnode and -endnode are not included in the new_task_list.
        Info: Maybe we don't need this method anymore.
        """
        new_task_list = []

        for task_id in self._graph.nodes:
            if task_id in {task_node_as_artificial_startnode.id, task_node_as_artificial_endnode.id}:
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
            raise ValueError(f"Node with id {sub_end} end is not a milestone")
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
            self._graph[successor][predecessor]["domain_model"].to_dot()
            for successor, predecessor in self._graph.edges()
        )
        result += "}"
        # for debugging purposes you might copy the result from your IDE/Debugger and paste it here:
        # https://kroki.io/#try (select 'GraphViz' in the dropdown)
        return result

    def to_mermaid_gantt(self) -> str:
        """
        Returns the mermaid-gantt-representation of the entire tdg
        """
        result: str = """gantt
    title A Gantt Diagram
    dateFormat YYYY-MM-DDTHH:mm:SZ
    axisFormat %d.%m %H:%M
    tickInterval 15minute
    section Example Stream
"""
        # todo: group by stream https://github.com/Hochfrequenz/cutover-tool/issues/374
        result += "".join(self._get_task_mermaid_gantt(tid) for tid in self._graph.nodes().keys())
        return result
