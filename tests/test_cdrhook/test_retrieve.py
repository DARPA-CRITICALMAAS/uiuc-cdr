import os
import json
from dotenv import load_dotenv

import cdrhook.retrieve as rt
from cdrhook.cdr_types import SystemId
from cdrhook.connector import CdrConnector
from tests.utilities import init_test_log

class TestRetrieve:
    cog_id = '78c274e9575d1ac948d55a55265546d711551cdd5cdd53592c9928d502d50700'

    def setup_class(self):
        load_dotenv()
        system_name = 'ncsa_test'
        system_version = '0.1'
        token = os.getenv('CDR_TOKEN')
        callback_url = 'https://criticalmaas.ncsa.illinois.edu'
        self.con = CdrConnector(system_name=system_name, system_version=system_version, token=token, callback_url=callback_url)
        self.con.register()

    def test_retrieve_cog_metadata(self):
        log = init_test_log('TestRetrieve/test_retrieve_cog_metadata')
        json_data = rt.retrieve_cog_metadata(self.con, self.cog_id)
        json_path = 'tests/logs/TestRetrieve/test_cog_metadata.json'
        log.info(f'Saving result to {json_path}')
        with open(json_path, 'w') as fh:
            fh.write(json.dumps(json_data))
        log.info('Test passed successfully')

    def test_retrieve_cog_results(self):
        log = init_test_log('TestRetrieve/test_retrieve_cog_results')
        json_data = rt.retrieve_cog_results(self.con, self.cog_id)
        json_path = 'tests/logs/TestRetrieve/test_cog_results.json'
        log.info(f'Saving result to {json_path}')
        with open(json_path, 'w') as fh:
            fh.write(json.dumps(json_data))
        log.info('Test passed successfully')

    def test_retrieve_cog_system_versions(self):
        log = init_test_log('TestRetrieve/test_retrieve_cog_system_versions')
        json_data = rt.retrieve_cog_system_versions(self.con, self.cog_id)
        json_path = 'tests/logs/TestRetrieve/test_cog_system_versions.json'
        log.info(f'Saving result to {json_path}')
        with open(json_path, 'w') as fh:
            fh.write(json.dumps(json_data))
        log.info('Test passed successfully')
    
    def test_retrieve_cog_area_extraction(self):
        log = init_test_log('TestRetrieve/test_retrieve_cog_area_extraction')
        json_data = rt.retrieve_cog_area_extraction(self.con, self.cog_id)
        json_path = 'tests/logs/TestRetrieve/test_cog_area_extraction.json'
        log.info(f'Saving result to {json_path}')
        with open(json_path, 'w') as fh:
            fh.write(json.dumps(json_data))
        log.info('Test passed successfully')

    # def test_retrieve_cog_area_extraction_by_system_id(self):
    #     log = init_test_log('TestRetrieve/test_retrieve_cog_area_extraction_by_system_id')
    #     json_data = rt.retrieve_cog_area_extraction(self.con, self.cog_id, system_id=SystemId('polymer', '0.0.1'))
    #     json_path = 'tests/logs/TestRetrieve/test_retrieve_cog_area_extraction_by_system_id.json'
    #     log.info(f'Saving result to {json_path}')
    #     with open(json_path, 'w') as fh:
    #         fh.write(json.dumps(json_data))
    #     log.info('Test passed successfully')
    
    def test_retrieve_cog_legend_items(self):
        log = init_test_log('TestRetrieve/test_retrieve_cog_legend_items')
        json_data = rt.retrieve_cog_legend_items(self.con, self.cog_id)
        json_path = 'tests/logs/TestRetrieve/test_cog_legend_items.json'
        log.info(f'Saving result to {json_path}')
        with open(json_path, 'w') as fh:
            fh.write(json.dumps(json_data))
        log.info('Test passed successfully')

    # def test_retrieve_cog_legend_items_by_system_id(self):
    #     log = init_test_log('TestRetrieve/test_retrieve_cog_legend_items_by_system_id')
    #     json_data = rt.retrieve_cog_legend_items(self.con, self.cog_id, system_id=SystemId('polymer', '0.0.1'))
    #     json_path = 'tests/logs/TestRetrieve/test_cog_legend_items_by_system_id.json'
    #     log.info(f'Saving result to {json_path}')
    #     with open(json_path, 'w') as fh:
    #         fh.write(json.dumps(json_data))
    #     log.info('Test passed successfully')

    def teardown_class(self):
        self.con.unregister()