from defines import *
from auxFunc import *
import json

class Entrega:
    connection,channel = None,None

    def init()->None:
        Entrega.connection, Entrega.channel = get_connection_channel(host, exchange)
        if (Entrega.connection and Entrega.channel) is not None:
            print("Conexão com o Broker estabelecida com sucesso!")
            Entrega.subscribe_to_topics()

    def subscribe_to_topics():
        #Se inscreve no tópio de Pagamentos Aprovados
        Entrega.channel.queue_declare(queue=e_commerce_queue)
        Entrega.channel.queue_bind(exchange=exchange, queue=e_commerce_queue, routing_key=pagamentos_aprovados_key)
        Entrega.channel.basic_consume(queue=e_commerce_queue, on_message_callback=Entrega.on_pagamentos_aprovados, auto_ack=True)
        Entrega.channel.start_consuming()

    def on_pagamentos_aprovados(ch, method, properties, body):
        """Se algum pedido for aprovado, ele envia o pedido (publica no tópico pedidos enviados)"""
        message = json.loads(body.decode('utf-8'))
        if "id_pedido" not in message.keys():
            print("Erro: id_pedido faltante")
            return
        Entrega.publish_pedidos_enviados({"id_pedido":message["id_pedido"]})

    def publish_pedidos_enviados(message:dict)->bool:
        """Formato do Json de Pedidos:
            "id_pedido": int
        """
        try:
            Entrega.channel.basic_publish(exchange=exchange, routing_key = pedidos_enviados_key,body=json.dumps(message))
            print("Pedido Enviado com Sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar publicar pedido enviado:\n{e}")
            return False

    def run()->None:
        while True:
            pass

if __name__ == "__main__":
    Entrega.init()
    Entrega.run()