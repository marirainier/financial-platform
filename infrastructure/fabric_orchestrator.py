import requests
import argparse
import os
import subprocess
import time

def fabric_api_call(method, endpoint, token, data=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f'https://api.fabric.microsoft.com/v1/{endpoint}'
    response = requests.request(method, url, headers=headers, json=data)

    if not response.ok:
        print(f"API Error ({response.status_code}) on {method} {url}: {response.text}")
    response.raise_for_status()

    # Handle LRO (202) if needed
    if response.status_code == 202:
        print("Operation Accepted (202). Polling...")
        # Polling logic for simplicity (can be enhanced)
        time.sleep(10)
    return response.json() if response.text else {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace-name', default='FinancialRevenuePlatform')
    parser.add_argument('--git-provider', choices=['GitHub', 'AzureDevOps'], default='GitHub')
    parser.add_argument('--git-repo', help='GitHub: owner/repo, ADO: org/project/repo')
    parser.add_argument('--git-branch', default='main')
    parser.add_argument('--git-directory', default='/fabric')
    parser.add_argument('--git-pat', required=True)
    args = parser.parse_args()

    token = os.environ.get('FABRIC_TOKEN')

    # 1. Resolve Workspace
    workspaces = fabric_api_call('GET', 'workspaces', token)
    ws = next((w for w in workspaces.get('value', []) if w.get('displayName') == args.workspace_name), None)
    if not ws:
        ws = fabric_api_call('POST', 'workspaces', token, {'displayName': args.workspace_name})
    ws_id = ws['id']

    # 2. Check Git Connection
    try:
        status = fabric_api_call('GET', f'workspaces/{ws_id}/git/status', token)
        print("Workspace is already connected to Git.")
    except:
        print("Connecting to Git...")
        repo_parts = args.git_repo.split('/')
        git_config = {
            'gitProviderDetails': {
                'gitProviderType': args.git_provider,
                'branchName': args.git_branch,
                'directoryName': args.git_directory,
                'repositoryName': repo_parts[-1]
            },
            'myGitCredentials': {
                'source': 'PersonalAccessToken',
                'personalAccessToken': args.git_pat
            }
        }
        if args.git_provider == 'GitHub':
            git_config['gitProviderDetails']['ownerName'] = repo_parts[0]
        else:
            git_config['gitProviderDetails']['organizationName'] = repo_parts[0]
            git_config['gitProviderDetails']['projectName'] = repo_parts[1]

        fabric_api_call('POST', f'workspaces/{ws_id}/git/connect', token, git_config)

        # Initialize
        fabric_api_call('POST', f'workspaces/{ws_id}/git/initializeConnection', token, {'initializationStrategy': 'PreferRemote'})
        print("Connected and Initialized.")

    # 3. Sync
    commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
    print(f"Syncing to commit: {commit_hash}")
    fabric_api_call('POST', f'workspaces/{ws_id}/git/updateFromGit', token, {
        'mode': 'All',
        'remoteCommitHash': commit_hash,
        'conflictResolution': {'conflictResolutionType': 'Workspace', 'conflictResolutionPolicy': 'PreferRemote'},
        'options': {'allowOverrideItems': True}
    })
    print("Sync Complete.")

if __name__ == '__main__':
    main()
