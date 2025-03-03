"""
interface like descriptions for any kind of plotting "client" library
"""

from typing import Literal, Protocol

PlotMode = Literal["dot", "gantt"]


class DotPlottable(Protocol):
    """
    something that can be plotted using Dot/GraphViz
    """

    def to_dot(self) -> str:
        """
        returns the dot-representation of this object as plain string
        """


class MermaidPlottable(Protocol):
    """
    something that can be plotted using Mermaid
    """

    def to_mermaid_gantt(self) -> str:
        """
        returns the mermaid-gantt chart representation of this object as plain string
        """


class Plotter(Protocol):
    """
    a plotter is something that converts a task dependency graph to a visual representation
    """

    async def plot_as_svg(self, graph: MermaidPlottable | DotPlottable, mode: PlotMode) -> str:
        """
        Plots something plottable as SVG; returns the SVG as XML string
        """


__all__ = ["DotPlottable", "MermaidPlottable", "Plotter"]
