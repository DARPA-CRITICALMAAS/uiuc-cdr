from cdrhook.connector import CdrConnector


class MockConnector(CdrConnector):
    # override
    def register(self):
        return "12345"

    # override
    def unregister(self):
        return

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def get_mock_connector():
    con = MockConnector(
        system_name="mock_connector",
        system_version="0.1",
        token="my_super_secret_mock_token_12345",
        callback_url="https://mockurl.org/",
        callback_secret="my_super_secret_mock_secret_54321",
        callback_username="mock_username",
        callback_password="password_99999",
        registration="my_super_secret_mock_registration_67890"
    )
    return con
