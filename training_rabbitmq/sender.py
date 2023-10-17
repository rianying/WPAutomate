import pika
import pandas as pd

# Read your dataset (assuming it's in a CSV file)
# Replace 'your_dataset.csv' with the actual path to your dataset
df = pd.read_csv('depo.csv')

# Create a connection to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare a queue named 'user_ids'
channel.queue_declare(queue='customers')

# Iterate through the rows of the dataset and send each user ID
for customer in df.iterrows():
    # Convert the user_id to a string before sending
    message = str(customer)
    channel.basic_publish(exchange='',
                          routing_key='customers',
                          body=message)
    print(f" [x] Sent '{message}'")

# Close the connection
connection.close()
