from typing import Generator

from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.waiting_utils import wait_container_is_ready, wait_for

_MERMAID_INTERNAL_PORT = 8124
_KROKI_INTERNAL_PORT = 8000


from typing import AsyncGenerator

import pytest
from pydantic_core import Url


@pytest.fixture(scope="session")
def docker_network() -> Network:
    """Creates a shared Docker network for inter-container communication."""
    network = Network()
    network.create()
    yield network
    network.remove()


from taskdependencygraph.plotting.kroki import KrokiClient, KrokiConfig


@pytest.fixture(scope="session")
def start_kroki_on_localhost(docker_network: Network) -> Generator[int, None, None]:
    """
    Starts Kroki and Mermaid containers.
    Yields the exposed kroki port.
    """
    kroki = DockerContainer("yuzutech/kroki:0.24.1")
    mermaid = DockerContainer("yuzutech/kroki-mermaid")
    kroki.with_network(docker_network)
    mermaid.with_exposed_ports(_MERMAID_INTERNAL_PORT)
    mermaid.with_network(docker_network)
    kroki.with_exposed_ports(_KROKI_INTERNAL_PORT)
    mermaid.start()
    wait_container_is_ready(mermaid)
    mermaid_port_on_localhost = mermaid.get_exposed_port(_MERMAID_INTERNAL_PORT)
    kroki.with_env("KROKI_MERMAID_HOST", f"{mermaid.get_container_host_ip()}:{mermaid_port_on_localhost}")
    kroki.start()
    wait_container_is_ready(kroki)
    port_on_localhost = kroki.get_exposed_port(_KROKI_INTERNAL_PORT)
    yield int(port_on_localhost)
    mermaid.stop()
    kroki.stop()


@pytest.fixture(scope="function")
async def internal_kroki_client(start_kroki_on_localhost: int) -> AsyncGenerator[KrokiClient, None]:
    kroki_config = KrokiConfig(host=Url(f"http://localhost:{start_kroki_on_localhost}/"))
    kroki_client = KrokiClient(kroki_config)
    yield kroki_client
    await kroki_client.close_session()
