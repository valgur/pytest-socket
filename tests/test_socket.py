# -*- coding: utf-8 -*-
import pytest
from pytest_socket import enable_socket


@pytest.fixture(autouse=True)
def reenable_socket():
    # The tests can leave the socket disabled in the global scope.
    # Fix that by automatically re-enabling it after each test
    yield
    enable_socket()


def assert_socket_blocked(result):
    result.stdout.fnmatch_lines("""
        *SocketBlockedError: A test tried to use socket.socket.*
    """)


def test_socket_enabled_by_default(testdir):
    testdir.makepyfile("""
        import socket
        
        def test_socket():
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """)
    result = testdir.runpytest("--verbose")
    result.assert_outcomes(1, 0, 0)
    with pytest.raises(Exception):
        assert_socket_blocked(result)


def test_global_disable_via_fixture(testdir):
    testdir.makepyfile("""
        import pytest
        import pytest_socket
        import socket

        @pytest.fixture(autouse=True)
        def disable_socket_for_all():
            pytest_socket.disable_socket()

        def test_socket():
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """)
    result = testdir.runpytest("--verbose")
    result.assert_outcomes(0, 0, 1)
    assert_socket_blocked(result)


def test_global_disable_via_cli_flag(testdir):
    testdir.makepyfile("""
        import socket

        def test_socket():
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """)
    result = testdir.runpytest("--verbose", "--disable-socket")
    result.assert_outcomes(0, 0, 1)
    assert_socket_blocked(result)


def test_global_disable_via_config(testdir):
    testdir.makepyfile("""
        import socket

        def test_socket():
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """)
    testdir.makeini("""
        [pytest]
        addopts = --disable-socket
    """)
    result = testdir.runpytest("--verbose")
    result.assert_outcomes(0, 0, 1)
    assert_socket_blocked(result)


def test_disable_socket_marker(testdir):
    testdir.makepyfile("""
        import pytest
        import socket
        
        @pytest.mark.disable_socket
        def test_socket():
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """)
    result = testdir.runpytest("--verbose")
    result.assert_outcomes(0, 0, 1)
    assert_socket_blocked(result)


def test_enable_socket_marker(testdir):
    testdir.makepyfile("""
        import pytest
        import socket
        
        @pytest.mark.enable_socket
        def test_socket():
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """)
    result = testdir.runpytest("--verbose", "--disable-socket")
    result.assert_outcomes(0, 0, 1)
    assert_socket_blocked(result)


def test_urllib_succeeds_by_default(testdir):
    testdir.makepyfile("""
        try:
            from urllib.request import urlopen
        except ImportError:
            from urllib2 import urlopen
        
        def test_disable_socket_urllib():
            assert urlopen('https://httpbin.org/get').getcode() == 200
    """)
    result = testdir.runpytest("--verbose")
    result.assert_outcomes(1, 0, 0)


def test_enabled_urllib_succeeds(testdir):
    testdir.makepyfile("""
        import pytest
        import pytest_socket
        try:
            from urllib.request import urlopen
        except ImportError:
            from urllib2 import urlopen

        @pytest.mark.enable_socket
        def test_disable_socket_urllib():
            assert urlopen('https://httpbin.org/get').getcode() == 200
    """)
    result = testdir.runpytest("--verbose", "--disable-socket")
    result.assert_outcomes(0, 0, 1)
    assert_socket_blocked(result)


def test_disabled_urllib_fails(testdir):
    testdir.makepyfile("""
        import pytest
        try:
            from urllib.request import urlopen
        except ImportError:
            from urllib2 import urlopen

        @pytest.mark.disable_socket
        def test_disable_socket_urllib():
            assert urlopen('https://httpbin.org/get').getcode() == 200
    """)
    result = testdir.runpytest("--verbose")
    result.assert_outcomes(0, 0, 1)
    assert_socket_blocked(result)


def test_double_call_does_nothing(testdir):
    testdir.makepyfile("""
        import pytest
        import pytest_socket
        import socket
        
        def test_double_enabled():
            pytest_socket.enable_socket()
            pytest_socket.enable_socket()
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
        def test_double_disabled():
            pytest_socket.disable_socket()
            pytest_socket.disable_socket()
            with pytest.raises(pytest_socket.SocketBlockedError):
                socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
        def test_disable_enable():
            pytest_socket.disable_socket()
            pytest_socket.enable_socket()
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """)
    result = testdir.runpytest("--verbose")
    result.assert_outcomes(3, 0, 0)
    with pytest.raises(Exception):
        assert_socket_blocked(result)


def test_socket_enabled_fixture(testdir, socket_enabled):
    testdir.makepyfile("""
        import socket
        def test_socket_enabled(socket_enabled):
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """)
    result = testdir.runpytest("--verbose")
    result.assert_outcomes(1, 0, 0)
    with pytest.raises(Exception):
        assert_socket_blocked(result)


def test_mix_and_match(testdir, socket_enabled):
    testdir.makepyfile("""
        import socket

        def test_socket1():
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        def test_socket_enabled(socket_enabled):
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        def test_socket2():
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    """)
    result = testdir.runpytest("--verbose", "--disable-socket")
    result.assert_outcomes(1, 0, 2)
