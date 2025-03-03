"""
a test for demonstration purposes
"""

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from taskdependencygraph.models import TaskDependencyId, TaskId
from taskdependencygraph.models.task_dependency_edge import TaskDependencyEdge
from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.models.task_node_as_artificial_endnode import ID_OF_ARTIFICIAL_ENDNODE
from taskdependencygraph.plotting import KrokiClient
from taskdependencygraph.plotting.protocols import PlotMode
from taskdependencygraph.task_dependency_graph import TaskDependencyGraph


# pylint:disable=too-many-locals # it's just a demo test
async def test_baking_a_cake(kroki_client: KrokiClient) -> None:
    """
    a test case that makes the possibilities clear
    """
    start = datetime(2025, 1, 1, 18, 0, 0, 0, tzinfo=UTC)

    # first we create some tasks that need to be done
    shopping_at_grocery_store = TaskNode(
        planned_duration=timedelta(minutes=30),
        external_id="supermarket",
        name="Shopping Flour and Sugar in the Grocery Store",
        id=TaskId(uuid.uuid4()),
    )
    shopping_at_weekly_market = TaskNode(
        planned_duration=timedelta(minutes=20),
        external_id="strawberries",
        name="Shopping Strawberries at Weekly Market",
        id=TaskId(uuid.uuid4()),
    )
    milestone_shopping_is_done = TaskNode(
        is_milestone=True,
        external_id="milestone-0",
        planned_duration=timedelta(minutes=0),
        name="Milestone 'Shopping is Done'",
        id=TaskId(uuid.uuid4()),
    )
    whipping_the_creme = TaskNode(
        external_id="creme",
        name="Preparing the Creme",
        planned_duration=timedelta(minutes=15),
        id=TaskId(uuid.uuid4()),
    )
    doing_the_cake_base = TaskNode(
        external_id="cake-base",
        name="Doing Cake Base",
        planned_duration=timedelta(minutes=30),
        id=TaskId(uuid.uuid4()),
    )
    decoration = TaskNode(
        external_id="decoration",
        name="Add some Decoration",
        planned_duration=timedelta(minutes=5),
        id=TaskId(uuid.uuid4()),
    )
    putting_it_all_together = TaskNode(
        planned_duration=timedelta(minutes=20),
        external_id="putting-it-all-together",
        name="Putting It All Together",
        id=TaskId(uuid.uuid4()),
    )
    edges = [
        TaskDependencyEdge(
            task_predecessor=predecessor.id, task_successor=successor.id, id=TaskDependencyId(uuid.uuid4())
        )
        for predecessor, successor in [
            (shopping_at_grocery_store, milestone_shopping_is_done),
            (shopping_at_weekly_market, milestone_shopping_is_done),
            (milestone_shopping_is_done, whipping_the_creme),
            (milestone_shopping_is_done, doing_the_cake_base),
            (doing_the_cake_base, putting_it_all_together),
            (whipping_the_creme, putting_it_all_together),
            (putting_it_all_together, decoration),
        ]
    ]
    tdg = TaskDependencyGraph(
        task_list=[
            # order is irrelevant here
            shopping_at_weekly_market,
            shopping_at_grocery_store,
            milestone_shopping_is_done,
            whipping_the_creme,
            doing_the_cake_base,
            decoration,
            putting_it_all_together,
        ],
        dependency_list=edges,
        starting_time_of_run=start,
    )

    # The so called 'critical path' includes those nodes in the graph for which any delay leads to a delay of the
    # last node in the graph. Nodes not on the critical path can have a delay and still, the overall finishing time
    # wouldn't change.
    assert tdg.is_on_critical_path(shopping_at_weekly_market.id) is False
    assert (
        tdg.is_on_critical_path(shopping_at_grocery_store.id) is True
    )  # because this is parallel to the shopping at the farm but takes longer

    shopping_finished_at = tdg.calculate_planned_starting_time_of_task(milestone_shopping_is_done.id)
    assert shopping_finished_at == start + timedelta(minutes=30)

    # to get the time when everything is done, the TDG has something like a virtual end node
    cake_is_done_at = tdg.calculate_planned_starting_time_of_task(ID_OF_ARTIFICIAL_ENDNODE)
    assert cake_is_done_at == start + timedelta(hours=1, minutes=25)

    actual = {
        "dot": tdg.to_dot(),  # generates the dot language code
        "gantt": tdg.to_mermaid_gantt(),  # generates mermaid.js code
        "tdg": tdg,  # the graph itself
    }
    supported_visualizations: list[PlotMode] = ["dot", "gantt"]
    # now if you have a kroki server started in docker (see the test fixtures), you can visualize the plan
    for plot_mode in supported_visualizations:
        svg_code = await kroki_client.plot_as_svg(tdg, mode=plot_mode)
        actual[f"{plot_mode}_svg"] = svg_code
        with open(Path(__file__).parent / f"baking_a_cake_{plot_mode}.svg", "w", encoding="utf-8") as outfile:
            outfile.write(svg_code)
    # we used to have a snapshot test on actual here, but it required hardcoded uuids to have reproducible results
