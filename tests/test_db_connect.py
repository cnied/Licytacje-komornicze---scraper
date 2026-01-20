import pytest
from psycopg2 import OperationalError, Error


class MockConnection:
    pass


def test_db_login_success(monkeypatch):
    mock_conn = MockConnection()

    def mock_connect(**kwargs):
        return mock_conn

    monkeypatch.setattr("src.db_connect.psycopg2.connect", mock_connect)

    from src.db_connect import db_login
    conn, error = db_login()

    assert conn is mock_conn
    assert error is None


def test_db_login_operational_error(monkeypatch):
    def mock_connect(**kwargs):
        raise OperationalError("Connection refused")

    monkeypatch.setattr("src.db_connect.psycopg2.connect", mock_connect)

    from src.db_connect import db_login
    conn, error = db_login()

    assert conn is None
    assert isinstance(error, OperationalError)


def test_db_login_generic_error(monkeypatch):
    def mock_connect(**kwargs):
        raise Error("Generic database error")

    monkeypatch.setattr("src.db_connect.psycopg2.connect", mock_connect)

    from src.db_connect import db_login
    conn, error = db_login()

    assert conn is None
    assert isinstance(error, Error)
