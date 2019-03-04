from __future__ import print_function
import sys
import argparse
import json
import datetime
import itertools
import os.path
import math
import urllib.parse
from os import listdir
from collections import OrderedDict
from abc import ABCMeta, abstractmethod
from six import add_metaclass
import pyjq
from policyuniverse.policy import Policy
from shared.common import parse_arguments, query_aws, get_parameter_file, get_regions, get_account_stats, get_us_east_1, get_collection_date, get_access_advisor_active_counts
from shared.nodes import Account, Region
from shared.public import get_public_nodes


from jinja2 import Template

__description__ = "Create report"

DASHBOARD_OUTPUT_FILE = os.path.join('web', 'account-data', 'report.html')

COLOR_PALETTE = [
        'rgba(141,211,199,1)', 'rgba(255,255,179,1)', 'rgba(190,186,218,1)', 'rgba(251,128,114,1)', 'rgba(128,177,211,1)', 'rgba(253,180,98,1)', 'rgba(179,222,105,1)', 'rgba(252,205,229,1)', 'rgba(217,217,217,1)', 'rgba(188,128,189,1)', 'rgba(204,235,197,1)', 'rgba(255,237,111,1)']

ACTIVE_COLOR = 'rgb(139, 214, 140)'
BAD_COLOR = 'rgb(204, 120, 120)'
INACTIVE_COLOR = 'rgb(244, 178, 178)'


