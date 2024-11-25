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
        
    def get_commited_log(self):
        return self.__commited_log

    def start(self):
        print('Leader is running...')
        self.__daemon.requestLoop()

    def register(self, uri):
        if len(self.__voter_uris) ==  self.__quorum_size:
            self.__observer_uris.append(uri)
            print(f"Novo observer registrado. URI: {uri}")
            return 'observer'
        else:
            self.__voter_uris.append(uri)
            print(f"Novo votante registrado. URI: {uri}")
            return 'voter'

    def get_message(self,offset):
        print("Get Message")
        if (len(self.__uncommited_log)) < offset:
            print("Erro")
            raise Exception("Offset incorreto")
        messages = []
        for i in range(offset,len(self.__uncommited_log)):
            messages.append(self.__uncommited_log[i]['entry'])
            #self.__uncommited_log[i]['votes'] += 1
            #if self.__uncommited_log[i]['votes'] == self.__quorum_size:
            #    self.__commited_log.append(self.__uncommited_log[i]['entry'])
                #Notificar os consumidores
        return messages

    def confirm_message(self,uri,offset):
        self.__uncommited_log[offset-1]['votes'][uri] = True
        print(uri)
        for vote in self.__uncommited_log[offset-1]['votes'].values():
            if not vote:
                break
        #if self.__uncommited_log[offset-1]['votes'] == self.__quorum_size:
            self.__commited_log.append(self.__uncommited_log[offset-1]['entry'])
            self.__notify_commit()
            self.__voting = False

    def __notify_commit(self):
        for voter_uri in self.__voter_uris:
            voter = Pyro5.api.Proxy(voter_uri)
            voter.commit()

    def __notify_voters(self):
        for voter_uri in self.__voter_uris:   
            try:
                voter = Pyro5.api.Proxy(voter_uri)
                voter.notify_voter()
                print("Notificado")
            except:
                if len(self.__observer_uris) >= 0:
                    self.__voter_uris.remove(voter_uri)
                    new_voter = self.__observer_uris[0]
                    try:
                        new_voter = Pyro5.api.Proxy(new_voter)
                        new_voter.set_voter()
                        print("Novo Votante!")
                    except:
                        print("Votantes Indisponíveis!")    
    
    def __append_uncommited(self,entry):
        votes = {key:False for key in self.__voter_uris}
        self.__uncommited_log.append({'entry':entry,'votes':votes})

    def __append_and_notify(self,entry):
        while self.__voting:
            pass
        self.__voting = True
        print(self.__voter_uris)
        self.__append_uncommited(entry)
        self.__notify_voters()

    def publish(self, entry):
        self.__append_and_notify(entry)
        #thread = threading.Thread(target=self.__append_and_notify(entry))
        #thread.start()

if __name__ == '__main__':
    leader = Leader()
    leader.start()