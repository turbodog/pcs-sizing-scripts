"""Gathers data for Prisma Cloud sizing in AWS"""

# Questions / TODOs
# - Does this need pagination?
# - Need to get list of ELBv1?
# x Org support
# x Multi-account support via credentials file
# - Compute support
# - Data security support
# - IAM calculation
# - Save time by skipping disabled regions (https://stackoverflow.com/questions/56182935/how-to-identify-disabled-regions-in-aws) (https://austincloud.guru/2020/06/11/excluding-disabled-regions/)

import datetime
import argparse
import sys
import os

import botocore
import boto3

starttime = datetime.datetime.now()
print('Start time: %s' % starttime)

parser = argparse.ArgumentParser()
parser.add_argument('--nocsv', action='store_true')
parser.add_argument('--awsorg', action='store_true')
parser.add_argument('--profiles', action='store_true')
parser.add_argument('--skipdefault', action='store_true')
args = parser.parse_args()

try:
    accountid = boto3.client('sts').get_caller_identity().get('Account')
except botocore.exceptions.ClientError as error:
    print(error.response['Error'])
    print('Exiting')
    sys.exit(1)
except botocore.exceptions.NoCredentialsError as error:
    print(error)
    print('Exiting')
    sys.exit(1)
except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")
    print('Exiting')
    raise

ec2_total = 0
rds_total = 0
natgw_total = 0
redshift_total = 0
elb_total = 0

credentialsfile = os.path.expanduser('~/.aws/credentials')
profileenvvar = 'AWS_PROFILE'

f = None
if not args.nocsv:
    outputfile = 'sizing.csv'
    f = open(outputfile, 'w')
    print('Account ID, Service, Count', file=f)
print('%-*s\t%-*s\t%s' % (16, 'Account ID', 10, 'Service', 'Count'))

