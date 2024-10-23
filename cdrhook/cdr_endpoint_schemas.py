from typing import List, Optional
from pydantic import BaseModel, Field

# # Returned by cog_download enpoint
class CogDownloadSchema(BaseModel):
    """
    The response schema from the CDR cog download endpoint.
    """
    cog_url: str = Field(description="The URL to download the geotif of the requested cog")
    ngmdb_prod: Optional[str] = Field(description="???")
    ngmdb_item: Optional[int] = Field(description="???")

# # Returned by cog_system_versions endpoint
class SystemId(BaseModel):
    """
    The system ID tuple used by the CDR to identify the provence of a peice of data.
    System versions endpoint returns a list of these.
    """
    name: str = Field(description="The name of the system")
    version: str = Field(description="The version of the system")

class CogSystemVersionsSchema(BaseModel):
    """
    The response schema from the CDR cog system versions endpoint.
    """
    system_versions: List[SystemId]

    def pretty_str(self):
        """
        Return a pretty string representation of the system versions.
        """
        outstr = "CogSystemVersionsSchema(\n"
        outstr += "\n".join([f"\t{s.name} - {s.version}," for s in self.system_versions])[:-1]
        outstr += "\n)"
        return outstr

# # Returned by cog_metadata endpoint
class GeoJsonCoord(BaseModel):
    type: str
    coordinates: List[List[List[float]]]

class CMACoord(BaseModel):
    type: str
    coordinates: List[List[List[List[float]]]]

class CmaInfo(BaseModel):
    extent: CMACoord
    resolution: List[float]
    description: str
    creation_date: str
    cma_id : str
    crs : str
    mineral : str
    download_url : str

class CogMetadataSchema(BaseModel):
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
    best_bounds: GeoJsonCoord
    cmas: List[CmaInfo]
    georeferenced_count : int
    validated_count : int

