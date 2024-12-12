from defines import *
from auxFunc import *
import json

class Estoque:
    connection,channel = None,None

    def init()->None:
        Estoque.connection, Estoque.channel = get_connection_channel(host, exchange)
        if (Estoque.connection and Estoque.channel) is not None:
            print("Conexão com o Broker estabelecida com sucesso!")
            Estoque.subscribe_to_topics()

    def subscribe_to_topics():
        #Se inscreve no tópio de Pagamentos Aprovados
        Estoque.channel.queue_declare(queue=e_commerce_queue)
        Estoque.channel.queue_bind(exchange=exchange, queue=e_commerce_queue, routing_key=pedidos_criados_key)
        Estoque.channel.basic_consume(queue=e_commerce_queue, on_message_callback=Estoque.on_pedidos_criados, auto_ack=True)

        Estoque.channel.queue_declare(queue=e_commerce_queue)
        Estoque.channel.queue_bind(exchange=exchange, queue=e_commerce_queue, routing_key=pedidos_excluidos_key)
        Estoque.channel.basic_consume(queue=e_commerce_queue, on_message_callback=Estoque.on_pedidos_excluidos, auto_ack=True)

        Estoque.channel.start_consuming()

    def on_pedidos_criados(ch, method, properties, body):
        """TODOOO Sistema de Estoque!!!"""
        message = json.loads(body.decode('utf-8'))
        print(message)

    def on_pedidos_excluidos(ch, method, properties, body):
        """TODOOO Sistema de Estoque!!!"""
        message = json.loads(body.decode('utf-8'))
        print(message)

    def run()->None:
        while True:
            pass

if __name__ == "__main__":
    Estoque.init()
    Estoque.run()