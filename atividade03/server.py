import Pyro5.api
from threading import Timer
import time

@Pyro5.api.expose
class Server:
    def __init__(self):
        self.__notification_uris = []
        self.log = []
        self.quorum_size = 2
        self.confirmations = {}
        self.heart_interval = {}

    def register_voter(self, uri):
        self.__notification_uris.append(uri)
    
    def add_entry(self, entry):
        self.log.append(entry)
        entry_offset = len(self.log) - 1
        print (f"Entry added: {entry} at index {entry_offset}")

    


if __name__ == '__main__':
    try:
        server = Server()
        daemon = Pyro5.server.Daemon()
        ns = Pyro5.api.locate_ns()

        uri = daemon.register(server)
        ns.register('Líder-Epoca1', uri)

        print('Server is running...')

        heart_beat_thread = Timer(0, server.monitorar_heartbets)
        heart_beat_thread.start()

        daemon.requestLoop()
    finally:
        daemon.close()