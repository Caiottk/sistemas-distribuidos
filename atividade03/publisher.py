import Pyro5.api

if __name__ == '__main__':
    name_server = Pyro5.api.locate_ns()
    leader_uri = name_server.lookup('Líder-Epoca1')  
    leader = Pyro5.api.Proxy(leader_uri)
    leader.publish("Olá Mundo!")