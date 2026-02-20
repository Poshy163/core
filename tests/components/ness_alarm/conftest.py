"""Test fixtures for ness_alarm."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.ness_alarm.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT

from tests.common import MockConfigEntry


@pytest.fixture
def mock_nessclient() -> Generator[MagicMock]:
    """Mock the nessclient Client constructor.

    Replaces nessclient.Client with a MagicMock whose return value
    has AsyncMock methods matching the real Client interface.
    """
    with patch("homeassistant.components.ness_alarm.Client", autospec=True) as mock_cls:
        client = mock_cls.return_value
        client.panic = AsyncMock()
        client.disarm = AsyncMock()
        client.arm_away = AsyncMock()
        client.arm_home = AsyncMock()
        client.aux = AsyncMock()
        client.keepalive = AsyncMock()
        client.update = AsyncMock()
        client.close = AsyncMock()
        client.on_zone_change = MagicMock()
        client.on_state_change = MagicMock()
        yield client


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
        },
    )


@pytest.fixture
def mock_client() -> Generator[AsyncMock]:
    """Mock the nessclient Client for config flow tests."""
    with patch(
        "homeassistant.components.ness_alarm.config_flow.Client",
        return_value=AsyncMock(),
    ) as mock:
        yield mock.return_value


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock async_setup_entry."""
    with patch(
        "homeassistant.components.ness_alarm.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def post_connection_delay() -> Generator[None]:
    """Mock POST_CONNECTION_DELAY to 0 for faster tests."""
    with patch(
        "homeassistant.components.ness_alarm.config_flow.POST_CONNECTION_DELAY",
        0,
    ):
        yield
