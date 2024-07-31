import logging
import requests
from typing import List
from pydantic import BaseModel
from .connector import CdrConnector
from .cdr_endpoint_schemas import SystemId, CogSystemVersionsSchema, CogMetadataSchema, CogDownloadSchema
from cdr_schemas.cdr_responses.area_extractions import AreaExtractionResponse
from cdr_schemas.cdr_responses.legend_items import LegendItemResponse
from cdr_schemas.map_results import MapResults

# Generic retrieval
def retrieve_endpoint(connection:CdrConnector, endpoint_url:str, headers:dict=None):
    if headers is None:
        headers = {'Authorization': f'Bearer {connection.token}'}
    logging.debug(f"Retrieving {endpoint_url}")
    r = requests.get(endpoint_url, headers=headers)
    r.raise_for_status()
    return r.json()

def validate_endpoint(response:dict, schema:BaseModel):
    # Validate the response against the model
    return schema.model_validate(response)

# region Cog Endpoints
def retrieve_cog_download(connection:CdrConnector, cog_id:str) -> dict:
    endpoint_url = f"{connection.cdr_url}/v1/maps/cog/{cog_id}"
    return retrieve_endpoint(connection, endpoint_url)

def validate_cog_download_response(response:dict) -> CogDownloadSchema:
    """
    Convert the response from the cdr into a CogDownloadSchema object, validating the data in the process.
    """
    return CogDownloadSchema.model_validate(response)

def retrieve_cog_metadata(connection:CdrConnector, cog_id:str) -> dict:
    # Get cog info
    endpoint_url = f"{connection.cdr_url}/v1/maps/cog/meta/{cog_id}"
    return retrieve_endpoint(connection, endpoint_url)

def validate_cog_metadata_response(response:dict) -> CogMetadataSchema:
    """
    Convert the response from the cdr into a CogMetadataSchema object, validating the data in the process.
    """
    return CogMetadataSchema.model_validate(response)

def retrieve_cog_results(connection:CdrConnector, cog_id:str) -> dict:
    # Get results for a cog
    endpoint_url = f"{connection.cdr_url}/v1/maps/cog/{cog_id}/results"
    response_data = retrieve_endpoint(connection, endpoint_url)
    response_data['cog_id'] = cog_id # Need to add cog_id to the response to conform to cdr_schema
    return response_data

def validate_cog_results_response(response:dict) -> MapResults:
    """
    Convert the response from the cdr into a CogResultsSchema object, validating the data in the process. Does not
    convert point_feature_results as they have validation errors in the data that we are sent.
    """
    # Drop point_feature_results as they have validation errors
    for er in response['extraction_results']:
        er['point_feature_results'] = []
    return MapResults.model_validate(response)

def retrieve_cog_system_versions(connection:CdrConnector, cog_id:str) -> List[List[str]]:
    """
    Retrieve list of system versions that have posted data for this cog
    """
    # Get all system_versions for extraction types per cog
    endpoint_url = f"{connection.cdr_url}/v1/features/{cog_id}/system_versions"
    return retrieve_endpoint(connection, endpoint_url)

def validate_cog_system_versions_response(response:List[List[str]]) -> CogSystemVersionsSchema:
    """
    Convert the response from the cdr into a CogSystemVersionsSchema object, validating the data in the process.
    """
    system_versions = []
    for item in response:
        system_versions.append(SystemId(name=item[0], version=item[1]))
    return CogSystemVersionsSchema(system_versions=system_versions)

def retrieve_cog_area_extraction(connection:CdrConnector, cog_id:str, system_id:SystemId=None) -> List[dict]:
    """
    Retreive area extraction data for a given cog from the cdr. Note that while the code for filtering by system_id is 
    ready on our side, the cdr does not yet provide support for this and will just ignore the addtional query info.
    """
    endpoint_url = f"{connection.cdr_url}/v1/features/{cog_id}/area_extractions"
    if system_id is not None:
        endpoint_url += f"?system_version={system_id.name}__{system_id.version}"
    return retrieve_endpoint(connection, endpoint_url)

def validate_cog_area_extraction_response(response:List[dict]) -> List[AreaExtractionResponse]:
    """
    Convert the response from the cdr into a list of AreaExtractionResponse objects, validating the data in the process.
    """
    area_extractions = []
    for item in response:
        area_extractions.append(AreaExtractionResponse.model_validate(item))
    return area_extractions

def retrieve_cog_legend_items(connection:CdrConnector, cog_id:str, system_id:SystemId=None) -> List[dict]:
    # Get all legend items for a cog
    endpoint_url = f"{connection.cdr_url}/v1/features/{cog_id}/legend_items"
    if system_id is not None:
        endpoint_url += f"?system_version={system_id.name}__{system_id.version}"
    return retrieve_endpoint(connection, endpoint_url)

def validate_cog_legend_items_response(response:List[dict]) -> List[LegendItemResponse]:
    """
    Convert the response from the cdr into a list of LegendItemResponse objects, validating the data in the process.
    """
    legend_items = []
    for item in response:
        legend_items.append(LegendItemResponse.model_validate(item))
    return legend_items
# endregion Cog Endpoints

# region Event Endpoints
def retrieve_area_extraction_event(connection:CdrConnector, event_id:str) -> dict:
    endpoint_url = f"{connection.cdr_url}/v1/maps/extractions/{event_id}"
    return retrieve_endpoint(connection, endpoint_url)
# endregion Event Endpoints

