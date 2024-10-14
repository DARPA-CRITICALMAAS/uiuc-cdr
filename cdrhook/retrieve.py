from typing import List, Literal
from .connector import CdrConnector
from .cdr_endpoint_schemas import SystemId, CogSystemVersionsSchema, CogDownloadSchema
from cdr_schemas.cdr_responses.area_extractions import AreaExtractionResponse
from cdr_schemas.cdr_responses.legend_items import LegendItemResponse
from cdr_schemas.cdr_responses.cogs import CogMeta
from cdr_schemas.map_results import MapResults


# region Cog Endpoints
def retrieve_cog_download(connection:CdrConnector, cog_id:str) -> CogDownloadSchema:
    """
    Retrieve the download information for a cog. (download_url and ngmdb_ids)

    Args:
        connection (CdrConnector): A CdrConnector with a registered connection.
        cog_id (str): The id of the cog to retrieve data for

    Returns:
        CogDownloadSchema: The download information for the cog

    Raises:
        requests.HTTPError: If the request fails
        pydantic.ValidationError: If the data returned from the CDR does not match the CogDownloadSchema format.
    """
    endpoint_url = f"{connection.cdr_url}/v1/maps/cog/{cog_id}"
    return connection.retrieve_endpoint(endpoint_url, schema=CogDownloadSchema)

def retrieve_cog_metadata(connection:CdrConnector, cog_id:str) -> CogMeta:
    """
    Retrieve the metadata for a cog.

    Args:
        connection (CdrConnector): A CdrConnector with a registered connection.
        cog_id (str): The id of the cog to retrieve data for

    Returns:
        CogMetadataSchema: The metadata information for the cog

    Raises:
        requests.HTTPError: If the request fails
        pydantic.ValidationError: If the data returned from the CDR does not match the CogMetadataSchema format.
    """
    endpoint_url = f"{connection.cdr_url}/v1/maps/cog/meta/{cog_id}"
    return connection.retrieve_endpoint(endpoint_url, schema=CogMeta)

def retrieve_cog_results(connection:CdrConnector, cog_id:str) -> List[MapResults]:
    """
    Retrieve the georeferencing and segmentation results for a cog. Currently drops the point feature results due to issues in how CDR returns data.

    Args:
        connection (CdrConnector): A CdrConnector with a registered connection.
        cog_id (str): The id of the cog to retrieve data for

    Returns:
        MapResults: The georeferencing and segmentation results for the cog

    Raises:
        requests.HTTPError: If the request fails
        pydantic.ValidationError: If the data returned from the CDR does not match the MapResults format.
    """
    # Data will be returned in the format it was orginally uploaded in. This means we have to
    # support every version of MapResults that has existed. 
    def fix_map_unit_format(d:dict) -> dict:
        for er in d['extraction_results']:
            for pfr in er['polygon_feature_results']:
                if pfr['map_unit'] is None:
                    pfr['map_unit'] = []
                if not isinstance(pfr['map_unit'], list):
                    pfr["map_unit"] = [pfr['map_unit']]
        return d
    def drop_point_features(d:dict) -> dict:
        # Can't seem to get the point features to work so just dropping them. Too many different versions to fix. 
        for er in d['extraction_results']:
            er['point_feature_results'] = []
            # for pfr in er['point_feature_results']:
            #     for pf in pfr['point_features']:
            #         if pf['features'] is not None:
            #             for f in pf['features']:
            #                 if f['properties']['bbox'] is None:
            #                     f['properties']['bbox'] = []
        # extraction_results.11.point_feature_results.1.point_features.features.0.properties.bbox
        return d
    endpoint_url = f"{connection.cdr_url}/v1/maps/cog/{cog_id}/results"
    response_data = connection.retrieve_endpoint(endpoint_url)
    if isinstance(response_data, dict):
        response_data = [response_data]
    results = []
    for response in response_data:
        response['cog_id'] = cog_id
        response = fix_map_unit_format(response)
        response = drop_point_features(response)
        results.append(MapResults.model_validate(response))
    return results
    # response_data['cog_id'] = cog_id # Need to add cog_id to the response to conform to cdr_schema
    # return response_data

