import os
import json
from dotenv import load_dotenv

import cdrhook.retrieve as rt
from cdrhook.connector import CdrConnector
from cdrhook.cdr_endpoint_schemas import SystemId, CogSystemVersionsSchema, CogDownloadSchema
from cdr_schemas.cdr_responses.area_extractions import AreaExtractionResponse
from cdr_schemas.cdr_responses.legend_items import LegendItemResponse
from cdr_schemas.cdr_responses.cogs import CogMeta
from cdr_schemas.map_results import MapResults
from tests.utilities import init_test_log, dumps_list

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
            fh.write(response_data.model_dump_json())
        # Check is response is valid
        assert isinstance(response_data, CogSystemVersionsSchema)
        log.info("Test passed successfully")

    def test_retrieve_cog_area_extraction(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_area_extraction")
        cog_id = "5a06544690b6611f419f0c6f244776a536ad52915555555555515545c9b1ddb9"

        response_data = rt.retrieve_cog_area_extraction(self.con, cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_area_extraction.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(dumps_list(response_data))
        # Check is response is valid
        assert isinstance(response_data[0], AreaExtractionResponse)
        log.info("Test passed successfully")

    def test_retrieve_cog_area_extraction_by_system_id(self):
        log = init_test_log('TestRetrieveCog/test_retrieve_cog_area_extraction_by_system_id')
        cog_id = "5a06544690b6611f419f0c6f244776a536ad52915555555555515545c9b1ddb9"
        test_system = SystemId(name='uncharted-area', version='0.0.4')

        response_data = rt.retrieve_cog_area_extraction(self.con, cog_id, system_id=test_system)
        # Save Response 
        json_path = 'tests/logs/TestRetrieveCog/test_retrieve_cog_area_extraction_by_system_id.json'
        log.info(f'Saving result to {json_path}')
        with open(json_path, 'w') as fh:
            fh.write(dumps_list(response_data))
        # Check only the requested system data is returned
        for area_system in response_data:
            assert area_system.system == test_system.name
            assert area_system.system_version == test_system.version
        log.info('Test passed successfully')

    def test_retrieve_cog_legend_items(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_legend_items")
        response_data = rt.retrieve_cog_legend_items(self.con, self.cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_legend_items.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, 'w') as fh:
            fh.write(dumps_list(response_data))
        # Check is response is valid
        assert isinstance(response_data[0], LegendItemResponse)
        log.info("Test passed successfully")

    def test_retrieve_cog_legend_items_by_system_id(self):
        log = init_test_log('TestRetrieveCog/test_retrieve_cog_legend_items_by_system_id')
        test_system = SystemId(name='polymer', version='0.0.1')
        response_data = rt.retrieve_cog_legend_items(self.con, self.cog_id, system_id=test_system, validated='true')
        # Save Response
        json_path = 'tests/logs/TestRetrieveCog/test_cog_legend_items_by_system_id.json'
        log.info(f'Saving result to {json_path}')
        with open(json_path, 'w') as fh:
            fh.write(dumps_list(response_data))
        # Check only the requested system data is returned
        for legend_system in response_data:
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
            fh.write(response_data.model_dump_json())
        # Check is response is valid
        assert isinstance(response_data, CogMeta)
        log.info("Test passed successfully")

    def test_retrieve_cog_results(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_results")
        cog_results = rt.retrieve_cog_results(self.con, self.cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_results_response.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, 'w') as fh:
            fh.write(dumps_list(cog_results))
        # Check if response is not empty
        for result in cog_results:
            assert isinstance(result, MapResults)
        log.info("Test passed successfully")

    def test_retrieve_cog_download(self):
        log = init_test_log("TestRetrieveCog/test_retrieve_cog_download")
        response_data = rt.retrieve_cog_download(self.con, self.cog_id)
        # Save Response
        json_path = "tests/logs/TestRetrieveCog/test_cog_download_response.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(response_data.model_dump_json())
        # Check if response is not empty
        assert isinstance(response_data, CogDownloadSchema)
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