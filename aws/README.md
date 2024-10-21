# Prisma Cloud AWS License Sizing Script

## Overview

This document describes how to prepare for, and how to run the Prisma Cloud AWS License Sizing Python Script.

## Prerequisites

### Required Permissions

The AWS account that is used to run the sizing script must have the required permissions to be able to collect sizing information.

### Required AWS APIs

The below AWS APIs need to be enabled in order to gather information from AWS.

* aws organizations describe-organization (optional, when scanning an Org)
* aws organizations list-accounts (optional, when scanning an Org)
* aws sts assume-role (optional, when scanning an Org)
* aws ec2 describe-instances

## AWS Organization Support

The script can collect sizing information for AWS accounts attached to an AWS Organization. It does this by leveraging the AWS `OrganizationAccountAccessRole`

https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_access.html

Flow and logic for AWS Organizations:

1. Queries for member accounts using the Organizations API
1. Loops through each member account
1. Authenticates into each member account via STS Assume Role into the `OrganizationAccountAccessRole` with the minimum session duration possible (900 seconds)
1. Counts resources

The `OrganizationAccountAccessRole` is automatically created in an account if the account was provisioned via the organization.
If the account was not originally provisioned in that manner, the role may not exist and assuming the role may fail.
Administrators can create the role manually by following this documentation:

https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_access.html

## Running the Script from AWS Cloud Shell

1. Start a Cloud Shell session from the AWS UI, which should have the AWS CLI tool, your credentials, ```git``` and ``python3`` already prepared
2. Clone this repository
3. ```cd pcs-sizing-scripts/aws```
4. ```pip3 install boto```
5. ```python3 resource-count-aws-instances.py --awsorg```
6. Output is sent to the console and saved in ```sizing.csv```
