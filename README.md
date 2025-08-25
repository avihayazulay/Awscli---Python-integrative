# Awscli---Python-integrative-with-boto3-ec2-s3-route53
Requirements
Python 3.8+
boto3
click
AWS credentials-
aws configure
access your key

Install dependencies:
pip install boto3 click

Running the CLI
Run the CLI with Python 3:

python3 awscli.py <resource> <action> 

Use the --help for guidance:

python3 awscli.py --help
python3 awscli.py ec2cli --help
python3 awscli.py s3cli create --help

EC2
List: python3 awscli.py ec2cli list
Create: python3 awscli.py ec2cli create --type t3.micro --ami ubuntu
Start: python3 awscli.py ec2cli start --id <INSTANCE_ID>
Stop: python3 awscli.py ec2cli stop --id <INSTANCE_ID>

S3
List: python3 awscli.py s3cli list
Create: python3 awscli.py s3cli create --name mybucket --type Public
Upload: python3 awscli.py s3cli upload --bucket mybucket --file /path/to/file.txt --key file.txt

Route53

List zones: python3 awscli.py routecli list-zones
Create zone: python3 awscli.py routecli create-zone --name avi.com
Add record: python3 awscli.py routecli add-record --zone-id <ZONE_ID> --name sub.avi.com --ip 1.2.3.4
Update record: python3 awscli.py routecli update-record --zone-id <ZONE_ID> --name sub.avi.com --ip 5.6.7.8
Delete record: python3 awscli.py routecli delete-record --zone-id <ZONE_ID> --name sub.avi.com --ip 5.6.7.8
