"""Regression guard: unit tests must never reach external model services."""

import socket

import pytest
from pytest_socket import SocketBlockedError


@pytest.mark.parametrize("family", [socket.AF_INET, socket.AF_INET6])
def test_internet_sockets_are_disabled(family):
    with pytest.raises(SocketBlockedError):
        socket.socket(family, socket.SOCK_STREAM)