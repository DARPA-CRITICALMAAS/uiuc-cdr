from cdrhook.connector import CdrConnector

class MockConnector(CdrConnector):
    # override 
    def register(self):
        return '12345'
    # override
    def unregister(self):
        return 
    
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

def get_mock_connector():
    return MockConnector('mock_connector', '0.1', 'mock_token')