def scan_account(assumedrole, credentials, accountid, session):
    """Scan an individual AWS account"""
    ec2_account_total = 0
    rds_account_total = 0
    natgw_account_total = 0
    redshift_account_total = 0
    elb_account_total = 0

    # Count EC2
    if assumedrole:
        ec2client = session.client('ec2', aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
    else:
        ec2client = session.client('ec2')
    regions = ec2client.describe_regions()

    for region in regions['Regions']:
        if assumedrole:
            ec2 = session.resource('ec2', region_name=region['RegionName'], aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
        else:
            ec2 = session.resource('ec2', region_name=region['RegionName'])
        # aws ec2 describe-instances --max-items 99999 --region="${1}" --filters "Name=instance-state-name,Values=running"
        for instance in ec2.instances.filter(Filters=[{'Name':'instance-state-name', 'Values':['running']}]):
            ec2_account_total += 1

    if not args.nocsv:
        print('%s, EC2, %d' % (accountid, ec2_account_total), file=f)
    print('%-*s\t%-*s\t%s' % (16, accountid, 10, 'EC2', ec2_account_total))

    return ec2_account_total, rds_account_total, natgw_account_total, redshift_account_total, elb_account_total

"""
    # Count RDS
    if assumedrole:
        rdsregions = session.Session(aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken']).get_available_regions('rds')
    else:
        try:
            rdsregions = session.Session().get_available_regions('rds')
        except:
            rdsregions = session.get_available_regions('rds')
    for region in rdsregions:
        instances = {'DBInstances': []}
        if assumedrole:
            rds = session.client('rds', region_name=region, aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
        else:
            rds = session.client('rds', region_name=region)
        try:
            instances = rds.describe_db_instances()
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'InvalidClientTokenId':
                print('Region %s not enabled for account ID %s' % (region, accountid))
            else:
                print(error.response['Error'])
            continue

        # aws rds describe-db-instances --max-items 99999
        rds_account_total = len(instances['DBInstances'])
    if not args.nocsv:
        print('%s, RDS, %d' % (accountid, rds_account_total), file=f)
    print('%-*s\t%-*s\t%s' % (16, accountid, 10, 'RDS', rds_account_total))

    # Count NAT Gateways
    # aws ec2 describe-nat-gateways --max-items 99999

    for region in regions['Regions']:
        if assumedrole:
            natgwclient = session.client('ec2', aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
#            natgw = session.resource('ec2', region_name=region['RegionName'], aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
        else:
            natgwclient = session.client('ec2', region_name=region['RegionName'])
#            natgw = session.resource('ec2', region_name=region['RegionName'])
        natgws = natgwclient.describe_nat_gateways()
        natgw_account_total = len(natgws['NatGateways'])

    if not args.nocsv:
        print('%s, NATGW, %d' % (accountid, natgw_account_total), file=f)
    print('%-*s\t%-*s\t%s' % (16, accountid, 10, 'NATGW', natgw_account_total))

    # Count Redshift
    #aws redshift describe-clusters --max-items 99999
    for region in regions['Regions']:
        if assumedrole:
            redshift = session.client('redshift', region_name=region['RegionName'], aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
        else:
            redshift = session.client('redshift', region_name=region['RegionName'])
        clusters = redshift.describe_clusters()
        redshift_account_total = len(clusters['Clusters'])

    if not args.nocsv:
        print('%s, Redshift, %d' % (accountid, redshift_account_total), file=f)
    print('%-*s\t%-*s\t%s' % (16, accountid, 10, 'Redshift', redshift_account_total))

    # Count ELBs
    # aws elb describe-load-balancers --max-items 99999
    for region in regions['Regions']:
        if assumedrole:
            elb = session.client('elbv2', region_name=region['RegionName'], aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
        else:
            elb = session.client('elbv2', region_name=region['RegionName'])
        lbs = elb.describe_load_balancers()
        elb_account_total = len(lbs['LoadBalancers'])

    if not args.nocsv:
        print('%s, ELB, %d' % (accountid, elb_account_total), file=f)
    print('%-*s\t%-*s\t%s' % (16, accountid, 10, 'ELB', elb_account_total))

    return ec2_account_total, rds_account_total, natgw_account_total, redshift_account_total, elb_account_total
"""
#
# Main
#

master_accountid = accountid
accounts = {'Accounts': [{'Id':accountid}]}

if args.awsorg:
    try:
        client = boto3.client('organizations')
        org = client.describe_organization()
        master_accountid = org['Organization']['MasterAccountId']
        accounts = client.list_accounts()
    except Exception as error:
        print(error.response['Error'])
        print('Exiting')
        sys.exit(1)
elif args.profiles:
    accounts = {'Accounts': []}
    profiles = boto3.session.Session().available_profiles
    for profile in profiles:
        accounts['Accounts'].append({'Id':profile})

for account in accounts['Accounts']:
    session = boto3
    credentials = None
    if args.profiles:
        assumedrole = False
        if args.skipdefault and account['Id'] == 'default':
            print('Skipping default profile')
            continue
        session = boto3.session.Session(profile_name=account['Id'])
    elif account['Id'] != master_accountid:
        assume_role_arn = "arn:aws:iam::%s:role/OrganizationAccountAccessRole" % account['Id']
        stsclient = boto3.client('sts')
        assumed_role_object = stsclient.assume_role(RoleArn=assume_role_arn, RoleSessionName="AssumeRoleSession1")
        credentials = assumed_role_object['Credentials']
        assumedrole = True
    else:
        assumedrole = False
        credentials = None
    ec2_account_total, rds_account_total, natgw_account_total, redshift_account_total, elb_account_total = scan_account(assumedrole, credentials, account['Id'], session)
    ec2_total += ec2_account_total
    rds_total += rds_account_total
    natgw_total += natgw_account_total
    redshift_total += redshift_account_total
    elb_total += elb_account_total

overall_total = ec2_total + rds_total + redshift_total + natgw_total + elb_total

if not args.nocsv:
    print('', file=f)
    print('TOTAL, EC2, %d' % ec2_total, file=f)
    print('TOTAL, RDS, %d' % rds_total, file=f)
    print('TOTAL, Redshift, %d' % redshift_total, file=f)
    print('TOTAL, NATGW, %d' % natgw_total, file=f)
    print('TOTAL, ELB, %d' % elb_total, file=f)
    print('OVERALL, TOTAL, %d' % (overall_total), file=f)
print()
print('%-*s\t%-*s\t%s' % (16, 'TOTAL', 10, 'EC2', ec2_total))
print('%-*s\t%-*s\t%s' % (16, 'TOTAL', 10, 'RDS', rds_total))
print('%-*s\t%-*s\t%s' % (16, 'TOTAL', 10, 'NATGW', natgw_total))
print('%-*s\t%-*s\t%s' % (16, 'TOTAL', 10, 'Redshift', redshift_total))
print('%-*s\t%-*s\t%s' % (16, 'TOTAL', 10, 'ELB', elb_total))
print('%-*s\t%-*s\t%s' % (16, 'OVERALL', 10, 'TOTAL', overall_total))

if not args.nocsv:
    f.close()

endtime = datetime.datetime.now()
print('End time: %s' % endtime)
print('Total runtime: %s' % (endtime - starttime))
