"""Script used to update the list of mocks for dev usage.
"""
import requests
from getpass import getpass
from base64 import b64encode
import os
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

username = input('Username:')
password = getpass('Password:')

cookies_auth = {'nginxauth': b64encode(f'{username}:{password}'.encode()).decode()}
api_url = 'https://siemdev-ci.engsec/sei-qradar/api'
current_dir = os.path.abspath(os.path.dirname(__file__))
mocks_dir = os.path.join(current_dir, 'src', 'app', 'mock')

mappings = [
  {
    'url': '/dashboard',
    'file': os.path.join(mocks_dir, 'dashboard.json')
  },
  {
    'url': '/dashboard/collected-and-incidents',
    'file': os.path.join(mocks_dir, 'dashboard-event.json')
  },
  {
    'url': '/rule',
    'file': os.path.join(mocks_dir, 'rules.json')
  },
  {
    'url': '/logsource',
    'file': os.path.join(mocks_dir, 'logsource.json')
  },
  {
    'url': '/logsource/overview',
    'file': os.path.join(mocks_dir, 'logsource-overview.json')
  },
  {
    'url': '/variable',
    'file': os.path.join(mocks_dir, 'variable.json')
  },
  {
    'url': '/investigate/origin_usr',
    'file': os.path.join(mocks_dir, 'investigate-search-user.json')
  },
  {
    'url': '/investigate/risk_category',
    'file': os.path.join(mocks_dir, 'investigate-search-threats.json')
  },
  {
    'url': '/investigate/ruleid',
    'file': os.path.join(mocks_dir, 'investigate-search-ruleid.json')
  },
  {
    'url': '/investigate/origin_net',
    'file': os.path.join(mocks_dir, 'investigate-search-network.json')
  },
  {
    'url': '/investigate/origin',
    'file': os.path.join(mocks_dir, 'investigate-search-ip.json')
  },
  {
    'url': '/investigate/origin_asset',
    'file': os.path.join(mocks_dir, 'investigate-search-asset.json')
  },
  {
    'url': '/investigate/domain_name',
    'file': os.path.join(mocks_dir, 'investigate-search-domain.json')
  },
    {
    'url': '/investigate/risk-scoring',
    'file': os.path.join(mocks_dir, 'investigate-search-risk.json')
  },
  {
    'url': '/investigate/logsource',
    'file': os.path.join(mocks_dir, 'investigate-search-logsource.json')
  },
  {
    'url': '/events/search',
    'file': os.path.join(mocks_dir, 'event-search-email.json')
  },
  {
    'url': '/customer',
    'file': os.path.join(mocks_dir, 'customer.json')
  },
  {
    'url': '/qradar-check',
    'file': os.path.join(mocks_dir, 'qradar-check.json')
  },
  {
    'url': '/elastic-check',
    'file': os.path.join(mocks_dir, 'elastic-check.json')
  },
  {
    'url': '/urls',
    'file': os.path.join(mocks_dir, 'urls.json')
  },
    {
    'url': '/networks',
    'file': os.path.join(mocks_dir, 'networks.json')
  },
  {
    'url': '/domains',
    'file': os.path.join(mocks_dir, 'domains.json')
  },
  {
    'url': '/networks/rules',
    'file': os.path.join(mocks_dir, 'networks-mapping.json')
  },
  {
      'url': '/custom-property',
    'file': os.path.join(mocks_dir, 'custom-properties.json')
  }
]


for mapping in mappings:
  print(f'Requesting {mapping["url"]} and dumping to {mapping["file"]} ...')
  response = requests.get(f'{api_url}{mapping["url"]}', cookies=cookies_auth, verify=False)
  if response.status_code == 200:
    json.dump(response.json(), open(mapping['file'], 'w'), indent=4)
  else:
    print(f'Request: {response.request.url}')
    print(f'Status: {response.status_code}')
    print(response.text)
