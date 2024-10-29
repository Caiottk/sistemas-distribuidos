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

def process_invoice_request(ch, method, properties, body, public_key, private_key):
    message = json.loads(body)
    invoice_request_json = json.dumps(message["request"])
    signature = message["signature"]
    if verify_signature(public_key, invoice_request_json, signature):
        print("Requisição de nota recebida e verificada:", message["request"])
        # Gerar nota fiscal
        invoice = {"order_id": message["request"]["order_id"], "amount": message["request"]["amount"], "status": "gerada"}
        invoice_json = json.dumps(invoice)
        invoice_signature = sign_message(private_key, invoice_json)
        delivery = {
            "order_id": message["request"]["order_id"],
            "cliente_id": message["request"]["cliente_id"],
            "invoice": invoice,
            "gift_card": "link_para_download",
            "signature": invoice_signature.hex()
        }
        ch.basic_publish(exchange=method.exchange, routing_key='delivery.complete', body=json.dumps(delivery))
        print("Nota fiscal e produto digital enviados:", delivery)
    else:
        print("Falha na verificação da assinatura!")

def main(host, exchange):
    connection, channel = get_connection_channel(host, exchange)
    public_key, private_key = generate_keys()
    try:
        channel.queue_declare(queue='invoice_request_queue')
        channel.queue_bind(exchange=exchange, queue='invoice_request_queue', routing_key='invoice.request')
        channel.basic_consume(queue='invoice_request_queue', on_message_callback=lambda ch, method, properties, body: process_invoice_request(ch, method, properties, body, public_key, private_key), auto_ack=True)
        print("Aguardando requisições de nota...")
        channel.start_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    parser = get_args()
    args = parser.parse_args()
    main(args.host, args.exchange)