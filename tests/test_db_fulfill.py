import pytest


class MockCursor:
    def __init__(self):
        self.execute_calls = []
        self.fetchone_result = [999]

    def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))

    def fetchone(self):
        return self.fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class MockConnection:
    def __init__(self):
        self.cursor_instance = MockCursor()

    def cursor(self):
        return self.cursor_instance

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@pytest.fixture
def mock_conn():
    return MockConnection()


def test_save_auction_no_connection():
    from src.db_fulfill import save_auction

    data = {"object": {"id": 1}}
    result = save_auction(data, None)
    assert result is None


def test_save_auction_minimal_data(mock_conn):
    from src.db_fulfill import save_auction

    data = {
        "object": {
            "id": 12345,
            "auctionId": 12345,
            "name": "Test Auction",
            "aiGenerated": True
        }
    }

    save_auction(data, mock_conn)
    assert len(mock_conn.cursor_instance.execute_calls) > 0


def test_save_auction_with_bailiff_data(mock_conn):
    from src.db_fulfill import save_auction

    data = {
        "object": {
            "id": 12345,
            "auctionId": 12345,
            "name": "Test Auction",
            "aiGenerated": False,
            "bailiffData": {
                "bankName": "PKO BP",
                "bankIban": "PL123456789",
                "addressData": {
                    "institutionName": "Komornik Testowy",
                    "address": {
                        "street": "Testowa",
                        "buildingNo": "1",
                        "city": "Warszawa",
                        "zipCode": "00-001"
                    }
                }
            }
        }
    }

    save_auction(data, mock_conn)
    assert len(mock_conn.cursor_instance.execute_calls) >= 2


def test_save_auction_with_address_data(mock_conn):
    from src.db_fulfill import save_auction

    data = {
        "object": {
            "id": 12345,
            "auctionId": 12345,
            "name": "Test Auction",
            "aiGenerated": True
        }
    }

    address_data = {
        "auctionId": 12345,
        "street": "Testowa",
        "buildingNo": "10",
        "city": "Krakow",
        "zipCode": "30-001",
        "country": "Polska"
    }

    save_auction(data, mock_conn, address_data)
    assert len(mock_conn.cursor_instance.execute_calls) >= 2


def test_save_auction_with_attachments(mock_conn):
    from src.db_fulfill import save_auction

    data = {
        "object": {
            "id": 12345,
            "auctionId": 12345,
            "name": "Test Auction",
            "aiGenerated": True,
            "attachments": [
                {"fileName": "photo1.jpg", "fileContent": "base64data"},
                {"fileName": "photo2.jpg", "fileContent": "base64data2"}
            ]
        }
    }

    save_auction(data, mock_conn)
    assert len(mock_conn.cursor_instance.execute_calls) >= 3


def test_save_auction_with_additional_params(mock_conn):
    from src.db_fulfill import save_auction

    data = {
        "object": {
            "id": 12345,
            "auctionId": 12345,
            "name": "Test Auction",
            "aiGenerated": True,
            "additionalParams": {
                "AREA": {"value": 100.5, "format": "SINGLE"},
                "NUMBEROFROOMS": {"value": 4, "format": "SINGLE"}
            }
        }
    }

    save_auction(data, mock_conn)
    assert len(mock_conn.cursor_instance.execute_calls) >= 3


def test_save_auction_attachment_without_filename_skipped(mock_conn):
    from src.db_fulfill import save_auction

    data = {
        "object": {
            "id": 12345,
            "auctionId": 12345,
            "name": "Test Auction",
            "aiGenerated": True,
            "attachments": [
                {"fileName": None, "fileContent": "base64data"},
                {"fileContent": "base64data2"}
            ]
        }
    }

    save_auction(data, mock_conn)
    assert len(mock_conn.cursor_instance.execute_calls) == 1


def test_save_auction_additional_params_list_value(mock_conn):
    from src.db_fulfill import save_auction

    data = {
        "object": {
            "id": 12345,
            "auctionId": 12345,
            "name": "Test Auction",
            "aiGenerated": True,
            "additionalParams": {
                "MEDIA": {"value": ["woda", "prad", "gaz"], "format": "MULTI"}
            }
        }
    }

    save_auction(data, mock_conn)
    assert len(mock_conn.cursor_instance.execute_calls) > 0
