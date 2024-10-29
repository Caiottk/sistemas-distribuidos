import pika
import argparse
import json
import rsa

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default="localhost", action='store', help='RabbitMQ host')
    parser.add_argument('--exchange', default="default_pc", action='store', help='RabbitMQ exchange')
    return parser

def get_connection_channel(host, exchange):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type='topic')
    return connection, channel

def generate_keys():
    (public_key, private_key) = rsa.newkeys(512)
    return public_key, private_key

def sign_message(private_key, message):
    return rsa.sign(message.encode('utf-8'), private_key, 'SHA-1')

def verify_signature(public_key, message, signature):
    try:
        rsa.verify(message.encode('utf-8'), bytes.fromhex(signature), public_key)
        return True
    except rsa.VerificationError:
        return False

def send_order(channel, exchange, order, private_key):
    order_json = json.dumps(order)
    signature = sign_message(private_key, order_json)
    message = {
        "order": order,
        "signature": signature.hex()
    }
    channel.basic_publish(exchange=exchange, routing_key='order.new', body=json.dumps(message))
    print("Pedido enviado:", message)

def process_invoice(ch, method, properties, body, public_key):
    message = json.loads(body)
    order_json = json.dumps(message["order"])
    signature = message["signature"]
    if verify_signature(public_key, order_json, signature):
        print("Nota fiscal recebida e verificada:", message["order"])
        print("Pedido confirmado para o cliente:", message["order"]["order_id"])
    else:
        print("Falha na verificação da assinatura!")

def main(host, exchange):
    connection, channel = get_connection_channel(host, exchange)
    public_key, private_key = generate_keys()
    try:
        order = {"cliente_id": 1, "produto_id": 101, "quantidade": 2}
        send_order(channel, exchange, order, private_key)

        channel.queue_declare(queue='invoice_queue')
        channel.queue_bind(exchange=exchange, queue='invoice_queue', routing_key='invoice.generated')
        channel.basic_consume(queue='invoice_queue', on_message_callback=lambda ch, method, properties, body: process_invoice(ch, method, properties, body, public_key), auto_ack=True)
        print("Aguardando nota fiscal...")
        channel.start_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    parser = get_args()
    args = parser.parse_args()
    main(args.host, args.exchange)