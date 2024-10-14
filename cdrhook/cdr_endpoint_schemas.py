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

