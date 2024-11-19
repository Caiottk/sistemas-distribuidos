import Pyro5.api
from queue import Queue
from threading import Thread


class Observer:


    if __name__ == "__main__":
        leader = 
        msg_q = Queue()
        daemon = Pyro5.api.Daemon()
        observer = Observer()

        uri = daemon.register(observer)
        observer.set_uri(str(uri))

        server_t = Thread(target=server, args=(msg_q,))
        server_t.start()

        observer.run()
    