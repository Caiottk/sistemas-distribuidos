from defines import *
from auxFunc import *
import json

if __name__ == "__main__":
    connection, channel = get_connection_channel(host, exchange)
    channel.basic_publish(exchange=exchange, routing_key = pedidos_excluidos_key,body=json.dumps({"id_pedido":1}))