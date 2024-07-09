import os
from dotenv import load_dotenv

from tests.utilities import init_test_log
from cdrhook.connector import CdrConnector

load_dotenv()


class TestCDRConnector:
    system_name = "ncsa_test"
    system_version = "0.1"
    token = os.getenv("CDR_TOKEN")
    callback_url = "https://criticalmaas.ncsa.illinois.edu/"

    def test_constructor(self):
        log = init_test_log("TestCDRConnector/test_constructor")
        con = CdrConnector(
            system_name=self.system_name,
            system_version=self.system_version,
            token=self.token,
            callback_url=self.callback_url,
        )

        log.info(f"Connector : {con.__dict__}")
        assert con.system_name == self.system_name
        assert con.system_version == self.system_version
        assert con.token == self.token
        assert str(con.callback_url) == self.callback_url
        log.info("Test passed successfully")

    def test_registration(self):
        log = init_test_log("TestCDRConnector/test_registration")
        con = CdrConnector(
            system_name=self.system_name,
            system_version=self.system_version,
            token=self.token,
            callback_url=self.callback_url,
        )
        con.register()
        assert con.registration is not None
        con.unregister()
        assert con.registration is None
        log.info("Test passed successfully")
