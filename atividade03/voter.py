import Pyro5.api
import threading
import time

HEARTBEAT_PERIOD = 3

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

    def send_heabeat(self):
        while True:
            leader = Pyro5.api.Proxy(self.__leader_uri) 
            leader.set_voter_heartbeat(self.__uri)
            time.sleep(HEARTBEAT_PERIOD)

    def set_voter(self):
        self.type = 'voter'
        self.__voter_setup()

    def send_confirmation(self):
        while True:
            if self.__send_confirm != 0:
                try:
                    leader = Pyro5.api.Proxy(self.__leader_uri) 
                    leader.confirm_message(self.__uri,len(self.__uncommited_list))
                    self.__send_confirm -= 1
                except:
                    continue

    def __voter_setup(self):
        thread = threading.Thread(target=self.send_confirmation)
        thread.start()
        thread = threading.Thread(target=self.send_heabeat)
        thread.start()
        print('Voter is running...')

    def start(self):
        self.__leader = Pyro5.api.Proxy(self.__leader_uri)
        self.__commited_list = self.__leader.get_commited_log()
        if self.type == 'voter':
            self.__voter_setup()
            print('Voter is running...')
        else:
            print("Observer is running")
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
    