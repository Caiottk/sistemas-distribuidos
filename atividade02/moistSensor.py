import pika
import argparse
import json
import struct
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCYiXz7v1TEEGxC\nkDYtkZWiyQwX9OG1QWlu9BWie8mCjNJS0vzyKefk6NH/DY9g43AF+kObL8BTtS1z\ngxe+1U7l85vvUZcI+J8Zx+hyfKjab4vPDhjJ5C8nMxWGFO5GqDDqOwfnLjW90dvC\nWZMP5omab+b7wFgs0X/Vd6c0nZkSZrO8c2dPHhpVS/iSFo2+oNHg36SWdPtzw8AU\n6IlZ9lrJ5EKx457Zaph2o6MVZXElQqm5UVHKT+t1eGDCVDddsbIhF+Wi5AWwZivU\nKhUU2XDLed9AF7e/xeCKC9/phLfKBDMm8ZRoK2PxjbxrekTsXNKCEgLUP+c2vVeP\nheeFq4UvAgMBAAECggEAB+DqFLKwNSRIAzQhqD7hxLOvrTkXw13qjTGMQIU2Rkjx\nwBdnuzZQ5PDlj8/qfO2iZpyji0tvGqO8AkBeJJwt5BCuGDFVpL/6r8E0j11C921V\ngk9PFnZzvQmVbgR8vieHx0FfSiCH5BMHz8UCpIqaxuBKxOwNYds8SBFTEJOnSVzy\nMwVYjNC+NXEPcxg3dynNoT7Uk3Zz3psdvpnIgxVSrKScbKx7+8Q+C5/DZjTOc5Wi\ncDmnLOLwlphxRuFGBmJ0dUXAIBvMe0zZ0I4VPMclC8ZFw2xMqzo7R/vp3cO1rAbp\npxextO1oCnLEClF9a+pSsG02Qu3/1jWPHfM2ej4ckQKBgQC9VlB4gE9YHQW39L4H\nskI73zrBCQ72qd+KktsHl+oIgFX5srL7outDZt2vkJ7LNpT7UK7VXWSpTOWuuZwd\nWrqlP4MYO4r38B5Ot9u1lSBHblyIwTpSfHLNOFd7rLq1OufmsLy+F4SgABR6O8u2\nUvggWvQ2YjzYgJ1TLXKSzxIR2QKBgQDOPj1IpDUBbkCWqtUxA5OKgd+9pAJQ8P34\nuYYMi4hx5v3BX+y/7rWlsN/3Jq3xmy3LAbLKlXJejdYW5alv3/0cyJu64rPWiQwb\n7TKiIzOdws9TMONJnnaoXXzkYBBPkWkpJKdG9BMRGDWvnP/gZdWjWUPc6+d4kxRY\nhLAmi7/iRwKBgATWEZQiYuRzSVQbkkcMDJkO6KdJnfI7AJS/j4ywGrBA5vFL2TqI\nPM4p8HutjADQ0hlhRDX6/rk8V5mQ8CXnzWCvMKAL1U7j+UI1fA01U++/J+nuVZkJ\nyLzpNYLZNKOwb3/6/7czTpXvqpY8tMVhdSkOabKB69/z2RDo1kZdt65xAoGAOYeg\n/qdXZcvEVoLWrzJpMISjzbl3L+7ZWU0e+Fbfu64McKl6V9uVbd+VydJPSQrZTjxu\nDBZ97aQw6PgtOFjJuQK4dfwQ4DIgX5Xdvt6E4mfZ/0Gu1PVP8g0J7oZhZmCQbfqc\ncq1YuDcBmrf3pDejzUn0JSbkzXxxe3Of01C+OLcCgYAct5rrsclmRqSRQXnRt+yh\nD6mAw8Eez3SMOCMzstDR3WPRe+4ZcfiWAGNV4feO+p+VKQeG+pwSqXeyyzNtG72G\njftoAxr1RDqIMyj6FBj+gBdfc4b8WHetqf7sLvvdrsvwFYwmJfxAyyvd1pWs5XgX\nZ2snatsJvtKq7E5+0B22kg==\n-----END PRIVATE KEY-----\n"
queue = "humidity_data"
routing_key = "humidity_data.new"
connection, channel = None,None

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

def main(host, exchange):
    global private_key,connection, channel
    init(host, exchange)
    while True:
        humidity = input("Digite a Umidade:\n")
        try: 
            humidity = float(humidity)
        except:
            print("Valor não numérico\n")
            continue
        value = json.dumps({"humidity":humidity})
        byte_value = value.encode('utf-8')
        signature = sign_message(private_key, byte_value)

        message = {
            "value": value,
            "signature": signature.hex()
        }

        channel.basic_publish(exchange=exchange, routing_key=routing_key, body=json.dumps(message))
        print("Done\n")

def init(host, exchange):
    global connection, channel, private_key
    private_key = serialization.load_pem_private_key(
        private_key.encode('utf-8'),
        password=None
    )
    parser = get_args()
    args = parser.parse_args()
    connection, channel = get_connection_channel(host, exchange)

if __name__ == "__main__":
    main("localhost", "irrigation_system")