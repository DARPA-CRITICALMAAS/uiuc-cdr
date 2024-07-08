import logging
import requests

class CdrConnector:
    cdr_url = "https://api.cdr.land"

    def __init__(self, system_name, system_version, token, callback_url, callback_secret="", callback_username="", callback_password=""):
        self.system_name = system_name
        self.system_version = system_version
        self.token = token
        self.callback_url = callback_url
        self.callback_secret = callback_secret
        self.callback_username = callback_username
        self.callback_password = callback_password
        # Registers for ALL events
        self.events = []
        self.registration = None
    
    def register(self):
        """
        Register our system to the CDR using the app_settings
        """
        headers = {'Authorization': f'Bearer {self.token}'}
        registration = {
            "name": self.system_name,
            "version": self.system_version,
            "callback_url": self.callback_url,
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