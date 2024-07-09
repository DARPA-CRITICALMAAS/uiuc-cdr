from typing import List, Optional
from pydantic import BaseModel

# Returned by cog_system_versions endpoint
class SystemId(BaseModel):
    name: str
    version: str

class SystemVersionsEndpoint(BaseModel):
    system_versions: List[SystemId]

# Returned by cog_area_extraction endpoint
class AreaExtractionCoords(BaseModel):
    type: str
    coordinates: List[List[List[float]]]

class AreaExtractionsEndpoint(BaseModel):
    area_extraction_id : str
    cog_id: str
    reference_id: str
    px_bbox : List[float]
    px_geojson : AreaExtractionCoords
    system :str
    system_version :str
    model_id : str
    validated : bool
    confidence : Optional[float] = None
    category : str
    text : str
    projected_feature : List[str]

# Returned by cog_legend_items endpoint
class PxGeojson(BaseModel):
    type: str
    coordinates: List = []
    
class LegendItemsEndpoint(BaseModel):
    legend_id: str
    abbreviation: str
    description: str
    color: str
    reference_id: str
    label: str
    pattern: str
    px_bbox: List = []
    px_geojson: PxGeojson
    cog_id: str
    category: str
    system: str
    system_version: str
    _model_id: str
    validated: bool
    confidence: Optional[float] = None
    map_unit_age_text: str
    map_unit_lithology: str
    map_unit_b_age: Optional[float] = None
    map_unit_t_age: Optional[float] = None
    point_extractions: List = []
    polygon_extractions: List = []
    line_extractions: List = []

# Returned by cog_metadata endpoint
class BestBoundsGeoJson(BaseModel):
    type: str
    coordinates: List[List[List[float]]]

class MetadataEndpoint(BaseModel):
    citation: str
    ngmdb_prod: str
    scale: int
    has_part_names: List[str]
    ngmdb_item: int
    cog_id: str
    publisher: str
    cog_url: str
    provider_name: str
    display_links_str: str
    cog_size: int
    authors: List[str]
    provider_url: str
    original_download_url: str
    no_map: bool
    thumbnail_url: str
    state: Optional[str]
    cog_name: str
    publish_year: int
    quadrangle: Optional[str]
    alternate_name: str
    keywords: List[str]
    best_bounds_geojson: BestBoundsGeoJson
    georeferenced_count : int
    validated_count : int

# Map results endpoint is a cdr_schema map_result