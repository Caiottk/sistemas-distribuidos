import pika
import argparse
import json
import struct
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDb7PHbLOiMkk+E\nSIE14djB633xuxRbDHkYyyOI5kHSrEq6ltDV6bDl+8vxtO3uNjc1ZWTUzUw43q33\nFz42IcGvJlXorjEr8aIPMG+LQd9xz7kYZ7ubm/GAesgbAZVqzZFn4Z7sj9GRuJGW\nOhfPtjydTOrkg5YXh5R/IBGhSKOYuygubcOUzCiH+/fBd6IMg6fMOQ7DRpl2Yz/t\nLBF6h2O4vIz5381WFYQ+LV/d9CReGd8U+t4vpHJbe88W6HXsbY5hByI5+UrVbH6R\nSs33XMOsix/Dk5lSUYFTpECqtpO4REQcOV/VdyO/+3ZWapnFRTRoPM27cftDal/1\nHqIN7JDJAgMBAAECggEAJiYiqQaP+0xo8zUhhr97ul23bd5qEEYoXmrkadupONpu\npxHAvY6JQ0erj6y3Jh5s8rv5IunOykGkUyuKvNibsJ55ggBvYqRKXJCmFLWzRRqH\njMp3sm05VfRWcErUyJ9KlQa/6uCitYCa7oB6v2ro9k9Qop2JxGCeG3QsYroHONeR\n9cdMhepfM998vJqZM6KMuFXrz49E1AK9fHL8Nywn4fz7tZzc/KibGA5OYZLjLn5N\nbHPPVH7DhQ4DCsC3NdKZhwyQMz5kTXS8INmncB4YNWeByjhnAGLTiblmIZ059Hki\n7bMiCIuE7fTAJFUGXPoG2bGv729ZG8zcGlIj1GvWdQKBgQDtCo8FwIGAQ3F6tKtr\njm56gsWC/SMBqRrcv/4fRdUUTrhjaHqxUXhhrUDJET3+sK/WzEQ3nj+p2Y91dKuk\nTlNkRhGgDmwID0pbCZ4C/dj1I4339aydGrZ8K8+ayFobsjLIK8KEhp3L5YwZcT5v\n4nRmpYT6oS8MVye7jZGFEyLWNQKBgQDtg/DiiptOUPeUH8d4rQGgz61ta0MsLY+D\nZv9OTH2Xom3T4axM8gRLOdRA00rPmJtseGc1gsKLuNFgQQMhyKrIsOYWtXdqn997\nJ5HDhTt9yzTUOG9GjoVdRU8rs8XcdX1S0tVuPVKQEQcmJmZ3Vu5UclG7guZz93KA\nqbqKppYSxQKBgEsqo/vg9a/ksyGEFS/ANMxol5VYDDfElh4WS9FC5bTQ2au8P9vm\nx9PBit+3tf8DrF7i22b/qZSExvcqDhvGMq+DgKdOq3dK0ftYa2DrelcR9T0CDMCs\n7d0mT2j3y4so0O2k4sP/pB46JlkTDgeQufSq3CZV4oN5R8IzvEeEr/FZAoGBAJ6/\nkBIqaDFJJqDnOLBsmej8xcKbbZMqhIBkKAISV+Mwmk2CyWHIZJxO85G8Z4UnT8KJ\nGxqF4jf2+GJoMYq0D4oBylelREKMxpcO1HslIqUqW434hk9XVMYJXCguiPGXyYLB\nDgwXioZmCywxgE0FWlgw7HXywMsDuZFLYDXpr+atAoGASVS5YS+oryWPuJwCe2FP\nIhkNxDyjCYYduTxq7/77MKHKTt5+zsN+ULFxyGACVEGe6SDuzKXdMpMIG73f49uE\n3ou1gMQWDFqZbqpiiO95Ndkf23tfKPLr9a7bBGsYhQI8L81RcK9PsEmv17jlTSTA\njtVFi3CErySakXRjntG+0xg=\n-----END PRIVATE KEY-----\n"
queue = "temperature_data"
routing_key = "temperature_data.new"
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
        temperature = input("Digite a Temperatura:\n")
        try: 
            temperature = float(temperature)
        except:
            print("Valor não numérico\n")
            continue
        value = json.dumps({"temperature":temperature})
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