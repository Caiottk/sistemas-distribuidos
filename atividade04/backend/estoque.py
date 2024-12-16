from defines import *
from auxFunc import *
import json

class Estoque:
    connection,channel = None,None

    products = [
        {"id": 1, "name": "Product 1", "price": 10,"quantity":5},
        {"id": 2, "name": "Product 2", "price": 20,"quantity":5},
        {"id": 3, "name": "Product 3", "price": 30,"quantity":5},
    ]
    
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

        Estoque.channel.queue_declare(queue=e_commerce_queue)
        Estoque.channel.queue_bind(exchange=exchange, queue=e_commerce_queue, routing_key=get_produtos)
        Estoque.channel.basic_consume(queue=e_commerce_queue, on_message_callback=Estoque.on_get_pedidos, auto_ack=True)
        
        Estoque.channel.start_consuming()

    def on_pedidos_criados(ch, method, properties, body):
        message = json.loads(body.decode('utf-8'))
        print(message)

    def on_pedidos_excluidos(ch, method, properties, body):

        message = json.loads(body.decode('utf-8'))
        print(message)

    def on_get_pedidos(ch, method, properties, body):
        Estoque.publish_produtos()

    def publish_produtos()->bool:
        try:
            Estoque.channel.basic_publish(exchange=exchange, routing_key= lista_produtos,body=json.dumps(Estoque.products))
            print("Pedido Criado com Sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar publicar pedido criado:\n{e}")
            return False
        
    def run()->None:
        while True:
            pass

if __name__ == "__main__":
    Estoque.init()
    Estoque.run()