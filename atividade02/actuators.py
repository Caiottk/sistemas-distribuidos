#docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4.0-management



import pika
import argparse
import json
import struct
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDA2EQTFKB72CzY\n4v4WfjO8teQghkMgMV4AdVi+/9SFL4YwctKfMsDmIVLTR8d+G7wWkuRkZLXPcjpi\nf5apjBk7tuGBQxM+NFZA+KHBMTzK753AtbtejSZat77goG37brbLq8YYfJP0UVTc\nMdAlkk/XgytJKnTXgiRvG2mF6Ojy/+Tk1dRqCjzNX2BDP8jo+cMtaXNwSaJVbcfk\nR7sLf2WId+5pE/wPkeKFWIPJuyDZ03wks0Ngsv80luAjVngc8b/AA6l77xa0odh2\nx8tuTlF54Pv/V1wWJ/2IGTKTvEG9YxeyAycjVsCNStVo5HelRSkAovBVeMFsdBNE\ntKkl/vjlAgMBAAECggEAF/XW8XL25KRNoC4F6WgJSBlmbIcaCIIxvodV/Tc+ocSv\nnM3rbvXIo19BEfjBZ+EMy9Y48+NSdqGn8OyO3OaIDRQSLTQXDDvG+sAZou4Z8lH2\nzQaXbu5FNXDOkczFFYAiTKh9TrYN0QWY8FntFXn6GxoUUv0oMs2b9sUWZZm0ddqP\nutkSIDlnIWF4jWy6XsBNLhzGJS1etfETqz6m9K0Kz17zKBAll5O2qcqfzOgy04Sa\n+NG6CPg8YiOWMUytIo0hQ55X4G25HqGBPmLPoKX4mQhRYzdtyruONNdADpjOiaAp\nF1MpKUtd2e+jffvskv41fdZdj1EOHd+5VCbca2SKgQKBgQDSMr4LjhuKkNLW8IOD\nnT/iJJeLAjASEW23WWrbMYGxw8Ugl+1EGDlQmPn1+30C1CQqCGzgansOKhjgldTk\ntKVbc1ihdthNQ0Bz4FBDuDFKS3OWaaBrXn+k+cxkcomtS36UuEqJWJhOVwDsKpok\nNRx2+6MeRaRlIa7pAGaS+S6XZQKBgQDq3YQ18XWZBXj1ummXsLPqZ+6onkeYAWtK\nr8cexDIso2uB3ihPLEWUxrhPNadIApMUumgsIEB3Vi665sH9ERgPO8Ilon4+SF9I\nV97Ad8pR62zzieo/ncvDjc5kY639TdFn1hG7DiPzRH3ZwXjkpEythbUN0FW36loL\nyGHYAxyDgQKBgELK3vrbAENqu6STLqcu27Lnf8QrQM0s/pkpb7wRIi4zkDtIK5vc\nurGyupMAg/vXH1q/7KDvFQUuOVN8KPc3s+e4YmyEUD1U5nEr0TWDnR4HlcYw8EnN\n8G+i9ODiSH9pouJtITo9jcAvA1sIOozQ16ezVGT1KkT8jBD8EJwZVEXFAoGADTPO\njsm39pYcKpQEA4bnVjHpdIkRNTY/Nb+TzeLxfxjgnjhCw9CVSLuy+KDnemDKq8ue\nt3xIo2ywy8jU9sjTNWgCjeMIfa/Ly2FFIESbludJBJeoF1NjdOavx2zjBu4s601Z\nSc6NrssW1/rMNO4XcVmmx9QCPYhq72agOWhTXgECgYA741NRZfn89QA4L9xlI5c4\nafrINrbOr9stGBnCdJBpb6CrCUdp/9eZQq1lRkDOTimKMiyYqfUsAGilBQXP/bYq\nPqZw7qUrHsADW04p/v5vBmBNNiMPXmXRZMSdUAOtiUNuTiRa/7swMMGdh0O7IiUB\nMMUImGuWybWUb6uPxnWbiw==\n-----END PRIVATE KEY-----\n"

actuators_queue = "actuators_schedule"
actuators_routing_key = "actuators_schedule.new"

connection, channel = None,None

public_keys = None
systems = ["moist_sensor","temperature_sensor","irrigation_system"]

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

def on_actuators_data_received(ch, method, properties, body):
    global host, exchange,actuators_queue,actuators_routing_key
    if(verify_signature(body,"irrigation_system")):
        message = json.loads(body.decode('utf-8'))
        schedule = message["value"]
        print(f" [x] schedule received:{schedule}")
    

def main():
    global public_keys,connection,channel,host,exchange,actuators_queue,actuators_routing_key
    init()
    channel.queue_declare(queue=actuators_queue)
    channel.queue_bind(exchange=exchange, queue=actuators_queue, routing_key=actuators_routing_key)
    channel.basic_consume(queue=actuators_queue, on_message_callback=on_actuators_data_received, auto_ack=True)
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