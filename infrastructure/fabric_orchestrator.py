import requests
import json
import argparse
import os

def fabric_api_call(method, endpoint, token, data=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f'https://api.fabric.microsoft.com/v1/{endpoint}'
    response = requests.request(method, url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def main():
    token = os.environ.get('FABRIC_TOKEN')
    workspace_name = 'FinancialRevenuePlatform'
    
    # 1. Create Workspace
    ws = fabric_api_call('POST', 'workspaces', token, {'displayName': workspace_name})
    ws_id = ws['id']
    print(f'Workspace Created: {ws_id}')
    
    # 2. Git Connect (Example - requires repo info)
    git_config = {
        'gitProvider': 'GitHub',
        'repository': 'financial-platform',
        'branch': 'main',
        'directory': 'fabric'
    }
    fabric_api_call('POST', f'workspaces/{ws_id}/gitConnect', token, git_config)
    print('Git Connected.')
    
    # 3. Git Update
    fabric_api_call('POST', f'workspaces/{ws_id}/gitUpdate', token, {'mode': 'All'})
    print('Sync from Git Complete.')

if __name__ == '__main__':
    main()
