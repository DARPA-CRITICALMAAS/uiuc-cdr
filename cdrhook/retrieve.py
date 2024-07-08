import logging
import requests
from cdrhook.connector import CdrConnector
from cdrhook.cdr_types import SystemId

# Generic retrieval
def retrieve_json(connection:CdrConnector, endpoint_url:str, headers:dict=None):
    if headers is None:
        headers = {'Authorization': f'Bearer {connection.token}'}
    logging.debug(f"Retrieving {endpoint_url}")
    r = requests.get(endpoint_url, headers=headers)
    r.raise_for_status()
    return r.json()

# region Cog Endpoints
def retrieve_cog_metadata(connection:CdrConnector, cog_id:str):
    # Get cog info
    endpoint_url = f"{connection.cdr_url}/v1/maps/cog/meta/{cog_id}"
    return retrieve_json(connection, endpoint_url)

def retrieve_cog_results(connection:CdrConnector, cog_id:str):
    # Get results for a cog
    endpoint_url = f"{connection.cdr_url}/v1/maps/cog/{cog_id}/results"
    return retrieve_json(connection, endpoint_url)

def retrieve_cog_system_versions(connection:CdrConnector, cog_id:str):
    # Get all system_versions for extraction types per cog
    endpoint_url = f"{connection.cdr_url}/v1/features/{cog_id}/system_versions"
    return retrieve_json(connection, endpoint_url)

def retrieve_cog_area_extraction(connection:CdrConnector, cog_id:str, system_id:SystemId=None):
    # Get all area extractions for a cog
    endpoint_url = f"{connection.cdr_url}/v1/features/{cog_id}/area_extractions"
    if system_id is not None:
        endpoint_url += f"?system_version={system_id.name}__{system_id.version}"
    return retrieve_json(connection, endpoint_url)

def retrieve_cog_legend_items(connection:CdrConnector, cog_id:str, system_id:SystemId=None):
    # Get all legend items for a cog
    endpoint_url = f"{connection.cdr_url}/v1/features/{cog_id}/legend_items"
    if system_id is not None:
        endpoint_url += f"?system_version={system_id.name}__{system_id.version}"
    return retrieve_json(connection, endpoint_url)
# endregion Cog Endpoints

# region Event Endpoints
def retrieve_area_extraction_event(connection:CdrConnector, event_id:str):
    endpoint_url = f"{connection.cdr_url}/v1/maps/extractions/{event_id}"
    return retrieve_json(connection, endpoint_url)
# endregion Event Endpoints

