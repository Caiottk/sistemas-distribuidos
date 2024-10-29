#docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4.0-management



import pika
import argparse
import json
import struct
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCStSCa8dO0KUmP\nPOxox7q4fgzMLyzWwA814FusLIishBVs8Gxx7D61j/VYxWYnRPlz+QhIiMg7WL8b\ncOxUaM3tesYRvQYY52i2cJ7Q7ISUf83njOAALrAChJqk0kEtSA/pVzAYci3kxLBe\nB+Kzp0bRIxOF7h8t/sFFtyvGTcLOC7qD2Rsn1LaO7EbR5PzP+rxo1YY5833IKea7\n66Ucgaqm8I4RFEozFCRmoLJID+tkoSMhLj9tAhQIOUpdn7IQS82Ivt7hGDwlX4kW\nYEVc4clGyvfqDS/CXFKwm67cqpiFw0i6lGNNiKxncQ3vRsYDCDgcVQIjqMr145OP\nTlJOOgJbAgMBAAECggEANuLBqIY5jEj4BrklvwueHSC3W/p4PX2MEz11PoRIu7YM\np/2IrNRUH6wUf5oWXjGtW8h641wdASryEGueVvQAusx4ZrF/oviMUdjvab1a2o23\n9F1dfmP5IHAIxQoOLUks/sDKMxMgfVpim0M6+rhlw59qUexkyNnq59Cf9WgpLdlf\nMm440KtKHDaMD3BNyg/CM1hKEnwJUS9yGHl6mtn3QzjZ2+2kBUD9P1UcRTJNDtvr\nFDd6YhgvkkcBfCha3DF0JZ2NDSKuu2PaHD4woqylU+qfBdOUjKsuDzgO3dzYUrKo\ndMCvsvIcv7ZwsopXM0r6rqukdRiMd2OF1+CebpF5cQKBgQC2ohFcGXbD8ghD8MJu\ncsfsi3AowGQz9YSaY/IfsAXuzEJ5AWUXLDvrqvmQgL3nmzeakiIUbMSbr52kWxXl\nk0lzNh52Du7vhDMarJU2YtTu4u2SafnFQWnNNKkmVXbtSEbE57ThUFAY41xkrt+U\nsPK/chMTDAqiKGb8A/UgSSwSiwKBgQDNpHyVYbI/BqbwPKxpqOgHtTwA7A+UhsyA\naLStT34uWWxcJYRGyaDc58tIfbBjomTknH1mjmJstGZsGL+HShmwujHqMdH4rVzX\naG1wj4b3hnuZwNiaRjq9dxSjZNaFntbgM8aAeUtk71BimM1fNoyABkQtbacB77Ue\nHYzdeerZcQKBgG+rWQH/b+cPro4cQEZYWHYCLGo+eQZsMNBWHE3Ty0zgCCUE/VLV\n8S2ANWhtz7A18CHLCJuEhhLLppBAQXtGO7r+dFGrf91j7/t3WyUN+TS3/JtxwQ8j\nmBWpBWQzDay4bM0pAChkexU8r9nAM2UvbL4yegdDbZ0JJy8hHFjJZPFRAoGAR4Hs\nBHHdbocco6sldPRUAuIlhFiRrl8VW42NTjq3MNzNjllJXugb9NTxXjq+jFba6Jf2\nDyRx20T73JjaeOvudQK5+qrqTaPTBeB9Ncfi8c2kyzlA2JyVLm7rEUouQnaSV5IJ\nc4E6E1YYSMDDoVkxkA8dxAI+MbEt9NPnuNf9LzECgYB/Jlpu3N3okBvOrAPLiXC9\np5TW4pggJheTcquRVLB+IsrdutOAnvZd5ou2IXnVxi0RQqigFFVxDAsmThDJzrUA\ndB1cBo8gUXr3fUL0OnYAPAbOoxmf3gyIDvQBWuCLRwfdoU2QrrJj5stjW32qXQ9u\now11Y3kPIFwEFdU/91fZCQ==\n-----END PRIVATE KEY-----\n"

humidity_queue = "humidity_data"
humidity_routing_key = "humidity_data.new"

temperature_queue = "temperature_data"
temperature_routing_key = "temperature_data.new"

actuators_queue = "actuators_schedule"
actuators_routing_key = "actuators_schedule.new"

connection, channel = None,None

public_keys = None
systems = ["moist_sensor","temperature_sensor","actuators"]

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

