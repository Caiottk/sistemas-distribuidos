from defines import *
from auxFunc import *
import json

class Pagamento:
    connection,channel = None,None

    def init()->None:
        Pagamento.connection, Pagamento.channel = get_connection_channel(host, exchange)
        if (Pagamento.connection and Pagamento.channel) is not None:
            print("Conexão com o Broker estabelecida com sucesso!")
            Pagamento.subscribe_to_topics()

    def subscribe_to_topics()->None:
        #Se inscreve no tópio de Pagamentos Recusados
        Pagamento.channel.queue_declare(queue=e_commerce_queue)
        Pagamento.channel.queue_bind(exchange=exchange, queue=e_commerce_queue, routing_key=pedidos_criados_key)
        Pagamento.channel.basic_consume(queue=e_commerce_queue, on_message_callback=Pagamento.on_pedidos_criados, auto_ack=True)
        Pagamento.channel.start_consuming()

    def on_pedidos_criados(ch, method, properties, body):
        """TODOO: Pedido Criado"""
        return 
    
    def publish_pagamentos_recusados(message:dict)->bool:
        """Formato do Json de Pedidos:
            "id_pedido": int
        """
        try:
            Pagamento.channel.basic_publish(exchange=exchange, routing_key = pagamentos_recusados_key,body=json.dumps(message))
            print("Pagamento Recusado publicado com sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar Pagamento Recusado\n{e}")
            return False

    def publish_pagamentos_aprovados(message:dict)->bool:
        """Formato do Json de Pedidos:
            "id_pedido": int
        """
        try:
            Pagamento.channel.basic_publish(exchange=exchange, routing_key = pagamentos_aprovados_key, body=json.dumps(message))
            print("Pagamento Aprovados publicado com sucesso")
            return True
        except Exception as e:
            print(f"Erro ao publicar Pagamento Aprovados\n{e}")
            return False

    def run()->None:
        while True:
            pass

if __name__ == "__main__":
    Pagamento.init()
    Pagamento.run()