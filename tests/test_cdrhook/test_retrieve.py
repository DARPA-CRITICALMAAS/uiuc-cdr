import os
import json
from dotenv import load_dotenv

import cdrhook.retrieve as rt
from cdrhook.connector import CdrConnector
from tests.utilities import init_test_log
from cdr_schemas.map_results import MapResults
from cdr_schemas.feature_results import FeatureResults
from cdrhook.cdr_endpoint_schemas import (
    AreaExtractionsEndpoint,
    LegendItemsEndpoint,
    SystemId,
    MetadataEndpoint,
)

class TestRetrieve:
    cog_id = "78c274e9575d1ac948d55a55265546d711551cdd5cdd53592c9928d502d50700"
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

    def test_retrieve_cog_metadata(self):
        log = init_test_log("TestRetrieve/test_retrieve_cog_metadata")
        response_data = rt.retrieve_cog_metadata(self.con, self.cog_id)
        json_path = "tests/logs/TestRetrieve/test_cog_metadata.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        assert response_data
        log.info("Test passed successfully")

    def test_validate_cog_metadata(self):
        log = init_test_log("TestRetrieve/test_validate_cog_metadata")
        response_data = rt.retrieve_cog_metadata(self.con, self.cog_id)
        cog_metadata = rt.validate_endpoint(response_data, MetadataEndpoint)
        assert cog_metadata
        log.info("Test passed successfully")

    def test_retrieve_cog_results(self):
        log = init_test_log("TestRetrieve/test_retrieve_cog_results")
        response_data = rt.retrieve_cog_results(self.con, self.cog_id)
        json_path = "tests/logs/TestRetrieve/test_cog_results.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        log.info("Test passed successfully")

    def test_validate_cog_results(self):
        log = init_test_log("TestRetrieve/test_validate_cog_results")
        # response_data = rt.retrieve_cog_results(self.con, self.cog_id)
        with open("tests/logs/TestRetrieve/test_cog_results.json", "r") as fh:
            response_data = json.load(fh)
            for er in response_data["extraction_results"]:
                er["point_feature_results"] = []
        cog_results = rt.validate_endpoint(response_data, MapResults)
        assert cog_results
        log.info("Test passed successfully")

    def test_retrieve_cog_system_versions(self):
        log = init_test_log("TestRetrieve/test_retrieve_cog_system_versions")
        response_data = rt.retrieve_cog_system_versions(self.con, self.cog_id)
        json_path = "tests/logs/TestRetrieve/test_cog_system_versions.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        log.info("Test passed successfully")

    def test_validate_cog_system_versions(self):
        log = init_test_log("TestRetrieve/test_validate_cog_system_versions")
        response_data = rt.retrieve_cog_system_versions(self.con, self.cog_id)
        for r in response_data:
            cog_system_versions = SystemId(name=r[0], version=r[1])
            # cog_system_versions = rt.validate_endpoint(r, SystemVersionsEndpoint)
        assert cog_system_versions
        log.info("Test passed successfully")

    def test_retrieve_cog_area_extraction(self):
        log = init_test_log("TestRetrieve/test_retrieve_cog_area_extraction")
        cog_id = "5a06544690b6611f419f0c6f244776a536ad52915555555555515545c9b1ddb9"
        response_data = rt.retrieve_cog_area_extraction(self.con, cog_id)
        json_path = "tests/logs/TestRetrieve/test_cog_area_extraction.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        log.info("Test passed successfully")

    def test_validate_cog_area_extraction(self):
        log = init_test_log("TestRetrieve/test_validate_cog_area_extraction")
        cog_id = "5a06544690b6611f419f0c6f244776a536ad52915555555555515545c9b1ddb9"
        response_data = rt.retrieve_cog_area_extraction(self.con, cog_id)
        for r in response_data:
            cog_area_extraction = rt.validate_endpoint(r, AreaExtractionsEndpoint)
        assert cog_area_extraction
        log.info("Test passed successfully")

    # def test_retrieve_cog_area_extraction_by_system_id(self):
    #     log = init_test_log('TestRetrieve/test_retrieve_cog_area_extraction_by_system_id')
    #     json_data = rt.retrieve_cog_area_extraction(self.con, self.cog_id, system_id=SystemId('polymer', '0.0.1'))
    #     json_path = 'tests/logs/TestRetrieve/test_retrieve_cog_area_extraction_by_system_id.json'
    #     log.info(f'Saving result to {json_path}')
    #     with open(json_path, 'w') as fh:
    #         fh.write(json.dumps(json_data))
    #     log.info('Test passed successfully')

    def test_retrieve_cog_legend_items(self):
        log = init_test_log("TestRetrieve/test_retrieve_cog_legend_items")
        response_data = rt.retrieve_cog_legend_items(self.con, self.cog_id)
        json_path = "tests/logs/TestRetrieve/test_cog_legend_items.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        log.info("Test passed successfully")

    def test_validate_cog_legend_items(self):
        log = init_test_log("TestRetrieve/test_validate_cog_legend_items")
        response_data = rt.retrieve_cog_legend_items(self.con, self.cog_id)
        for r in response_data:
            cog_legend_items = rt.validate_endpoint(r, LegendItemsEndpoint)
        assert cog_legend_items
        log.info("Test passed successfully")

    # def test_retrieve_cog_legend_items_by_system_id(self):
    #     log = init_test_log('TestRetrieve/test_retrieve_cog_legend_items_by_system_id')
    #     json_data = rt.retrieve_cog_legend_items(self.con, self.cog_id, system_id=SystemId('polymer', '0.0.1'))
    #     json_path = 'tests/logs/TestRetrieve/test_cog_legend_items_by_system_id.json'
    #     log.info(f'Saving result to {json_path}')
    #     with open(json_path, 'w') as fh:
    #         fh.write(json.dumps(json_data))
    #     log.info('Test passed successfully')

    def test_retrieve_area_extraction_event(self):
        log = init_test_log("TestRetrieve/test_retrieve_area_extraction_event")
        response_data = rt.retrieve_area_extraction_event(self.con, self.event_id)
        json_path = "tests/logs/TestRetrieve/test_area_extraction_event.json"
        log.info(f"Saving result to {json_path}")
        with open(json_path, "w") as fh:
            fh.write(json.dumps(response_data))
        log.info("Test passed successfully")

    def test_validate_area_extraction_event(self):
        log = init_test_log("TestRetrieve/test_validate_area_extraction_event")
        response_data = rt.retrieve_area_extraction_event(self.con, self.event_id)
        for r in response_data:
            area_extraction_event = rt.validate_endpoint(r, FeatureResults)
        assert area_extraction_event
        log.info("Test passed successfully")

    def teardown_class(self):
        self.con.unregister()
