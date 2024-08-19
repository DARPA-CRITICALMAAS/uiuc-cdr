import os
import json
from dotenv import load_dotenv

from cdrhook.server import process_cog
from cdrhook.connector import CdrConnector
from tests.utilities import init_test_log

class TestCallbacks:
    cog_id = "78c274e9575d1ac948d55a55265546d711551cdd5cdd53592c9928d502d50700"
    #cog_id = "5a06544690b6611f419f0c6f244776a536ad52915555555555515545c9b1ddb9"
    def setup_class(self):
        load_dotenv()
        system_name = "ncsa_test"
        system_version = "0.1"
        token = os.getenv("CDR_TOKEN")
        callback_url = "https://criticalmaas.ncsa.illinois.edu"
        self.con = CdrConnector(
            system_name=system_name,
            system_version=system_version,
            token=token,
            callback_url=callback_url,
        )
        self.con.register()

    def teardown_class(self):
        self.con.unregister()

    def test_process_cog(self):
        log = init_test_log("TestCallbacks/test_process_cog")
        config = {}
        config["mode"] = 'test'
        config["prefix"] = os.getenv("PREFIX")
        config["callback_url"] = 'http://fakeurl.com'
        config['systems'] = {'area' : ['uncharted-area'], 'legend' : ['polymer']}
        with open("cdrhook/models.json", "r") as f:
            config["models"] = json.load(f)

        process_cog(self.con, self.cog_id, config_parm=config)
        log.info("Test passed successfully")
