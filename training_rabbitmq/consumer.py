import pika

# Create a connection to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare the queue ('user_ids' in this case)
channel.queue_declare(queue='customers')

# Callback function to handle incoming messages
def callback(ch, method, properties, body):
    print(f" [x] Received {body}")

# Set up a consumer that uses the callback function
channel.basic_consume(queue='customers',
                      on_message_callback=callback,
                      auto_ack=True)

print(' [*] Waiting for user IDs. To exit, press CTRL+C')
channel.start_consuming()
