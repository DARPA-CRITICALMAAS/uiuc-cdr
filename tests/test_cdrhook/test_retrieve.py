import os
import json
from dotenv import load_dotenv

import cdrhook.retrieve as rt
from cdrhook.connector import CdrConnector
from cdrhook.cdr_endpoint_schemas import SystemId
from tests.utilities import init_test_log

class TestRetrieveCog:
    cog_id = "78c274e9575d1ac948d55a55265546d711551cdd5cdd53592c9928d502d50700"

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

    def test_retrieve_cog_system_versions(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_system_versions")
        response_data = rt.retrieve_cog_system_versions(self.con, self.cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_system_versions_response.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        # Check if response is not empty
        assert response_data
        log.info("Test passed successfully")

    def test_retrieve_cog_area_extraction(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_area_extraction")
        cog_id = "5a06544690b6611f419f0c6f244776a536ad52915555555555515545c9b1ddb9"
        response_data = rt.retrieve_cog_area_extraction(self.con, cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_area_extraction.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        # Check if response is not empty
        assert response_data
        log.info("Test passed successfully")

    def test_retrieve_cog_area_extraction_by_system_id(self):
        log = init_test_log('TestRetrieveCog/test_retrieve_cog_area_extraction_by_system_id')
        cog_id = "5a06544690b6611f419f0c6f244776a536ad52915555555555515545c9b1ddb9"
        test_system = SystemId(name='uncharted', version='0.0.4')
        response_data = rt.retrieve_cog_area_extraction(self.con, cog_id, system_id=test_system)
        cog_area_extraction = rt.validate_cog_area_extraction_response(response_data)
        # Save Response 
        json_path = 'tests/logs/TestRetrieveCog/test_retrieve_cog_area_extraction_by_system_id.json'
        log.info(f'Saving result to {json_path}')
        with open(json_path, 'w') as fh:
            fh.write(json.dumps(response_data))
        # Check only the requested system data is returned
        assert len(cog_area_extraction) > 0
        for area_system in cog_area_extraction:
            assert area_system.system == test_system.name
            assert area_system.system_version == test_system.version
        log.info('Test passed successfully')

    def test_retrieve_cog_legend_items(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_legend_items")
        response_data = rt.retrieve_cog_legend_items(self.con, self.cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_legend_items.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        # Check if response is not empty
        assert response_data
        log.info("Test passed successfully")

    def test_retrieve_cog_legend_items_by_system_id(self):
        log = init_test_log('TestRetrieveCog/test_retrieve_cog_legend_items_by_system_id')
        test_system = SystemId(name='polymer', version='0.0.1')
        response_data = rt.retrieve_cog_legend_items(self.con, self.cog_id, system_id=test_system)
        cog_legend_items = rt.validate_cog_legend_items_response(response_data)
        # Save Response
        json_path = 'tests/logs/TestRetrieveCog/test_cog_legend_items_by_system_id.json'
        log.info(f'Saving result to {json_path}')
        with open(json_path, 'w') as fh:
            fh.write(json.dumps(response_data))
        # Check only the requested system data is returned
        assert len(cog_legend_items) > 0
        for legend_system in cog_legend_items:
            assert legend_system.system == test_system.name
            assert legend_system.system_version == test_system.version
        log.info('Test passed successfully')

    def test_retrieve_cog_metadata(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_metadata")
        response_data = rt.retrieve_cog_metadata(self.con, self.cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_metadata_response.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        # Check if response is not empty
        assert response_data
        log.info("Test passed successfully")

    def test_retrieve_cog_results(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_results")
        response_data = rt.retrieve_cog_results(self.con, self.cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_results_response.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        # Check if response is not empty
        assert response_data
        log.info("Test passed successfully")

    def test_retrieve_cog_download(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_download")
        response_data = rt.retrieve_cog_download(self.con, self.cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_download_response.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        # Check if response is not empty
        assert response_data
        log.info("Test passed successfully")

class TestValidateCog:
    def test_validate_cog_system_versions_response(self):
        log = init_test_log("TestValidateCog/test_validate_cog_system_versions_response")
        # response_data = rt.retrieve_cog_system_versions(self.con, self.cog_id)
        with open("tests/data/sample_cog_system_versions.json", "r") as fh:
            response_data = json.load(fh)
        # Validate data
        cog_system_versions = rt.validate_cog_system_versions_response(response_data)
        # log.info(f'Validated Data :\n{cog_system_versions.pretty_str()}')
        assert cog_system_versions
        log.info("Test passed successfully")

    def test_validate_cog_area_extraction_response(self):
        log = init_test_log("TestValidateCog/test_validate_cog_area_extraction_response")
        # response_data = rt.retrieve_cog_area_extraction(self.con, 5a06544690b6611f419f0c6f244776a536ad52915555555555515545c9b1ddb9)
        with open("tests/data/sample_cog_area_extraction.json", "r") as fh:
            response_data = json.load(fh)
        # Validate data
        cog_area_extraction = rt.validate_cog_area_extraction_response(response_data)
        # display_msg = [f"{ae.pretty_str()}" for ae in cog_area_extraction]
        # log.info(f"Validated Data :\n{[f'{ae.pretty_str()}' for ae in cog_area_extraction]}")
        assert cog_area_extraction
        log.info("Test passed successfully")

    def test_validate_cog_legend_items_response(self):
        log = init_test_log("TestValidateCog/test_validate_cog_legend_items_response")
        # response_data = rt.retrieve_cog_legend_items(self.con, self.cog_id)
        with open("tests/data/sample_cog_legend.json", "r") as fh:
            response_data = json.load(fh)
        # Validate data
        cog_legend_items = rt.validate_cog_legend_items_response(response_data)
        assert cog_legend_items
        log.info("Test passed successfully")

    def test_validate_cog_metadata_response(self):
        log = init_test_log("TestValidateCog/test_validate_cog_metadata_response")
        # response_data = rt.retrieve_cog_metadata(self.con, self.cog_id)
        with open("tests/data/sample_cog_metadata.json", "r") as fh:
            response_data = json.load(fh)
        # Validate data
        cog_metadata = rt.validate_cog_metadata_response(response_data)
        assert cog_metadata
        log.info("Test passed successfully")

    def test_validate_cog_results_response(self):
        log = init_test_log("TestValidateCog/test_validate_cog_results_response")
        # response_data = rt.retrieve_cog_results(self.con, self.cog_id)
        with open("tests/data/sample_cog_results.json", "r") as fh:
            response_data = json.load(fh)
        # Validate data
        cog_results = rt.validate_cog_results_response(response_data)
        assert cog_results
        log.info("Test passed successfully")

    def test_validate_cog_download_response(self):
        log = init_test_log("TestValidateCog/test_validate_cog_download_response")
        # response_data = rt.retrieve_cog_download(self.con, self.cog_id)
        with open("tests/data/sample_cog_download.json", "r") as fh:
            response_data = json.load(fh)
        # Validate data
        cog_download = rt.validate_cog_download_response(response_data)
        # log.info(f'Validated Data :\n{cog_download.pretty_str()}')
        assert cog_download
        log.info("Test passed successfully")

class TestRetrieveEvent:
    event_id = "uncharted_0.0.1_f2090dc52547330f2b1f0bc7163f19f730ff107f135f226708cf070f250fcca0"
    
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

    def test_retrieve_area_extraction_event(self):
        log = init_test_log("TestRetrieveEvent/test_retrieve_area_extraction_event")
        response_data = rt.retrieve_area_extraction_event(self.con, self.event_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveEvent/test_area_extraction_event.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        # Check if response is not empty
        assert response_data
        log.info("Test passed successfully")

    # def test_validate_area_extraction_event_response(self):
#     log = init_test_log("TestRetrieveEvent/test_validate_area_extraction_event")
#     # response_data = rt.retrieve_area_extraction_event(self.con, self.event_id)
#     with open("tests/data/sample_area_extraction_event.json", "r") as fh:
#         response_data = json.load(fh)
#     area_extraction_event = rt.test_validate_area_extraction_event_response(response_data)
#     assert area_extraction_event
#     log.info("Test passed successfully")