import boto3

key_id = 'AKIAIIG3GVFILFIAHBRQ'
access_key = '5wYkXHFF1Hw0Mru+NPuQT/XxBOIqNkVx18GxPSN3'
region_name = 'us-east-1'
endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'

client = boto3.client('mturk', endpoint_url=endpoint_url, region_name=region_name, aws_access_key_id=key_id, aws_secret_access_key=access_key)

response = client.notify_workers(
    Subject='Invitation to complete an evaluation task',
    MessageText=('Dear Participant, '
    			 'Thank you for participating in the task titled "Rate results from an information retrieval system". '
    			 'As a reward for performing exceptionally well, you are invited to take part in the next task titled "Evaluate an information retrieval system".'
    			 'Please take the test within 24 hours.'
    			 'Thanks in advance for your interest and time.'
    			 'Best Regards'),
    WorkerIds=[
        'A1GKEEI844CEKI', 'A1J1QKIGHFLF4M', 'A1NYV6LPHCYADS', 'A2BOXK0KVXGKPU', 'A2DYADMF9WPVO8', 'A2MJAXJEJ4SEQM', 'A2YO837C0O1E91',
        'A37JENVKZQ56U6', 'A39YBLQYIUBR76', 'A3EZ0H07TSDAPW', 'A3GNQDFPZALU92', 'A3IL3HGJW7K6Q1', 'A3SKEW89V5S0DI', 'AX8EX2QI5HIQQ',
        'AYJGJAIY0EXW'

    ]
)

print(response)