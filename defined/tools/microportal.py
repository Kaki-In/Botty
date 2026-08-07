import interactions as _interaction
import saves as _saves
import websockets.sync.client as _websockets_sync_client
import typing as _T
import json as _json

class _microportal_configuration_object(_T.TypedDict):
    host: str
    port: int
    username: str
    password: str
    robot_name: str

class MicroportalTool(_interaction.ChatCompletionTool):
    def __init__(self, directory: _saves.ResourcesDirectory) -> None:
        super().__init__(
            "déclencher_portail",
            self.open_portal,
            "Déclenche l'ouverture ou la fermeture du portail électrique du jardin. ",
            is_ephemeral=True
        )
        
        self.__directory = directory
        
    def open_portal(self, update_state: _T.Callable[[str], _T.Any], **kwargs) -> str:
        configuration = _saves.ConfigurationFile[_microportal_configuration_object](self.__directory.get_resource('config.json'), {
            'host': 'localhost',
            'port': 8266,
            'username': '',
            'password': '',
            'robot_name': ''
        }).read_configuration()
        
        with _websockets_sync_client.connect(f"ws://{configuration['host']}:{configuration['port']}/user") as _client:
            client: _websockets_sync_client.ClientConnection = _client # type:ignore

            client.send(_json.dumps({
                "name": "connectToAccount",
                "args": {
                    "name": configuration['username'],
                    "password": configuration['password']
                }
            }) + "\n")

            while True:
                try:
                    result = client.recv(3)
                    print(result)
                except TimeoutError:
                    break
            
            self.send_action(client, {
                "name": "sendRobotAction",
                "args": {
                    "robot": configuration["robot_name"],
                    "action": "setPin",
                    "args": {
                        "pin": 4,
                        "active": True
                    }
                }
            })
                
            self.send_action(client, {
                "name": "sendRobotAction",
                "args": {
                    "robot": configuration["robot_name"],
                    "action": "setPin",
                    "args": {
                        "pin": 4,
                        "active": False
                    }
                }
            })
            
            return _json.dumps({"command_status": "success"})

    def send_action(self, client: _websockets_sync_client.ClientConnection, command):
        print("sending action", command)
#        return "done"
    
        client.send(_json.dumps(command))
        
        while True:
            result = client.recv(5)
            data = _json.loads(result)

            if not data["name"] in ("robotActionSent", "requestProcessing"):
                break
            else:
                print("Wasting", result)

        return data
