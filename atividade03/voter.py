import Pyro5.api

@Pyro5.api.expose
class Voter:
    def __init__(self):
        self.uri = None

        self.__notification_uris = []

        self.daemon = Pyro5.server.Daemon()
        self.uri = self.daemon.register(self)

        name_server = Pyro5.api.locate_ns()
        self.leader_uri = name_server.lookup('Líder-Epoca1')  
        self.leader = Pyro5.api.Proxy(self.leader_uri)
    
        if not self.leader.register_voter(self.uri):
            raise("Falha ao se registrar como votante.")
        else:
            print("Registrado como votante com sucesso.")
            
    def start(self):
        print('Voter is running...')
        self.daemon.requestLoop()

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

if __name__ == '__main__':
    voter = Voter()
    voter.start()
    