import boto3
import botocore
import click
import json
import time
import getpass


ec2 = boto3.client("ec2")
s3 = boto3.client("s3")
route53 = boto3.client("route53")

OWNER = getpass.getuser()
CLI_TAG = {"Key": "MadeByCli", "Value": "yes"}


@click.group()
def cli():
    pass


@cli.group()
def ec2cli():
    pass


@ec2cli.command("list")
def list_instances():
    instances = ec2.describe_instances(
        Filters=[{"Name": "tag:MadeByCli", "Values": ["yes"]}]
    )
    for r in instances["Reservations"]:
        for inst in r["Instances"]:
            print(f"ID: {inst['InstanceId']} State: {inst['State']['Name']}")


@ec2cli.command("create")
@click.option("--type", required=True, type=click.Choice(["t3.micro", "t2.small"]))
@click.option("--ami", required=True, type=click.Choice(["ubuntu", "amazon"]))
def create_instance(type, ami):
    if ami == "ubuntu":
        images = ec2.describe_images(
            Owners=["099720109477"], Filters=[{"Name": "name", "Values": ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]}]
        )
    else:
        images = ec2.describe_images(
            Owners=["amazon"], Filters=[{"Name": "name", "Values": ["amzn2-ami-hvm-*-x86_64-gp2"]}]
        )
    latest = sorted(images["Images"], key=lambda x: x["CreationDate"], reverse=True)[0]

    instances = ec2.run_instances(
        ImageId=latest["ImageId"],
        InstanceType=type,
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Owner", "Value": OWNER},
                    CLI_TAG,
                ],
            }
        ],
    )
    print("Created:", instances["Instances"][0]["InstanceId"])


@ec2cli.command("start")
@click.option("--id", required=True)
def start_instance(id):
    ec2.start_instances(InstanceIds=[id])
    print("Started:", id)


@ec2cli.command("stop")
@click.option("--id", required=True)
def stop_instance(id):
    ec2.stop_instances(InstanceIds=[id])
    print("Stopped:", id)


#S3
@cli.group()
def s3cli():
    pass


@s3cli.command("list")
def list_buckets():
    response = s3.list_buckets()
    for bucket in response["Buckets"]:
        try:
            tags = s3.get_bucket_tagging(Bucket=bucket["Name"])
            has_cli = any(t["Key"] == "MadeByCli" and t["Value"] == "yes" for t in tags["TagSet"])
            owner_ok = any(t["Key"] == "Owner" and t["Value"] == OWNER for t in tags["TagSet"])
            if has_cli and owner_ok:
                print("Bucket:", bucket["Name"])
        except botocore.exceptions.ClientError:
            continue


@s3cli.command("create")
@click.option("--name", required=True)
@click.option("--type", required=True, type=click.Choice(["Private", "Public"]))
def create_bucket(name, type):
    try:
        s3.create_bucket(Bucket=name)
    except botocore.exceptions.ClientError as e:
        print("Error:", e)
        return

    if type == "Public":
        s3.put_public_access_block(
            Bucket=name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        )
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{name}/*",
                }
            ],
        }
        s3.put_bucket_policy(Bucket=name, Policy=json.dumps(policy))

    s3.put_bucket_tagging(
        Bucket=name,
        Tagging={"TagSet": [{"Key": "Owner", "Value": OWNER}, CLI_TAG]},
    )
    print("Bucket created:", name)


@s3cli.command("upload")
@click.option("--bucket", required=True)
@click.option("--file", required=True, type=click.Path(exists=True))
@click.option("--key", required=True)
def upload_file(bucket, file, key):
    try:
        with open(file, "rb") as f:
            s3.put_object(Body=f, Bucket=bucket, Key=key)
        print(f"Uploaded {file} to {bucket}/{key}")
    except Exception as e:
        print("Error:", e)


# -------------------- Route53 --------------------
@cli.group()
def routecli():
    """Manage Route53"""
    pass


@routecli.command("list-zones")
def list_zones():
    zones = route53.list_hosted_zones()["HostedZones"]
    for z in zones:
        tags = route53.list_tags_for_resource(ResourceType="hostedzone", ResourceId=z["Id"].split("/")[-1])
        has_cli = any(t["Key"] == "MadeByCli" and t["Value"] == "yes" for t in tags["ResourceTagSet"]["Tags"])
        owner_ok = any(t["Key"] == "Owner" and t["Value"] == OWNER for t in tags["ResourceTagSet"]["Tags"])
        if has_cli and owner_ok:
            print(f"Zone: {z['Name']} Id: {z['Id']}")


@routecli.command("create-zone")
@click.option("--name", required=True)
def create_zone(name):
    response = route53.create_hosted_zone(Name=name, CallerReference=f"{name}-{int(time.time())}")
    zone_id = response["HostedZone"]["Id"].split("/")[-1]
    route53.change_tags_for_resource(
        ResourceId=zone_id,
        ResourceType="hostedzone",
        AddTags=[{"Key": "Owner", "Value": OWNER}, CLI_TAG],
    )
    print("Zone created:", name)


@routecli.command("add-record")
@click.option("--zone-id", required=True)
@click.option("--name", required=True)
@click.option("--ip", required=True)
def add_record(zone_id, name, ip):
    route53.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            "Changes": [
                {
                    "Action": "CREATE",
                    "ResourceRecordSet": {
                        "Name": name,
                        "Type": "A",
                        "TTL": 60,
                        "ResourceRecords": [{"Value": ip}],
                    }
                }
            ]
        }
    )
    print("Record created:", name)


if __name__ == "__main__":
    cli()
