from collections.abc import AsyncGenerator, Generator

import pytest
from docker.errors import DockerException
from pydantic import HttpUrl
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.wait_strategies import HttpWaitStrategy, LogMessageWaitStrategy

from taskdependencygraph.plotting.kroki import KrokiClient, KrokiConfig

_KROKI_INTERNAL_PORT = 8000
_MERMAID_INTERNAL_PORT = 8002


@pytest.fixture(scope="session")
def docker_network() -> Generator[Network, None, None]:
    """Creates a shared Docker network for inter-container communication."""
    try:
        network = Network()
    except DockerException as docker_exception:
        if "Error while fetching server API version" in str(docker_exception):
            raise OSError(
                "For the plotting tests with dot and/or mermaid we use test containers. It seems like Docker Desktop is not running."  # noqa: E501
            ) from docker_exception
        raise
    network.create()
    yield network
    network.remove()


@pytest.fixture(scope="session")
def start_kroki_on_localhost(docker_network: Network) -> Generator[int, None, None]:
    """
    Starts Kroki and Mermaid containers.
    Yields the exposed kroki port.
    """
    kroki = DockerContainer("yuzutech/kroki:0.30.1")
    kroki.with_network(docker_network)
    mermaid = DockerContainer("yuzutech/kroki-mermaid")
    mermaid.with_network(docker_network)
    mermaid.with_network_aliases("mermaid")
    mermaid.with_exposed_ports(_MERMAID_INTERNAL_PORT)
    # the mermaid companion server doesn't log anything on successful startup, but it exposes a /health
    # route that renders a sample diagram, so we use that to know the (headless-Chrome-backed) worker is up
    mermaid.waiting_for(HttpWaitStrategy(_MERMAID_INTERNAL_PORT, path="/health").for_status_code(200))
    mermaid.start()
    kroki.with_env("KROKI_MERMAID_HOST", "mermaid")
    kroki.with_exposed_ports(_KROKI_INTERNAL_PORT)
    kroki.waiting_for(
        LogMessageWaitStrategy("Succeeded in deploying verticle")
    )  # this was just a guess, but it seems to work :)
    kroki.start()
    port_on_localhost = kroki.get_exposed_port(_KROKI_INTERNAL_PORT)
    yield int(port_on_localhost)
    mermaid.stop()
    kroki.stop()


@pytest.fixture(scope="function")
async def kroki_client(start_kroki_on_localhost: int) -> AsyncGenerator[KrokiClient, None]:
    kroki_config = KrokiConfig(host=HttpUrl(f"http://localhost:{start_kroki_on_localhost}/"))
    kroki_client = KrokiClient(kroki_config)
    yield kroki_client
    await kroki_client.close_session()
