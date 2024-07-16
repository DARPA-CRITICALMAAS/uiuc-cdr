import os
from dotenv import load_dotenv

from tests.utilities import init_test_log
from cdrhook.connector import CdrConnector
from tests.data.mock_data import get_mock_connector

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

    def test_repr(self):
        log = init_test_log("TestCDRConnector/test_repr")
        con = get_mock_connector()
        
        con_repr = con.__repr__()
        log.debug(f"Connector repr : {con_repr}")
        # Fields that should be displayed
        assert con.system_name in con_repr
        assert con.system_version in con_repr
        assert str(con.callback_url) in con_repr
        assert con.callback_username in con_repr
        assert con.cdr_url in con_repr
        # Fields that should NOT be displayed
        assert con.callback_password not in con_repr
        assert con.callback_secret not in con_repr
        assert con.token not in con_repr
        assert con.registration not in con_repr
        
        log.info("Test passed successfully")

    def test_str(self):
        log = init_test_log("TestCDRConnector/test_str")
        con = get_mock_connector()
        
        con_str = con.__str__()
        log.debug(f"Connector str : {con_str}")
        # Fields that should be displayed
        assert con.system_name in con_str
        assert con.system_version in con_str
        assert str(con.callback_url) in con_str
        assert con.callback_username in con_str
        assert con.cdr_url in con_str
        # Fields that should NOT be displayed
        assert con.callback_password not in con_str
        assert con.callback_secret not in con_str
        assert con.token not in con_str
        assert con.registration not in con_str
        
        log.info("Test passed successfully")

    def test_del(self):
        log = init_test_log("TestCDRConnector/test_del")
        con = get_mock_connector()  
        con.register()
        del con

        con = get_mock_connector()
        del con
        
        log.info("Test passed successfully")