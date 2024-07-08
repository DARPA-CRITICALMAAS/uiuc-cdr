import logging
import requests
from typing import List, Optional
from pydantic import BaseModel, Field, AnyUrl

class CdrConnector(BaseModel):
    cdr_url : AnyUrl = Field(
        default="https://api.cdr.land",
        description="The URL of the CDR API")
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
    registration : Optional[str] = Field(
        default=None,
        description="The registration ID returned by the CDR")
    
    def register(self):
        """
        Register our system to the CDR using the app_settings
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
        r = requests.post(f"{self.cdr_url}/user/me/register", json=registration, headers=headers)
        logging.debug(r.text)
        r.raise_for_status()
        self.registration = r.json()["id"]
        logging.info(f"Registered with CDR, id : {self.registration}")
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

    def __del__(self):
        if self.registration is not None:
            self.unregister()