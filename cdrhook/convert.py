from typing import List
from cdr_endpoint_schemas import CogMetadataSchema
from cdr_schemas.cdr_responses.legend_items import LegendItemResponse
from cdr_schemas.cdr_responses.area_extractions import AreaExtractionResponse
from cmaas_utils.types import Legend, MapUnit, MapUnitType, Layout, CMAAS_MapMetadata, Provenance

def convert_cdr_schema_metadata_to_cmass_map_metadata(cdr_metadata:CogMetadataSchema) -> CMAAS_MapMetadata:
    map_metadata = CMAAS_MapMetadata(provenance=Provenance(name='CDR', version='0.3.3'))
    map_metadata.title = cdr_metadata.cog_name
    map_metadata.authors = cdr_metadata.authors
    map_metadata.publisher = cdr_metadata.publisher
    map_metadata.source_url = cdr_metadata.cog_url
    map_metadata.year = cdr_metadata.publish_year
    map_metadata.scale = cdr_metadata.scale
    #map_metadata.map_color =
    #map_metadata.map_shape = 
    #map_metadata.physiographic_region 
    return map_metadata

def convert_cdr_schema_legend_items_to_cmass_legend(cdr_legend:List[LegendItemResponse]) -> Legend:
    if len(cdr_legend) == 0:
        return None
    legend = Legend(provenance=Provenance(name=cdr_legend[0].system, version=cdr_legend[0].system_version))    
    for item in cdr_legend:
        map_unit = MapUnit(type=MapUnitType.from_str(item.category.lower()))
        map_unit.label = item.label
        map_unit.abbreviation = item.abbreviation
        map_unit.description = item.description
        map_unit.color = item.color
        map_unit.pattern = item.pattern
        #map_unit.overlay = 
        map_unit.bounding_box = [item.px_bbox[0:2],item.px_bbox[2:4]]
        legend.features.append(map_unit)
    return legend

def convert_cdr_schema_area_extraction_to_layout(cdr_area_extraction:List[AreaExtractionResponse]) -> Layout:
    if len(cdr_area_extraction) == 0:
        return None
    layout = Layout(provenance=Provenance(name=cdr_area_extraction[0].system, version=cdr_area_extraction[0].system_version))
    for area in cdr_area_extraction:
        if area.category == 'map_area':
            layout.map = area.px_geojson.coordinates
        if area.category == 'line_point_legend_area':
            layout.line_legend = area.px_geojson.coordinates
            layout.point_legend = area.px_geojson.coordinates
        if area.category == 'polygon_legend_area':
            layout.polygon_legend = area.px_geojson.coordinates
        if area.category == 'cross_section':
            layout.cross_section = area.px_geojson.coordinates
        if area.category == 'correlation_diagram':
            layout.correlation_diagram = area.px_geojson.coordinates
    return layout