import json
import cdrhook.convert as convert
from cdr_schemas.map_results import MapResults
from cdrhook.cdr_endpoint_schemas import AreaExtractionsEndpoint, LegendItemsEndpoint, MetadataEndpoint
from cdrhook.retrieve import validate_endpoint
from tests.utilities import init_test_log

class TestConvert:
    # def test_convert_cdr_schema_map_to_cmass_map(self):
    #     log = init_test_log('TestConvert/test_convert_cdr_schema_map_to_cmass_map')
    #     with open('tests/data/sample_cog_results.json', 'r') as fh:
    #         cdr_map = json.load(fh)
    #         for er in cdr_map['extraction_results']:
    #             er['point_feature_results'] = []
    #         cdr_map = validate_endpoint(cdr_map, MapResults)
    #     cmass_map = convert.convert_cdr_schema_map_to_cmass_map(cdr_map)
    #     assert cmass_map
    #     log.info('Test passed successfully')

    def test_convert_cdr_schema_metadata_to_cmass_map_metadata(self):
        log = init_test_log('TestConvert/test_convert_cdr_schema_metadata_to_cmass_map_metadata')
        with open('tests/data/sample_cog_metadata.json', 'r') as fh:
            cdr_metadata = (validate_endpoint(json.load(fh), MetadataEndpoint))
        cmass_map_metadata = convert.convert_cdr_schema_metadata_to_cmass_map_metadata(cdr_metadata)
        assert cmass_map_metadata
        log.info('Test passed successfully')

    def test_convert_cdr_schema_legend_items_to_cmass_legend(self):
        log = init_test_log('TestConvert/test_convert_cdr_schema_legend_items_to_cmass_legend')
        with open('tests/data/sample_cog_legend.json', 'r') as fh:
            cdr_legend = []
            for map_unit in json.load(fh):
                cdr_legend.append(validate_endpoint(map_unit, LegendItemsEndpoint))
        cmass_legend = convert.convert_cdr_schema_legend_items_to_cmass_legend(cdr_legend)
        assert cmass_legend
        log.info('Test passed successfully')

    def test_convert_cdr_schema_area_extraction_to_layout(self):
        log = init_test_log('TestConvert/test_convert_cdr_schema_area_extraction_to_layout')
        with open('tests/data/sample_cog_area_extraction.json', 'r') as fh:
            cdr_area_extraction = []
            for area in json.load(fh):
                cdr_area_extraction.append(validate_endpoint(area, AreaExtractionsEndpoint))
        layout = convert.convert_cdr_schema_area_extraction_to_layout(cdr_area_extraction)
        assert layout
        log.info('Test passed successfully')