"""
Classes and methods to interact with kroki.io
"""

import logging
import uuid
import xml.etree.ElementTree as ET

from aiohttp import ClientConnectorError, ClientResponseError, ClientSession, ClientTimeout
from pydantic import BaseModel, HttpUrl
from yarl import URL

from taskdependencygraph.plotting.protocols import PlotMode
from taskdependencygraph.task_dependency_graph import TaskDependencyGraph

_logger = logging.getLogger(__name__)


class KrokiConfig(BaseModel):
    """
    Configuration to connect with the kroki service
    """

    host: HttpUrl
    """
    host is the base/root URL of the kroki service (e.g. 'http://localhost:8123' or 'https://kroki.io')
    """


def _replace_id_with_svg_id(svg: str) -> str:
    """replaces the ids of all <rect>-tags with 'svg-<id>' to avoid id-clashes in the overall DOM"""
    root = ET.fromstring(svg)
    for rect in root.findall(".//{http://www.w3.org/2000/svg}rect"):
        if "id" in rect.attrib:
            try:
                uuid_id = uuid.UUID(rect.get("id"))  # raises a ValueError if the id is not a valid UUID
                rect.set("id", f"svg-{uuid_id}")
            except ValueError:
                continue
    ET.register_namespace("", "http://www.w3.org/2000/svg")  # removes the annoying "ns0:" prefix
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


class KrokiClient:
    """
    A client to interact with the kroki service
    """

    def __init__(self, config: KrokiConfig):
        """initialize the client with a configuration"""
        self._config = config
        self._session: ClientSession | None = None
        _logger.info("Instantiated KrokiClient with server_url %s", str(self._config.host))

    async def _get_session(self) -> ClientSession:
        """
        returns a client session (that may be reused or newly created)
        reusing the same (threadsafe) session will be faster than re-creating a new session for every request.
        see https://docs.aiohttp.org/en/stable/http_request_lifecycle.html#how-to-use-the-clientsession
        """
        if self._session is None or self._session.closed:
            _logger.info("creating new session")
            self._session = ClientSession(
                timeout=ClientTimeout(60),
                raise_for_status=True,
            )
        else:
            _logger.log(5, "reusing aiohttp session")  # log level 5 is half as "loud" logging.DEBUG
        return self._session

    async def close_session(self) -> None:
        """
        closes the client session
        """
        if self._session is not None and not self._session.closed:
            _logger.info("Closing aiohttp session")
            await self._session.close()
            self._session = None

    async def is_ready(self) -> bool:
        """
        returns true, iff kroki is available
        """
        try:
            simple_svg = await self._plot_dot_as_svg('digraph G{"A";"B";A->B}')
            return simple_svg is not None
        except Exception:  # pylint:disable=broad-except
            _logger.exception("The is_ready check failed of the kroki client failed")
            return False

    async def _plot_dot_as_svg(self, dot_string: str) -> str:
        payload = {"diagram_source": dot_string, "diagram_type": "graphviz", "output_format": "svg"}
        session = await self._get_session()
        request_uuid = uuid.uuid4()
        svg_url = URL(str(self._config.host)) / "graphviz" / "svg"
        _logger.debug("[%s] Send SVG request to kroki service", request_uuid)
        try:
            response = await session.post(svg_url, json=payload)
        except ClientConnectorError:
            _logger.exception("Failed to connect to kroki. Is it actually running at '%s'?", self._config.host)
            raise
        except ClientResponseError as cre:
            if cre.status == 400:
                _logger.warning(
                    "The kroki service returned a 400 Bad Request. Your dot is probably invalid: %s", dot_string
                )
            raise
        _logger.debug("[%s] Received response from kroki service; Status code %i", request_uuid, response.status)
        svg = await response.text()
        return svg

    async def _plot_mermaid_as_svg(self, mermaid_str: str) -> str:
        payload = {"diagram_source": mermaid_str, "diagram_type": "mermaid", "output_format": "svg"}
        session = await self._get_session()
        request_uuid = uuid.uuid4()
        svg_url = URL(str(self._config.host)) / "mermaid" / "svg" % {"html-labels": "true"}
        _logger.debug("[%s] Send SVG request to kroki service", request_uuid)
        try:
            response = await session.post(svg_url, json=payload)
        except ClientConnectorError:
            _logger.exception("Failed to connect to kroki. Is it actually running at '%s'?", self._config.host)
            raise
        except ClientResponseError as cre:
            if cre.status == 400:
                _logger.warning(
                    "The kroki service returned a 400 Bad Request. Your dot is probably invalid: %s", mermaid_str
                )
            raise
        _logger.debug("[%s] Received response from kroki service; Status code %i", request_uuid, response.status)
        response_body = await response.text()
        return _replace_id_with_svg_id(response_body)

    async def plot_as_svg(self, tdg: TaskDependencyGraph, mode: PlotMode = "gantt") -> str:
        """
        returns an XML/SVG string of the task dependency graph
        """
        match mode:
            case "dot":
                dot_string = tdg.to_dot()
                return await self._plot_dot_as_svg(dot_string)
            case "gantt":
                mermaid_gantt_str = tdg.to_mermaid_gantt()
                return await self._plot_mermaid_as_svg(mermaid_gantt_str)
            case _:
                raise ValueError(f"Unknown mode '{mode}'")


__all__ = ["KrokiClient", "KrokiConfig"]
