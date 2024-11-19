import Pyro5.api

class Voter:
    def __init__(self):
        self.__notification_uris = []

    def add_notification_uri(self, uri):
        self.__notification_uris.append(uri)

    def remove_notification_uri(self, uri):
        self.__notification_uris.remove(uri)

    def vote(self, message):
        for uri in self.__notification_uris:
            with Pyro5.api.Proxy(uri) as observer:
                observer.update(message)

