import pytest


class MockIMAPMail:
    def __init__(self, login_error=None, select_error=None):
        self.login_error = login_error
        self.select_error = select_error
        self.login_called_with = None
        self.select_called_with = None

    def login(self, user, password):
        if self.login_error:
            raise self.login_error
        self.login_called_with = (user, password)

    def select(self, folder):
        if self.select_error:
            raise self.select_error
        self.select_called_with = folder


def test_login_success(monkeypatch):
    mock_mail = MockIMAPMail()

    def mock_imap4_ssl(url):
        assert url == 'imap.gmail.com'
        return mock_mail

    monkeypatch.setattr("src.login.imaplib.IMAP4_SSL", mock_imap4_ssl)

    from src.login import login
    result = login("test@example.com", "password")

    assert result is mock_mail
    assert mock_mail.login_called_with == ("test@example.com", "password")
    assert mock_mail.select_called_with == "Inbox"


def test_login_auth_failure(monkeypatch):
    mock_mail = MockIMAPMail(login_error=Exception("Auth failed"))

    def mock_imap4_ssl(url):
        return mock_mail

    monkeypatch.setattr("src.login.imaplib.IMAP4_SSL", mock_imap4_ssl)

    from src.login import login
    result = login("test@example.com", "wrong_password")

    assert result is None


def test_login_select_inbox_failure(monkeypatch):
    mock_mail = MockIMAPMail(select_error=Exception("No inbox"))

    def mock_imap4_ssl(url):
        return mock_mail

    monkeypatch.setattr("src.login.imaplib.IMAP4_SSL", mock_imap4_ssl)

    from src.login import login
    result = login("test@example.com", "password")

    assert result is None
