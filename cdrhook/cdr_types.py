# Returned by system_versions endpoint
class SystemId:
    def __init__(self, system_name:str, system_version:str):
        self.name = system_name
        self.version = system_version