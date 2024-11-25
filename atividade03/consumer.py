import Pyro5.api
from queue import Queue
from threading import Thread

@Pyro5.api.expose
class Consumer:
    def __init__(self):
        self.log = []
        name_server = Pyro5.api.locate_ns()

        self.__daemon = Pyro5.server.Daemon()
        self.__uri = self.__daemon.register(self)

        self.__leader_uri = name_server.lookup('Líder-Epoca1')  
        self.__leader = Pyro5.api.Proxy(self.__leader_uri)
        self.__leader.register_consumer(self.__uri)

    @Pyro5.api.oneway
    def on_message(self,message):
        print(f"Message Received: {message}")
        self.log.append(message)

    def start(self):
        self.__daemon.requestLoop()
if __name__ == '__main__':
    consumer = Consumer()
    consumer.start()
    