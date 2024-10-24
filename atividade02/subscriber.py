import pika
import argparse

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default="localhost", action='store', help='RabbitMQ host')
    parser.add_argument('--exchange', default="default_pc", action='store', help='RabbitMQ exchange')
    return parser

def get_connetion_channel(host, exchange):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange)
    return connection, channel

def main(host, exchange):
    connection, channel = get_connetion_channel(host, exchange)
    try:
        print("A fazer")
    finally:
        connection.close()


if __name__ == "__main__":
    parser = get_args()
    args = parser.parse_args()
    main(args.host, args.exchange)