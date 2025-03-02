from typing import AsyncGenerator, Generator

import pytest
from docker.errors import DockerException
from pydantic import HttpUrl
from testcontainers.core.container import DockerContainer  # type:ignore[import-untyped]
from testcontainers.core.network import Network  # type:ignore[import-untyped]
from testcontainers.core.waiting_utils import wait_container_is_ready, wait_for_logs  # type:ignore[import-untyped]

from taskdependencygraph.plotting.kroki import KrokiClient, KrokiConfig

_KROKI_INTERNAL_PORT = 8000


@pytest.fixture(scope="session")
def docker_network() -> Network:
    """Creates a shared Docker network for inter-container communication."""
    try:
        network = Network()
    except DockerException as docker_exception:
        if "Error while fetching server API version" in str(docker_exception):
            raise OSError(
                # pylint:disable=line-too-long
                "For the plotting tests with dot and/or mermaid we use test containers. It seems like Docker Desktop is not running."
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
    kroki = DockerContainer("yuzutech/kroki:0.24.1")
    kroki.with_network(docker_network)
    mermaid = DockerContainer("yuzutech/kroki-mermaid")
    mermaid.with_network(docker_network)
    mermaid.with_network_aliases("mermaid")
    mermaid.start()
    wait_container_is_ready(mermaid)
    kroki.with_env("KROKI_MERMAID_HOST", "mermaid")
    kroki.with_exposed_ports(_KROKI_INTERNAL_PORT)
    kroki.start()
    wait_container_is_ready(kroki)
    wait_for_logs(kroki, "Succeeded in deploying verticle")  # this was just a guess, but it seems to work :)
    port_on_localhost = kroki.get_exposed_port(_KROKI_INTERNAL_PORT)
    yield int(port_on_localhost)
    mermaid.stop()
    kroki.stop()


@pytest.fixture(scope="function")
async def internal_kroki_client(start_kroki_on_localhost: int) -> AsyncGenerator[KrokiClient, None]:
    kroki_config = KrokiConfig(host=HttpUrl(f"http://localhost:{start_kroki_on_localhost}/"))
    kroki_client = KrokiClient(kroki_config)
    yield kroki_client
    await kroki_client.close_session()
