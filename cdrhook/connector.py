import logging
import requests
from typing import List, Optional
from pydantic import BaseModel, Field, AnyUrl

class CdrConnector(BaseModel):
    """
    Class to handle registration and communication with the CDR API.
    """
    system_name : str = Field(
        description="The name of the system registering with the CDR")
    system_version : str = Field(
        description="The version of the system registering with the CDR")
    token : str = Field(
        description="The token used to authenticate with the CDR")
    callback_url : AnyUrl = Field(
        description="The URL to which the CDR will send callbacks")
    callback_secret : str = Field(
        default="",
        description="The secret to use for the webhook")
    callback_username : str = Field(
        default="",
        description="The username to use for the webhook")
    callback_password : str = Field(
        default="",
        description="The password to use for the webhook")
    events : List[str] = Field(
        default_factory=list,
        description="The events to register for, leaving blank will register for all events")
    cdr_url : AnyUrl = Field(
        default="https://api.cdr.land",
        description="The URL of the CDR API")
    registration : Optional[str] = Field(
        default=None,
        description="The registration ID returned by the CDR")
    
    def register(self):
        """
        Register our system to the CDR using the app_settings. The register call can fail if
        another system with the same name and version is already registered, if this happens
        you can manual deregister the other system through the CDR Docs API or change the name
        and version of your system.

        Returns:
            str: The registration ID returned by the CDR

        Raises:
            requests.HTTPError: If the request fails
        """
        headers = {'Authorization': f'Bearer {self.token}'}
        registration = {
            "name": self.system_name,
            "version": self.system_version,
            "callback_url": str(self.callback_url),
            "webhook_secret": self.callback_secret,
            "auth_header": self.callback_username,
            "auth_token": self.callback_password,
            "events": self.events
        }
        logging.info(f"Registering with CDR: [system_name : {registration['name']}, system_version : {registration['version']}, callback_url : {registration['callback_url']}")
        r = requests.post(f"{self.cdr_url}user/me/register", json=registration, headers=headers)
        logging.debug(r.text)
        r.raise_for_status()
        self.registration = r.json()["id"]
        logging.info(f"Registered with CDR, registration id : {self.registration}")
        return r.json()["id"]
    
    def unregister(self):
        """
        Unregister our system from the CDR
        """
        # unregister from the CDR
        headers = {'Authorization': f"Bearer {self.token}"}
        logging.info("Unregistering with CDR")
        r = requests.delete(f"{self.cdr_url}/user/me/register/{self.registration}", headers=headers)
        logging.info("Unregistered with CDR")
        r.raise_for_status()
        self.registration = None

    def __str__(self) -> str:
        repr = "CdrConnector("
        repr += f"system_name='{self.system_name}', "
        repr += f"system_version='{self.system_version}', "
        repr += f"token='{self.token[:8]}...', "
        repr += f"callback_url='{self.callback_url}', "
        repr += f"callback_secret='{self.callback_secret[:8]}...', "
        repr += f"callback_username='{self.callback_username}', "
        repr += "callback_password='...', "
        repr += f"events={self.events}, "
        repr += f"cdr_url='{self.cdr_url}', "
        repr += f"registration={self.registration[:8]}..."
        repr += ")"
        return repr

    def __repr__(self) -> str:
        repr = "CdrConnector("
        repr += f"system_name='{self.system_name}', "
        repr += f"system_version='{self.system_version}', "
        repr += f"token='{self.token[:8]}...', "
        repr += f"callback_url='{self.callback_url}', "
        repr += f"callback_secret='{self.callback_secret[:8]}...', "
        repr += f"callback_username='{self.callback_username}', "
        repr += "callback_password='...', "
        repr += f"events={self.events}, "
        repr += f"cdr_url='{self.cdr_url}', "
        repr += f"registration={self.registration[:8]}..."
        repr += ")"
        return repr

    def __del__(self):
        if self.registration is not None:
            self.unregister()

    def retrieve_endpoint(self, endpoint_url:str, schema:BaseModel=None, headers:dict=None):
        """
        Retrieve data from a CDR endpoint. If a schema is provided, the data will be converted to that schema and validated.

        Args:
            endpoint_url (str): The URL of the endpoint to retrieve data from.
            schema (BaseModel, optional): A Pydantic schema to convert the data to. Defaults to None.
            headers (dict, optional): A dictionary of headers to include in the request.  Defaults to None.
        
        Returns:
            A dictionary of the data from the endpoint or
            An instance of the schema object if a schema was provided.
            Data can potentionally be a list if the endpoint returns multiple items.

        Raises:
            requests.HTTPError: If the request fails
            pydantic.ValidationError: If the data does not match the provided schema
        """
        if headers is None:
            headers = {'Authorization': f'Bearer {self.token}'}
        logging.debug(f"Retrieving {endpoint_url}")
        r = requests.get(endpoint_url, headers=headers)
        r.raise_for_status()
        response = r.json()
        if schema is not None:
            if isinstance(response, list):
                return [schema.model_validate(item) for item in response]
            return schema.model_validate(response)
        return response
