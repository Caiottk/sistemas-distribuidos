from defines import *
from auxFunc import *
import json
import threading

from flask import Flask, jsonify, request
from flask_cors import CORS
#docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4.0-management
class Principal:
    connection,channel = None,None
    products = [

    ]

    def init()->None:
        Principal.connection, Principal.channel = get_connection_channel(host, exchange)
        if (Principal.connection and Principal.channel) is not None:
            print("Conexão com o Broker estabelecida com sucesso!")
            Principal.subscribe_to_topics()
            Principal.publish_get_pedidos()

    def subscribe_to_topics()->None:
        #Se inscreve no tópio de Pagamentos Recusados
        Principal.channel.queue_declare(queue=e_commerce_queue)
        Principal.channel.queue_bind(exchange=exchange, queue=e_commerce_queue, routing_key=pagamentos_recusados_key)
        Principal.channel.basic_consume(queue=e_commerce_queue, on_message_callback=Principal.on_pagamento_recusado, auto_ack=True)

        Principal.channel.queue_declare(queue=e_commerce_queue)
        Principal.channel.queue_bind(exchange=exchange, queue=e_commerce_queue, routing_key=pagamentos_recusados_key)
        Principal.channel.basic_consume(queue=e_commerce_queue, on_message_callback=Principal.on_pagamento_recusado, auto_ack=True)

        Principal.channel.queue_declare(queue=e_commerce_queue)
        Principal.channel.queue_bind(exchange=exchange, queue=e_commerce_queue, routing_key=lista_produtos)
        Principal.channel.basic_consume(queue=e_commerce_queue, on_message_callback=Principal.on_lista_produtos, auto_ack=True)

    def start_consuming():
        print("Consumindo")
        Principal.channel.start_consuming()

    def on_lista_produtos(ch, method, properties, body):
        message = json.loads(body.decode('utf-8'))
        Principal.produtos = message

    def on_pagamento_recusado(ch, method, properties, body):
        """Se algum pedido for recusado, ele exclui o pedido (publica no tópico peididos excluidos)"""
        message = json.loads(body.decode('utf-8'))
        if "id_pedido" not in message.keys():
            print("Erro: id_pedido faltante")
            return
        Principal.publish_pedidos_excluidos({"id_pedido":message["id_pedido"]})

    def publish_pedidos_criados(message:dict)->bool:
        """Formato do Json de Pedidos:
            "id_pedido": int
            "cod_produto": int
            "quantidade": int
        """
        try:
            Principal.channel.basic_publish(exchange=exchange, routing_key= pedidos_criados_key,body=json.dumps(message))
            print("Pedido Criado com Sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar publicar pedido criado:\n{e}")
            return False

    def publish_get_pedidos()->bool:
        try:
            Principal.channel.basic_publish(exchange=exchange, routing_key= pedidos_criados_key,body=json.dumps({"get_all":0}))
            print("Pedido Criado com Sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar publicar pedido criado:\n{e}")
            return False

    def publish_pedidos_excluidos(message:dict)->bool:
        """Formato do Json de Pedidos:
            "id_pedido": int
        """
        try:
            Principal.channel.basic_publish(exchange=exchange, routing_key = pedidos_excluidos_key,body=json.dumps(message))
            print("Pedido Excluido com Sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar publicar pedido excluido:\n{e}")
            return False