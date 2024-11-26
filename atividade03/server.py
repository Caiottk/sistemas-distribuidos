import Pyro5.api
from threading import Timer
import time
import threading
import copy 

HEARTBEAT_PERIOD = 10

@Pyro5.api.expose
class Leader:
    def __init__(self):
        self.__lock = threading.Lock()
        self.__voter_uris = []
        self.__active_voter_uris = {}
        self.__observer_uris = []
        self.__consumer_uris = []

        self.__uncommited_log = []
        self.__commited_log = []

        self.__quorum_size = 2
        
        self.__daemon = Pyro5.server.Daemon()
        self.__uri = self.__daemon.register(self)

        ns = Pyro5.api.locate_ns()
        ns.register('Líder-Epoca1', self.__uri)

        self.__voting = False
        self.__heartbeats = {}
        self.__cur_offset = 0
    def get_commited_log(self):
        return self.__commited_log

    def start(self):
        print('Leader is running...')
        self.__daemon.requestLoop()

    def voter_heartbeat_monitor(self, uri):
        while True:
            time.sleep(HEARTBEAT_PERIOD)
            if self.__heartbeats[uri]:
               self.__heartbeats[uri] = False
               continue
            if uri in self.__voter_uris:
                self.promote_observer_to_voter(uri)
            break
    
    @Pyro5.api.oneway
    def set_voter_heartbeat(self,uri):
        self.__heartbeats[uri] = True

    def __new_voter(self,uri):
        self.__voter_uris.append(uri)
        self.__heartbeats[uri] = True
        self.__active_voter_uris[uri] = True
        thread = threading.Thread(target=self.voter_heartbeat_monitor,args=(uri,))
        thread.start()
        print(f"Novo votante registrado. URI: {uri}")
        self.__notify_voters_about_new(uri)


    def register(self, uri):
        if len(self.__voter_uris) ==  self.__quorum_size:
            self.__observer_uris.append(uri)
            print(f"Novo observer registrado. URI: {uri}")
            return 'observer'
        else:
            self.__new_voter(uri)
            return 'voter'
        
    def register_consumer(self,uri):
        self.__consumer_uris.append(uri)

    def get_message(self,offset):
        print("Get Message")
        if (len(self.__uncommited_log)) < offset:
            print("Erro")
            raise Exception("Offset incorreto")
        messages = []
        for i in range(offset,len(self.__uncommited_log)):
            messages.append(self.__uncommited_log[i]['entry'])
        if len(messages) > 1:
            print(offset)
            print(messages)
        return messages

    def confirm_message(self, uri, offset):
        if offset > len(self.__uncommited_log):
            print(f"Erro: offset inválido {offset}")
            return
        
        self.__uncommited_log[offset - 1]['votes'][uri] = True
        print(f'Confirmação recebida de {uri} para offset {offset}')
        
        # Verifica se todos os votantes ativos confirmaram
        flag = all(
            vote or not self.__active_voter_uris[voter_uri]
            for voter_uri, vote in self.__uncommited_log[offset - 1]['votes'].items()
        )
        if flag:
            entry = self.__uncommited_log[offset - 1]['entry']
            self.__commited_log.append(entry)
            self.__notify_commit()
            self.__notify_consumer(entry)
            self.__voting = False
            print(f"Mensagem {entry} commitada com sucesso.")

            
    def __notify_consumer(self,message):
        for consumer_uri in self.__consumer_uris:
            consumer = Pyro5.api.Proxy(consumer_uri)
            consumer.on_message(message)

    def __notify_commit(self):
        for voter_uri in self.__voter_uris:
            voter = Pyro5.api.Proxy(voter_uri)
            voter.commit()

    def promote_observer_to_voter(self,voter_uri):
        if voter_uri in self.__voter_uris:
            self.__voter_uris.remove(voter_uri)
        self.__active_voter_uris[voter_uri] = False
        if len(self.__observer_uris) > 0:
            new_voter_uri = self.__observer_uris[0]
            try:
                new_voter = Pyro5.api.Proxy(new_voter_uri)
                new_voter.set_voter()
                self.__new_voter(new_voter_uri)
                self.__observer_uris.remove(new_voter_uri)
                print("Novo Votante!")
                return new_voter_uri
            except:
                print("Votantes Indisponíveis!") 
        else:
            print("Número insuficiente de observadores")


    def __notify_voters(self):
        voter_uris = copy.deepcopy(self.__voter_uris)
        for voter_uri in voter_uris:   
            try:
                voter = Pyro5.api.Proxy(voter_uri)
                voter.notify_voter()
                print(f"Votante {voter_uri} notificado.")
            except:
                print(f"Falha ao notificar votante {voter_uri}")
                self.promote_observer_to_voter(voter_uri)


    def __notify_voters_about_new(self, new_voter_uri):
        print(f"Notificando votantes sobre novo votante: {new_voter_uri}")
        for voter_uri in self.__voter_uris:
            if voter_uri != new_voter_uri: 
                try:
                    voter = Pyro5.api.Proxy(voter_uri)
                    voter.notify_new_voter(new_voter_uri)
                    print(f"Votante {voter_uri} notificado sobre {new_voter_uri}")
                except:
                    print(f"Falha ao notificar votante {voter_uri}")

                
    
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
        with self.__lock:
            self.__append_and_notify(entry)
        #thread = threading.Thread(target=self.__append_and_notify(entry))
        #thread.start()

if __name__ == '__main__':
    leader = Leader()
    leader.start()