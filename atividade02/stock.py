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

def process_order(ch, method, properties, body, public_key, private_key):
    message = json.loads(body)
    order_json = json.dumps(message["order"])
    signature = message["signature"]
    if verify_signature(public_key, order_json, signature):
        print("Pedido recebido e verificado:", message["order"])
        # Processar pagamento e gerar nota
        payment_confirmation = {"status": "pago", "order_id": message["order"]["cliente_id"]}
        payment_confirmation_json = json.dumps(payment_confirmation)
        payment_signature = sign_message(private_key, payment_confirmation_json)
        payment_message = {
            "confirmation": payment_confirmation,
            "signature": payment_signature.hex()
        }
        ch.basic_publish(exchange=method.exchange, routing_key='order.paid', body=json.dumps(payment_message))
        print("Confirmação de pagamento enviada:", payment_message)
        # Enviar requisição de nota
        invoice_request = {"order_id": message["order"]["cliente_id"], "amount": 100}  # Exemplo de valor
        invoice_request_json = json.dumps(invoice_request)
        invoice_signature = sign_message(private_key, invoice_request_json)
        invoice_message = {
            "request": invoice_request,
            "signature": invoice_signature.hex()
        }
        ch.basic_publish(exchange=method.exchange, routing_key='invoice.request', body=json.dumps(invoice_message))
        print("Requisição de nota enviada:", invoice_message)
    else:
        print("Falha na verificação da assinatura!")

def main(host, exchange):
    connection, channel = get_connection_channel(host, exchange)
    public_key, private_key = generate_keys()
    try:
        channel.queue_declare(queue='order_queue')
        channel.queue_bind(exchange=exchange, queue='order_queue', routing_key='order.new')
        channel.basic_consume(queue='order_queue', on_message_callback=lambda ch, method, properties, body: process_order(ch, method, properties, body, public_key, private_key), auto_ack=True)
        print("Aguardando pedidos...")
        channel.start_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    parser = get_args()
    args = parser.parse_args()
    main(args.host, args.exchange)