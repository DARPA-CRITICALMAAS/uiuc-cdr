import json

import cdrhook.convert as convert
import cdrhook.retrieve as retrieve
from tests.utilities import init_test_log

class TestConvert:
    # def test_convert_cdr_schema_map_to_cmass_map(self):
    #     log = init_test_log('TestConvert/test_convert_cdr_schema_map_to_cmass_map')
    #     with open('tests/data/sample_cog_results.json', 'r') as fh:
    #         cdr_map = retrieve.validate_cog_results_response(json.load(fh))
    #     cmass_map = convert.convert_cdr_schema_map_to_cmass_map(cdr_map)
    #     assert cmass_map
    #     log.info('Test passed successfully')

    def test_convert_cdr_schema_metadata_to_cmass_map_metadata(self):
        log = init_test_log("TestConvert/test_convert_cdr_schema_metadata_to_cmass_map_metadata")
        with open("tests/data/sample_cog_metadata.json", "r") as fh:
            cdr_metadata = retrieve.validate_cog_metadata_response(json.load(fh))
        cmass_map_metadata = convert.convert_cdr_schema_metadata_to_cmass_map_metadata(cdr_metadata)
        assert cmass_map_metadata
        log.info("Test passed successfully")

    def test_convert_cdr_schema_legend_items_to_cmass_legend(self):
        log = init_test_log("TestConvert/test_convert_cdr_schema_legend_items_to_cmass_legend")
        with open("tests/data/sample_cog_legend.json", "r") as fh:
            cdr_legend = retrieve.validate_cog_legend_items_response(json.load(fh))
        cmass_legend = convert.convert_cdr_schema_legend_items_to_cmass_legend(cdr_legend)
        assert cmass_legend
        log.info("Test passed successfully")

    def test_convert_cdr_schema_area_extraction_to_layout(self):
        log = init_test_log("TestConvert/test_convert_cdr_schema_area_extraction_to_layout")
        with open("tests/data/sample_cog_area_extraction.json", "r") as fh:
            cdr_area_extraction = retrieve.validate_cog_area_extraction_response(json.load(fh))
        layout = convert.convert_cdr_schema_area_extraction_to_layout(cdr_area_extraction)
        assert layout
        log.info("Test passed successfully")
