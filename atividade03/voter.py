import Pyro5.api

@Pyro5.api.expose
class Voter:
    def __init__(self):
        self.__uri = None
        
        self.__notification_uris = []

        self.__daemon = Pyro5.server.Daemon()
        self.__uri = self.__daemon.register(self)

        name_server = Pyro5.api.locate_ns()
        self.__leader_uri = name_server.lookup('Líder-Epoca1')  
        self.__leader = Pyro5.api.Proxy(self.__leader_uri)
    
        if not self.__leader.register_voter(self.__uri):
            raise("Falha ao se registrar como votante.")
        else:
            print("Registrado como votante com sucesso.")
            
        self.log = []
        self.offset = 0

    def start(self):
        print('Voter is running...')
        self.__daemon.requestLoop()

    def add_notification_uri(self, uri):
        self.__notification_uris.append(uri)

    def remove_notification_uri(self, uri):
        self.__notification_uris.remove(uri)

    def vote(self, message):
        for uri in self.__notification_uris:
            with Pyro5.api.Proxy(uri) as observer:
                observer.update(message)

    def setUri(self,uri):
        self.uri = uri

    @Pyro5.api.oneway
    def notify(self):
        print("Notificação Recebida!")
        self.__leader = Pyro5.api.Proxy(self.__leader_uri)
        messages = self.__leader.get_message(self.offset)
        self.offset += len(messages)

if __name__ == '__main__':
    voter = Voter()
    voter.start()
    