def dashboard(accounts, config, args):
    '''Create dashboard'''

    # Create directory for output file if it doesn't already exists
    try:
        os.mkdir(os.path.dirname(DASHBOARD_OUTPUT_FILE))
    except OSError:
        # Already exists
        pass

    # Create output file
    with open(os.path.join('templates', 'report.html'),'r') as dashboard_template:
        template = Template(dashboard_template.read())
    
    # Data to be passed to the template
    t = {}

    # Get account names and id's
    t['accounts'] = []
    for account in accounts:
        t['accounts'].append({
            'name':account['name'], 
            'id': account['id'], 
            'collection_date': get_collection_date(account)})
    
    # Get resource count info
    # Collect counts
    account_stats = {}
    print('* Getting resource counts')
    for account in accounts:
        account_stats[account['name']] = get_account_stats(account)
        print('  - {}'.format(account['name']))
    
    # Get names of resources
    # TODO: Change the structure passed through here to be a dict of dict's like I do for the regions
    t['resource_names'] = ['']
    # Just look at the resource names of the first account as they are all the same
    first_account = list(account_stats.keys())[0]
    for name in account_stats[first_account]['keys']:
        t['resource_names'].append(name)
    
    # Create jinja data for the resource stats per account
    t['resource_stats'] = []
    for account in accounts:
        for resource_name in t['resource_names']:
            if resource_name == '':
                resource_row = [account['name']]
            else:
                count = sum(account_stats[account['name']][resource_name].values())
                resource_row.append(count)
        
        t['resource_stats'].append(resource_row)
    
    t['resource_names'].pop(0)

    # Get region names
    t['region_names'] = []
    account = accounts[0]
    account = Account(None, account)
    for region in get_regions(account):
        region = Region(account, region)
        t['region_names'].append(region.name)

    # Get stats for the regions
    region_stats = {}
    region_stats_tooltip = {}
    for account in accounts:
        account = Account(None, account)
        region_stats[account.name] = {}
        region_stats_tooltip[account.name] = {}
        for region in get_regions(account):
            region = Region(account, region)
            count = 0
            for resource_name in t['resource_names']:
                n = account_stats[account.name][resource_name].get(region.name, 0)
                count += n

                if n > 0:
                    if region.name not in region_stats_tooltip[account.name]:
                        region_stats_tooltip[account.name][region.name] = ''    
                    region_stats_tooltip[account.name][region.name] += '{}:{}<br>'.format(resource_name, n)

            if count > 0:
                has_resources = 'Y'
            else:
                has_resources = 'N'
            region_stats[account.name][region.name] = has_resources
        
    t['region_stats'] = region_stats
    t['region_stats_tooltip'] = region_stats_tooltip

    # Pass the account names
    t['account_names'] = []
    for a in accounts:
        t['account_names'].append(a['name'])

    t['resource_data_set'] = []

    # Pass data for the resource chart
    color_index = 0
    for resource_name in t['resource_names']:
        resource_counts = []
        for account_name in t['account_names']:
            resource_counts.append(sum(account_stats[account_name][resource_name].values()))
        
        resource_data = {
            'label': resource_name,
            'data': resource_counts,
            'backgroundColor': COLOR_PALETTE[color_index],
            'borderWidth': 1
        }
        t['resource_data_set'].append(resource_data)

        color_index = (color_index + 1) % len(COLOR_PALETTE)
    

    # Get IAM access dat
    print('* Getting IAM data')
    t['iam_active_data_set'] = [
        {
            'label': 'Active users',
            'stack': 'users',
            'data': [],
            'backgroundColor': 'rgb(162, 203, 249)',
            'borderWidth': 1
        },
        {
            'label': 'Inactive users',
            'stack': 'users',
            'data': [],
            'backgroundColor': INACTIVE_COLOR,
            'borderWidth': 1
        },
        {
            'label': 'Active roles',
            'stack': 'roles',
            'data': [],
            'backgroundColor': ACTIVE_COLOR,
            'borderWidth': 1
        },
        {
            'label': 'Inactive roles',
            'stack': 'roles',
            'data': [],
            'backgroundColor': INACTIVE_COLOR,
            'borderWidth': 1
        }
    ]

    for account in accounts:
        account = Account(None, account)
        print('  - {}'.format(account.name))

        account_stats = get_access_advisor_active_counts(account, args.max_age)

        # Add to dataset
        t['iam_active_data_set'][0]['data'].append(account_stats['users']['active'])
        t['iam_active_data_set'][1]['data'].append(account_stats['users']['inactive'])
        t['iam_active_data_set'][2]['data'].append(account_stats['roles']['active'])
        t['iam_active_data_set'][3]['data'].append(account_stats['roles']['inactive'])

    print('* Getting public resource data')
    # TODO Need to cache this data as this can take a long time
    t['public_network_resource_type_names'] = ['ec2', 'elb', 'rds', 'autoscaling', 'cloudfront', 'apigateway']
    t['public_network_resource_types'] = {}

    t['public_ports'] = []
    t['account_public_ports'] = {}

    for account in accounts:
        print('  - {}'.format(account['name']))

        t['public_network_resource_types'][account['name']] = {}
        t['account_public_ports'][account['name']] = {}

        for type_name in t['public_network_resource_type_names']:
            t['public_network_resource_types'][account['name']][type_name] = 0

        public_nodes, _ = get_public_nodes(account, config, use_cache=True)

        for public_node in public_nodes:
            if public_node['type'] in t['public_network_resource_type_names']:
                t['public_network_resource_types'][account['name']][public_node['type']] += 1
            else:
                raise Exception('Unknown type {} of public node'.format(public_node['type']))
            
            if public_node['ports'] not in t['public_ports']:
                t['public_ports'].append(public_node['ports'])
            
            t['account_public_ports'][account['name']][public_node['ports']] = t['account_public_ports'][account['name']].get(public_node['ports'], 0) + 1

    # Pass data for the public port chart
    t['public_ports_data_set'] = []
    color_index = 0
    for ports in t['public_ports']:
        port_counts = []
        for account_name in t['account_names']:
            port_counts.append(t['account_public_ports'][account_name].get(ports, 0))

        # Fix the port range name for '' when ICMP is being allowed
        if ports == '':
            ports = 'ICMP only'

        port_data = {
            'label': ports,
            'data': port_counts,
            'backgroundColor': COLOR_PALETTE[color_index],
            'borderWidth': 1
        }
        t['public_ports_data_set'].append(port_data)

        color_index = (color_index + 1) % len(COLOR_PALETTE)

    # Generate report from template
    with open(DASHBOARD_OUTPUT_FILE,'w') as f:
        f.write(template.render(t=t))

def run(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-age",
        help="Number of days a user or role hasn't been used before it's marked dead",
        default=90,
        type=int)
    args, accounts, config = parse_arguments(arguments, parser)

    dashboard(accounts, config, args)
