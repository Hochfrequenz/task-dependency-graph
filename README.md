[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python Versions (officially) supported](https://img.shields.io/pypi/pyversions/taskdependencygraph.svg)
![Pypi status badge](https://img.shields.io/pypi/v/taskdependencygraph)

# Task Dependency Graph

Task Dependency Graph is a Python package that allows to model tasks and dependencies between tasks as a directed graph.
It also supports visualizing the graph with [dot](https://graphviz.org/docs/layouts/dot/) for a graph-like view
or [mermaid](https://mermaid.js.org/) for Gantt charts.

The package is built on [networkx](https://networkx.org/) and under the hood the task dependency graph is just a
networkx [DiGraph](https://networkx.org/documentation/stable/reference/classes/digraph.html).
For visualization, it uses GraphViz via [kroki](https://kroki.io/) (in a Docker container).

## Example / How to use

Install the package from [PyPI](https://pypi.org/project/taskdependencygraph/)

```bash
pip install taskdependencygraph
```

Imagine the following scenario:

You and your partner are invited to a birthday party.
You promised to bring a cake.
Baking the cake and the recipe can be divided into atomic tasks, all of which have a duration.
Those are the **nodes** of the task dependency graph (TDG).

Tasks are created like this:

```python
import uuid
from datetime import timedelta

from taskdependencygraph.models import TaskNode

my_task = TaskNode(
    id=uuid.uuid4(),  # boilerplate only, but you need the ID to find nodes in your graph later on
    name="Shop groceries",  # human readable description
    external_id="some unique string",  # technical ID for those who don't like uuids ;)
    planned_duration=timedelta(minutes=15)  # how long it probably takes
    # You may also add an assignees or an earliest_possible_start
    # (The latter is useful, when e.g. the supermarket opens at 7am and you cannot shop groceries before,
    # even if you were awake and have nothing else todo.)
)
```

The tasks depend on each other:
You cannot prepare the cake without buying the ingredients first.
You cannot decorate the cake before you've made it.
Which task has which mandatory predecessor tasks is defined in task dependencies.
Those are the **edges** of our task dependency graph.

Task dependencies are created like this:

```python
import uuid

from taskdependencygraph.models import TaskDependencyEdge, TaskNode

shopping_groceries = TaskNode(...)
mixing_flour_and_sugar = TaskNode(...)
baking_in_the_oven = TaskNode(...)

buy_ingredients_before_mixing_them = TaskDependencyEdge(
    id=uuid.uuid4(),  # boilerplate
    predecessor_task=shopping_groceries.id,
    successor_task=mixing_flour_and_sugar.id
)
mix_ingredients_before_baking_the_cake = TaskDependencyEdge(
    id=uuid.uuid4(),  # boilerplate
    predecessor_task=mixing_flour_and_sugar.id,
    successor_task=baking_in_the_oven.id
)
```

The graph is made out of tasks (nodes), task dependencies (edges) and a start datetime.

```python
from datetime import datetime, UTC

from taskdependencygraph import TaskDependencyGraph
from taskdependencygraph.models import TaskNode, TaskDependencyEdge

# nodes
shopping_groceries = TaskNode(...)
mixing_flour_and_sugar = TaskNode(...)
baking_in_the_oven = TaskNode(...)

# edges
buy_ingredients_before_mixing_them = TaskDependencyEdge(...)
mix_ingredients_before_baking_the_cake = TaskDependencyEdge(...)

# graph
tdg = TaskDependencyGraph(
    task_list=[shopping_groceries, mixing_flour_and_sugar, baking_in_the_oven],
    dependency_list=[buy_ingredients_before_mixing_them, mix_ingredients_before_baking_the_cake],
    starting_time_of_run=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
)
```

Now you can

* calculate at which time which task is scheduled to start depending on which predecessors it has,
* find out which tasks are 'critical' in sense that if they're delayed, then the finishing time of the last node is also
  delayed,
* assign persons to tasks and check if any person has more than one task assigned at a time.

Find a complete working example in [the demo unittest](unittests/test_demonstration.py).
This demo test is also the basis for the following visualization examples.

## Visualization with Kroki

You can visualize the dependencies either as rather simple technical graph or as Gantt chart, when you start kroki in a
docker container:

```yaml
# docker-compose.yaml
services:
  kroki: # see https://docs.kroki.io/kroki/setup/use-docker-or-podman/#_run_multiple_kroki_containers_together
    image: yuzutech/kroki:0.24.1
    depends_on:
      - mermaid
    environment:
      - KROKI_MERMAID_HOST=mermaid
    ports:
      - "8123:8000"
  mermaid:
    image: yuzutech/kroki-mermaid
# run
# docker-compose up -d
# and kroki is ready at localhost:8123
```

```python
import asyncio

from taskdependencygraph import TaskDependencyGraph
from taskdependencygraph.plotting import KrokiClient, KrokiConfig


async def plot_a_graph() -> None:
    tdg = TaskDependencyGraph(...)  # with all nodes and edges and stuff

    config = KrokiConfig(host="http://localhost:8123")  # w/o docker, you may also use kroki.io, but it's rate limited
    kroki_client = KrokiClient(config=config)

    await kroki_client.plot_as_svg(tdg, mode="gantt")  # or mode="dot"


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(plot_a_graph())
```

The result may look like this:

### Gantt Chart (Mermaid)

![A Gantt chart](unittests/baking_a_cake_gantt.svg)

The tasks marked in red mark the critical path on which delays affect the finishing time.
The 🔶 are milestones which mark important moments in your project (often you want to have a group of tasks like '
Shopping' done before starting with the next step, even though there's no "real" dependency between e.g. Cake Base and
buying the strawberries.)
The Gantt chart is useful to get an overview of your project and to identify which tasks are crucial.

### Raw Graph ("dot" engine)

![](unittests/baking_a_cake_dot.svg)

The raw graph helps you to understand the tasks and dependencies setup in a not so shiny but verbose fashion.

## Storing the Graph in a Database
You can store the nodes and edges on a database.
We suggest to just use two tables: One for the edges, one for the nodes.
You can even add trigger-based [DB constraints to prevent loops in the graph](https://gist.github.com/hf-kklein/49f6d05bd29ca850e33f5ccff3e66469) which are faster than you might guess, even for hundreds of tasks.

## Maintainers/ Further Development / Professional Support
This library was built for and then cut out of a mainly internal project by [@hf-crings](https://github.com/hf-crings), [@OLILHR](https://github.com/OLILHR), [@hf-sheese](https://github.com/hf-sheese) and [@hf-kklein](https://github.com/hf-kklein), but we decided to publish it, because it might be useful to someone.
This is why some things are hardcoded here and there and why some features might seem unintuitive at first glance.

We at Hochfrequenz also built a SQLAlchemy+FastAPI+htmx web application around this library in which you can plan and schedule time-critical tasks and projects in the browser.
It's ready to use, but not pretty enough to publish it yet ;)
Just ping us if interested.
