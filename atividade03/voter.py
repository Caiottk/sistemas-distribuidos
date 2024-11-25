import Pyro5.api
import threading


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
        
        #Se é votante ou observador
        self.type = self.__leader.register(self.__uri)

        self.__commited_list = []
        self.__uncommited_list = []

        self.__send_confirm = 0

    def set_voter(self):
        self.type = 'voter'
        thread = threading.Thread(target=self.send_confirmation)
        thread.start()
        #self.__commited_list = commited_list
        #self.__uncommited_list = uncommited_list
        #if len(self.__uncommited_list) < len(self.__commited_list):
            
            
    def send_confirmation(self):
        while True:
            if self.__send_confirm != 0:
                leader = Pyro5.api.Proxy(self.__leader_uri) 
                leader.confirm_message(self.__uri,len(self.__uncommited_list))
                self.__send_confirm -= 1

    def start(self):
        if self.type == 'voter':
            self.__leader = Pyro5.api.Proxy(self.__leader_uri)
            self.__commited_list = self.__leader.get_commited_log()
        print('Voter is running...')
        thread = threading.Thread(target=self.send_confirmation)
        thread.start()
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
        self.__leader = Pyro5.api.Proxy(self.__leader_uri)
        messages = self.__leader.get_message(len(self.__commited_list))
        self.__uncommited_list += messages
        self.__send_confirm += 1
        print(messages)
        #self.__leader.confirm_message(self.uri,len(self.__uncommited_list))

    @Pyro5.api.oneway
    def commit(self):
        begin = len(self.__commited_list)
        end = len(self.__uncommited_list)
        for i in range(begin,end):
            self.__commited_list.append(self.__uncommited_list[i])
            print(f"Comitando {self.__uncommited_list[i]}")
            

if __name__ == '__main__':
    voter = VoterObserver()
    voter.start()
    