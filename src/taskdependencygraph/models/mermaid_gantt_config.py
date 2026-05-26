"""Configuration model for Mermaid Gantt chart output."""

from pydantic import BaseModel, ConfigDict, Field


class MermaidGanttConfig(BaseModel):
    """Configuration for TaskDependencyGraph.to_mermaid_gantt() output.

    All fields default to the values that were previously hardcoded, so calling
    to_mermaid_gantt() without a config preserves the existing output exactly.

    Configuration for other diagram formats (e.g. DOT/GraphViz) belongs in a
    separate dedicated config class and must not be added here.
    """

    model_config = ConfigDict(frozen=True)

    title: str = Field(
        default="A Gantt Diagram",
        min_length=1,
        description="Chart title, emitted as 'title <value>' in the Mermaid header.",
    )
    date_format: str = Field(
        default="YYYY-MM-DDTHH:mm:SZ",
        min_length=1,
        description=(
            "Mermaid dateFormat string controlling how task start dates are parsed. "
            "See https://mermaid.js.org/syntax/gantt.html#setting-dates"
        ),
    )
    axis_format: str = Field(
        default="%d.%m %H:%M",
        min_length=1,
        description="strftime-style format for x-axis tick labels, emitted as 'axisFormat <value>'.",
    )
    tick_interval: str = Field(
        default="15minute",
        pattern=r"^\d+(millisecond|second|minute|hour|day|week|month)s?$",
        description=(
            "Interval between axis ticks, e.g. '1hour', '30minutes'. "
            "Must be a positive integer followed by a Mermaid time unit "
            "(millisecond, second, minute, hour, day, week, month) with optional trailing 's'. "
            "Emitted as 'tickInterval <value>'. "
            "See https://mermaid.js.org/syntax/gantt.html#setting-an-axis-tick-interval"
        ),
    )
    section_label: str = Field(
        default="Example Stream",
        min_length=1,
        description=(
            "Section header for ungrouped output. When group_by_phase=True, tasks whose "
            "phase field is None are placed under this section."
        ),
    )
    group_by_phase: bool = Field(
        default=False,
        description=(
            "When True, tasks are grouped into Mermaid sections by their phase field. "
            "Tasks with phase=None (including the internal artificial start/end nodes) "
            "are placed under section_label. "
            "Phase groups appear in the order their phase is first encountered "
            "during graph iteration."
        ),
    )


__all__ = ["MermaidGanttConfig"]