def sign_message(private_key, message):
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
def verify_signature(message,system):
    global public_keys
    if system not in public_keys.keys():
        return False
    try:
        message = json.loads(message.decode('utf-8'))
        signature = bytes.fromhex(message['signature']) if isinstance(message['signature'], str) else message['signature']
        value_bytes = message['value'].encode('utf-8')
        public_keys[system].verify(
            signature,
            value_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print("Signature is invalid:", e)

def calc_irrigation_based_on_humidity(humidity):
    if humidity < 30:
        period = 50-humidity
        schedule = {
            "on":True,
            "period": period,
            "period_unit": "seconds"
        }
        return json.dumps(schedule)
    else:
        return None

def on_humidity_data_received(ch, method, properties, body):
    global host, exchange,actuators_queue,actuators_routing_key
    if(verify_signature(body,"moist_sensor")):
        message = json.loads(body.decode('utf-8'))
        humidity = float(json.loads(message["value"])["humidity"])
        print(f" [x] humidity received:{humidity}")
        schedule = calc_irrigation_based_on_humidity(humidity)
        if schedule is not None:
            signature = sign_message(private_key, schedule.encode('utf-8'))
            message = {
                "value": schedule,
                "signature": signature.hex()
            }
            channel.basic_publish(exchange=exchange, routing_key=actuators_routing_key, body=json.dumps(message))
            print(f" [x] schedule plan sent: {message['value']}")

def on_humidity_data_received(ch, method, properties, body):
    global host, exchange,actuators_queue,actuators_routing_key
    if(verify_signature(body,"moist_sensor")):
        message = json.loads(body.decode('utf-8'))
        humidity = float(json.loads(message["value"])["humidity"])
        print(f" [x] humidity received:{humidity}")
        schedule = calc_irrigation_based_on_humidity(humidity)
        if schedule is not None:
            signature = sign_message(private_key, schedule.encode('utf-8'))
            message = {
                "value": schedule,
                "signature": signature.hex()
            }
            channel.basic_publish(exchange=exchange, routing_key=actuators_routing_key, body=json.dumps(message))
            print(f" [x] schedule plan sent: {message['value']}")

def calc_irrigation_based_on_temperature(temperature):
    if temperature < 5:
        period = 10
        schedule = {
            "on":True,
            "period": period,
            "period_unit": "seconds"
        }
        return json.dumps(schedule)
    else:
        return None
    
def on_temperature_data_received(ch, method, properties, body):
    global host, exchange,actuators_queue,actuators_routing_key
    if(verify_signature(body,"temperature_sensor")):
        message = json.loads(body.decode('utf-8'))
        temperature = float(json.loads(message["value"])["temperature"])
        print(f" [x] temperature received:{temperature}")
        schedule = calc_irrigation_based_on_temperature(temperature)
        if schedule is not None:
            signature = sign_message(private_key, schedule.encode('utf-8'))
            message = {
                "value": schedule,
                "signature": signature.hex()
            }
            channel.basic_publish(exchange=exchange, routing_key=actuators_routing_key, body=json.dumps(message))
            print(f" [x] schedule plan sent: {message['value']}")

def main():
    global public_keys,connection,channel,host,exchange,humidity_queue,humidity_routing_key,temperature_queue,temperature_routing_key
    init()
    
    channel.queue_declare(queue=humidity_queue)
    channel.queue_bind(exchange=exchange, queue=humidity_queue, routing_key=humidity_routing_key)
    channel.basic_consume(queue=humidity_queue, on_message_callback=on_humidity_data_received, auto_ack=True)

    channel.queue_declare(queue=temperature_queue)
    channel.queue_bind(exchange=exchange, queue=temperature_queue, routing_key=temperature_routing_key)
    channel.basic_consume(queue=temperature_queue, on_message_callback=on_temperature_data_received, auto_ack=True)
    channel.start_consuming()

    while True:
        pass
    
def load_private_key():
    global  private_key
    private_key = serialization.load_pem_private_key(
        private_key.encode('utf-8'),
        password=None
    )

def load_public_keys():
    global systems,public_keys
    with open("public.json", "r") as json_file:
        public_keys = json.load(json_file)
    for key,value in public_keys.items():
        public_keys[key] = serialization.load_pem_public_key(
            value.encode('utf-8')
        )

def init():
    global connection, channel,host, exchange
    load_private_key()
    load_public_keys()
    parser = get_args()
    args = parser.parse_args()
    connection, channel = get_connection_channel(host, exchange)

if __name__ == "__main__":
    host, exchange = "localhost", "irrigation_system"
    main()