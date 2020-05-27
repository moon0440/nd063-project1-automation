#!/usr/bin/env python
from PyInquirer import prompt

import screenshot
from questions import aws_region_setup, style
from pprint import pprint
import boto3
import ipaddress
import sys
import re
import requests

def check_aws_creds():
    c = boto3.client('sts')
    response = c.get_caller_identity()
    failure_string = f"AWS sts.get_caller_identity call failed 200 http code check \nRESPONSE RECEIVED:\n\t{response}"
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200, failure_string
    return


def build_config(answers):
    vpc_nets = list(ipaddress.IPv4Network('10.0.0.0/24').subnets(prefixlen_diff=1))
    return {
        'pri': {
            'region': answers['primary_region'],
            'vpc_name': "Primary",
            'vpc_cidr': vpc_nets[0].exploded,
            'public_subnet1_cidr': list(vpc_nets[0].subnets(prefixlen_diff=2))[0].exploded,
            'public_subnet2_cidr': list(vpc_nets[0].subnets(prefixlen_diff=2))[1].exploded,
            'private_subnet1_cidr': list(vpc_nets[0].subnets(prefixlen_diff=2))[2].exploded,
            'private_subnet2_cidr': list(vpc_nets[0].subnets(prefixlen_diff=2))[3].exploded,
        },
        'sec': {
            'region': answers['secondary_region'],
            'vpc_name': "Secondary",
            'vpc_cidr': vpc_nets[1].exploded,
            'public_subnet1_cidr': list(vpc_nets[1].subnets(prefixlen_diff=2))[0].exploded,
            'public_subnet2_cidr': list(vpc_nets[1].subnets(prefixlen_diff=2))[1].exploded,
            'private_subnet1_cidr': list(vpc_nets[1].subnets(prefixlen_diff=2))[2].exploded,
            'private_subnet2_cidr': list(vpc_nets[1].subnets(prefixlen_diff=2))[3].exploded,
        }
    }


def title_to_snake(s):
    l = re.findall('[A-Z][^A-Z]{2,}', s) + re.findall('[A-Z]{2,}', s)
    return "_".join([i.lower() for i in l])


def snake_to_title(s):
    # Hack for acronyms.
    s = s.replace("cidr", "CIDR")
    return ''.join([i.title() if i.islower() else i for i in s.split("_")])

def stack_outputs_to_dict(outputs):
    # Outputs from Cloudforamtion describe_stacks response @ response['Stacks'][0]['Outputs']
    return {title_to_snake(o['OutputKey']):o['OutputValue'] for o in outputs}


def vpc_template_params_builder(region_config):
    return [{'ParameterKey': snake_to_title(k), 'ParameterValue': v} for k, v in region_config.items()]

def get_template_body():
    template_url = "https://raw.githubusercontent.com/udacity/nd063-c2-design-for-availability-resilience-reliability-replacement-project-starter-template/master/cloudformation/vpc.yaml"
    r = requests.get(template_url)
    failure_string = f"Unable to get template body from {template_url}"
    assert r.status_code == 200, failure_string
    return r.text

def create_vpc_from_template(region_config):
    region = region_config.pop('region')
    stack_name = f"{region_config['vpc_name'].title()}RegionVpcStack"
    c = boto3.client('cloudformation', region_name=region)
    c.create_stack(
        StackName=stack_name,
        TemplateBody=get_template_body(),
        Parameters=vpc_template_params_builder(region_config),
        OnFailure='DELETE'
    )
    print(f"Waiting for {stack_name} to be created")
    waiter = c.get_waiter('stack_create_complete')
    waiter.wait(StackName=stack_name)
    print(f"Getting {stack_name} outputs")
    response = c.describe_stacks(
        StackName=stack_name,
    )
    # TODO add assertion for stack name exact match
    outputs = stack_outputs_to_dict(response['Stacks'][0]['Outputs'])
    print(f"Creating Screenshot of vpc creation")
    screenshot.create_vpc_screenshot(vpc_id=outputs['vpc'], region=region, file_name=f"{region_config['vpc_name'].lower()}_Vpc.png")
    print("done")


def main():
    check_aws_creds()
    # Add question to use these or add other
    # if not account is step offer to setup

    answers = prompt(aws_region_setup, style=style)
    if not answers['continue']:
        sys.exit('Stopping... no changes have been made')

    config = build_config(answers)

    create_vpc_from_template(config['pri'])
    create_vpc_from_template(config['sec'])

if __name__ == "__main__":
    main()
