import Pyro5.api
from threading import Timer
import time
import threading

@Pyro5.api.expose
class Leader:
    def __init__(self):
        self.__voter_uris = []
        self.__observer_uris = []

        self.__uncommited_log = []
        self.__commited_log = []

        self.__quorum_size = 2
        
        self.__daemon = Pyro5.server.Daemon()
        self.__uri = self.__daemon.register(self)

        ns = Pyro5.api.locate_ns()
        ns.register('Líder-Epoca1', self.__uri)

        self.__voting = False
        

    def start(self):
        print('Leader is running...')
        self.__daemon.requestLoop()

    def register_voter(self, uri):
        self.__voter_uris.append(uri)
        print(f"Novo votante registrado. URI: {uri}")
        return True
    
    def register_observer(self, uri):
        self.__observer_uris.append(uri)
        print(f"Novo observador registrado. URI: {uri}")
        return True

    def get_message(self,offset):
        if (len(self.__uncommited_log)) < offset:
            print("Erro")
            raise Exception("Offset incorreto")
        messages = []

        for i in range(offset,len(self.__uncommited_log)):
            messages.append(self.__uncommited_log[i]['entry'])
            self.__uncommited_log[i]['votes'] += 1
            
            if self.__uncommited_log[i]['votes'] == self.__quorum_size:
                self.__commited_log.append(self.__uncommited_log[i]['entry'])
                #Notificar os consumidores

        return messages
    
    def confirm_message(self,offset):
        self.__uncommited_log[offset]['votes'] += 1
        if self.__uncommited_log[offset]['votes'] == self.__quorum_size:
            self.__commited_log.append(self.__uncommited_log[offset]['entry'])
            self.__voting = False

    def __notify_voters(self):
        for voter_uri in self.__voter_uris:    
            try:
                voter = Pyro5.api.Proxy(voter_uri)
                voter.notify()
            except:
                print("Votante indisponível")
    
    def __append_uncommited(self,entry):
        self.__uncommited_log.append({'entry':entry,'votes':0})

    def __append_and_notify(self,entry):
        while self.__voting:
            pass
        self.__append_uncommited(entry)
        self.__notify_voters()

    def publish(self, entry):
        thread = threading.Thread(target=self.__append_and_notify(entry))
        thread.start()

if __name__ == '__main__':
    leader = Leader()
    leader.start()