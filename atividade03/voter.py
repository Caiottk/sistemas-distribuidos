import Pyro5.api

@Pyro5.api.expose
class VoterObserver:
    def __init__(self):
        self.__uri = None
        
        self.__notification_uris = []

        self.__daemon = Pyro5.server.Daemon()
        self.__uri = self.__daemon.register(self)

        name_server = Pyro5.api.locate_ns()
        self.__leader_uri = name_server.lookup('Líder-Epoca1')  
        self.__leader = Pyro5.api.Proxy(self.__leader_uri)

        if not self.__leader.register(self.__uri):
            raise("Falha ao se registrar")
        else:
            print("Registrado com sucesso.")

        self.__commited_list = []
        self.__uncommited_list = []
        self.voter = False

    def set_voter(self,uncommited_list,commited_list):
        self.voter = True
        self.__commited_list = commited_list
        self.__uncommited_list = uncommited_list
        if len(self.__uncommited_list) < len(self.__commited_list):
            self.__leader = Pyro5.api.Proxy(self.__leader_uri)
            self.__leader.confirm_message()
            
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
    def notify_voter(self):
        print("Notificação Recebida!")
        self.__leader = Pyro5.api.Proxy(self.__leader_uri)
        messages = self.__leader.get_message(len(self.__uncommited_list))
        self.__uncommited_list += messages
        self.__leader.confirm_message(len(self.__uncommited_list))

    @Pyro5.api.oneway
    def commit(self):
        self.__commited_list = self.__uncommited_list

if __name__ == '__main__':
    voter = VoterObserver()
    voter.start()
    