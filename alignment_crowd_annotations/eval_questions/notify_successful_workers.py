import boto3

key_id = 'xxxxxxx'
access_key = 'yyyyyyy'
region_name = 'us-east-1'
endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'

client = boto3.client('mturk', endpoint_url=endpoint_url, region_name=region_name, aws_access_key_id=key_id, aws_secret_access_key=access_key)

message_first = ('Dear Participant, '
    			 'Thank you for participating in the task titled "Rate results from an information retrieval system". '
    			 'As a reward for performing exceptionally well, you are invited to take part in the next task titled "Evaluate an information retrieval system".'
    			 'Please take the test within 24 hours.'
    			 'Thanks in advance for your interest and time.'
    			 'Best Regards')

message_subsequent = ('Dear Participant, '
    			 'Thank you for participating in the previous annotation tasks. '
    			 'As a reward for performing exceptionally well, you are invited to take part in the next task titled "Evaluate an information retrieval system".'
    			 'Please take the test within 24 hours.'
    			 'Thanks in advance for your interest and time.'
    			 'Best Regards')

response = client.notify_workers(
    Subject='Invitation to complete an evaluation task',
    MessageText=message_subsequent,
    WorkerIds=['a', 'b']
)

print(response)