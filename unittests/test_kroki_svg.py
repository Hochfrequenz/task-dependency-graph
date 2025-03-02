import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import pytest

from taskdependencygraph.models.task_node import TaskNode
from taskdependencygraph.plotting.kroki import KrokiClient
from taskdependencygraph.plotting.protocols import PlotMode, Plotter
from taskdependencygraph.task_dependency_graph import TaskDependencyGraph

# don't ask; it's some weird type-checking issues (related to our tox setup) that require me to do this ugly import
from .example_data_for_test_task_dependency_graph import dependency_list_2, task_list_2


async def test_kroki_is_ready(internal_kroki_client: KrokiClient) -> None:
    actual = await internal_kroki_client.is_ready()
    assert actual is True


@pytest.mark.parametrize("mode", [pytest.param("dot"), pytest.param("gantt")])
async def test_convert_tdg_to_svg(internal_kroki_client: Plotter, mode: PlotMode) -> None:
    tdg = TaskDependencyGraph(
        task_list_2,
        dependency_list_2,
        datetime(year=2024, month=3, day=12, hour=12, minute=10, tzinfo=timezone.utc),
    )
    svg = await internal_kroki_client.plot_as_svg(tdg, mode=mode)
    assert svg is not None
    assert svg.startswith("<?xml version=")
    assert not svg.startswith("<ns0:svg xmlns:ns0=@http://www.w3.org/2000/svg")
    root = ET.fromstring(svg)
    assert root is not None, "returned SVG should be valid XML"

    def get_task_svg_node(task: TaskNode, tag_snippet: str) -> list[ET.Element]:
        return list(x for x in root.findall(f".//*[@id='svg-{task.id}']") if tag_snippet in x.tag)

    for task in task_list_2:
        svg_nodes = get_task_svg_node(task, "g")
        assert len(svg_nodes) == 1
    task_6 = [t for t in task_list_2 if t.name == "name6"][0]
    match mode:
        case "dot":
            svg_node6 = list(x for x in root.findall(f".//*[@id='svg-{task_6.id}']/") if "polygon" in x.tag)[0]
            assert (
                svg_node6.attrib["stroke"] == "red"
            ), "The ellipse for task 6 should be red because it's on critical path"
        case "gantt":
            svg_node6 = get_task_svg_node(task_6, "rect")[0]
            assert (
                svg_node6.attrib["class"] == "task crit0"
            ), "The ellipse for task 6 should be red because it's on critical path"
