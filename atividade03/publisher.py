import Pyro5.api


class Publisher:
    def __init__(self):
        self.__name_server = Pyro5.api.locate_ns()
        self.__leader_uri = self.__name_server.lookup('Líder-Epoca1')  
        leader = Pyro5.api.Proxy(self.__leader_uri)
    
    def send_message(self):
        message = input("Digiter a Mensagem:")
        self.__leader_uri = self.__name_server.lookup('Líder-Epoca1')  
        leader = Pyro5.api.Proxy(self.__leader_uri)
        leader.publish(message)
    def start(self):
        while True:
            self.send_message()

if __name__ == '__main__':
    publisher = Publisher()
    publisher.start()