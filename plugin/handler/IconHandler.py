import imgkit

class IconHandler:
    def __init__(self, serverAddress: str, serverType: str, serverVersion: str, motd: str, onlinePlayerCount: int, responseLatency: float) -> None:
        self.serverAddress = serverAddress
        self.serverType = serverType
        self.serverVersion = serverVersion
        self.motd = motd
        self.onlinePlayerCount = onlinePlayerCount
        self.responseLatency = responseLatency
    
    def IconHandler(self):
        pass