def retrieve_cog_system_versions(connection:CdrConnector, cog_id:str, type:Literal['any','legend_item', 'polygon', 'line', 'point', 'area_extraction']='any') -> CogSystemVersionsSchema:
    """
    Retrieve list of system versions that have posted data for this cog

    Args:
        connection (CdrConnector): A CdrConnector with a registered connection.
        cog_id (str): The id of the cog to retrieve data for
        type (Literal['any','legend_item', 'polygon', 'line', 'point', 'area_extraction'], optional): Filter system versions for a specific feature type. Defaults to 'any'.

    Returns:
        CogSystemVersionsSchema: A list of system versions that have posted data for this cog

    Raises:
        requests.HTTPError: If the request fails
        pydantic.ValidationError: If the data returned from the CDR does not match the CogSystemVersionsSchema format.
    """
    endpoint_url = f"{connection.cdr_url}/v1/features/{cog_id}/system_versions"
    if type != 'any':
        endpoint_url += f"?type={type}"
    response = connection.retrieve_endpoint(endpoint_url)
    system_versions = [SystemId(name=item[0], version=item[1]) for item in response]
    return CogSystemVersionsSchema(system_versions=system_versions)

def retrieve_cog_area_extraction(connection:CdrConnector, cog_id:str, system_id:SystemId=None, validated:Literal['any','false','true']="any", items:int=5000) -> List[AreaExtractionResponse]:
    """
    Retreive area extraction data for a given cog from the cdr.

    Args:
        connection (CdrConnector): A CdrConnector with a registered connection.
        cog_id (str): The id of the cog to retrieve data for
        system_id (SystemId, optional): The system id to filter the data by. Defaults to None.
        validated (Literal['any','false','true'], optional): The validation status of the data. Defaults to "any".
        items (int, optional): The maxium number of items to retrieve. Defaults to 5000.

    Returns:
        List[AreaExtractionResponse]: A list of area extraction responses.

    Raises:
        requests.HTTPError: If the request fails
        pydantic.ValidationError: If the data returned does not match the AreaExtractionResponse format.
    """
    endpoint_url = f"{connection.cdr_url}/v1/features/{cog_id}/area_extractions?size={items}"
    if system_id is not None:
        endpoint_url += f"&system_version={system_id.name}__{system_id.version}"
    if validated.lower() in ['true','false']:
        endpoint_url += f"&validated={validated.lower()}"
    return connection.retrieve_endpoint(endpoint_url, schema=AreaExtractionResponse)

def retrieve_cog_legend_items(connection:CdrConnector, cog_id:str, system_id:SystemId=None, validated:Literal['any','false','true']="any", items:int=5000) -> List[LegendItemResponse]:
    """
    Retrieve legend items for a given cog from the cdr.

    Args:
        connection (CdrConnector): A CdrConnector with a registered connection.
        cog_id (str): The id of the cog to retrieve data for
        system_id (SystemId, optional): The system id to filter the data by. Defaults to None.
        validated (Literal['any','false','true'], optional): The validation status of the data. Defaults to "any".
        items (int, optional): The maxium number of items to retrieve. Defaults to 5000.

    Returns:
        List[LegendItemResponse]: A list of legend items.

    Raises:
        requests.HTTPError: If the request fails
        pydantic.ValidationError: If the data returned does not match the LegendItemResponse format.
    """
    endpoint_url = f"{connection.cdr_url}/v1/features/{cog_id}/legend_items?size={items}"
    if system_id is not None:
        endpoint_url += f"&system_version={system_id.name}__{system_id.version}"
    if validated.lower() in ['true','false']:
        endpoint_url += f"&validated={validated.lower()}"
    return connection.retrieve_endpoint(endpoint_url, schema=LegendItemResponse)
# endregion Cog Endpoints

# region Event Endpoints
def retrieve_area_extraction_event(connection:CdrConnector, event_id:str) -> dict:
    """
    Retrieve the area extraction data for a given cdr event id.

    Args:
        connection (CdrConnector): A CdrConnector with a registered connection.
        event_id (str): The id of the event to retrieve data for

    Returns:
        dict: The area extraction data for the event. Close to format of cdr_schemas.AreaExtraction object.

    Raises:
        requests.HTTPError: If the request fails
    """
    endpoint_url = f"{connection.cdr_url}/v1/maps/extractions/{event_id}"
    return connection.retrieve_endpoint(endpoint_url)
# endregion Event Endpoints

