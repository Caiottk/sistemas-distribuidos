import Pyro5.api
from threading import Timer
import time

@Pyro5.api.expose
class Leader:
    def __init__(self):
        self.voter_uris = []
        self.observer_uris = []

        self.log = []
        self.quorum_size = 2
        self.confirmations = {}
        self.heart_interval = {}
        
        self.daemon = Pyro5.server.Daemon()
        self.uri = self.daemon.register(self)

        ns = Pyro5.api.locate_ns()
        ns.register('Líder-Epoca1', self.uri)
        
    def start(self):
        print('Leader is running...')
        self.daemon.requestLoop()

    def register_voter(self, uri):
        self.voter_uris.append(uri)
        print(f"Novo votante registrado. URI: {uri}")
        return True
    
    def register_observer(self, uri):
        self.observer_uris.append(uri)
        print(f"Novo observador registrado. URI: {uri}")
        return True
    
    def add_entry(self, entry):
        self.log.append(entry)
        entry_offset = len(self.log) - 1
        print (f"Entry added: {entry} at index {entry_offset}")

    def hello(self):
        print("Hello")

if __name__ == '__main__':
    leader = Leader()
    leader.start()