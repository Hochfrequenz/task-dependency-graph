"""
The subpackage 'plotting' converts task dependency graphs to visual representations (images/SVGs).
We use kroki.io to do the plotting for us because this is way more powerful than matplotlib or builtin tools.
But instead of using the online kroki.io service, we host it locally in a docker-container (see docker-compose.yml).
Otherwise, we'd quickly run into rate limits.
"""

from taskdependencygraph.plotting.kroki import KrokiClient, KrokiConfig
from taskdependencygraph.plotting.protocols import DotPlottable, MermaidPlottable

__all__ = ["DotPlottable", "MermaidPlottable", "KrokiClient", "KrokiConfig"]
