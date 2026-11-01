import requests
import argparse
import os

def fabric_api_call(method, endpoint, token, data=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f'https://api.fabric.microsoft.com/v1/{endpoint}'
    response = requests.request(method, url, headers=headers, json=data)
    if not response.ok:
        print(f"API Error ({response.status_code}) on {method} {url}: {response.text}")
    response.raise_for_status()
    return response.json() if response.text else {}

def get_trial_capacity_id(token):
    """Get the first available Fabric Trial capacity ID."""
    try:
        capacities = fabric_api_call('GET', 'capacities', token)
        for cap in capacities.get('value', []):
            if cap.get('sku', '').startswith('Trial') or cap.get('sku', '').startswith('F'):
                return cap['id']
    except Exception as e:
        print(f'Warning: Could not fetch capacities: {e}')
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capacity-id', help='Fabric capacity ID (optional, will try to find Trial capacity)')
    parser.add_argument('--workspace-name', default='FinancialRevenuePlatform')
    parser.add_argument('--git-provider', choices=['GitHub', 'AzureDevOps'], default='GitHub', help='Git provider for Fabric Git integration')
    parser.add_argument('--git-repo', help='Git repository name (e.g., org/repo)')
    parser.add_argument('--git-branch', default='main', help='Git branch')
    parser.add_argument('--git-directory', default='fabric', help='Directory in repo for Fabric items')
    parser.add_argument('--skip-git', action='store_true', help='Skip Git integration setup')
    args = parser.parse_args()

    token = os.environ.get('FABRIC_TOKEN')
    if not token:
        raise ValueError('FABRIC_TOKEN environment variable not set')

    workspace_name = args.workspace_name
    capacity_id = args.capacity_id

    # If no capacity specified, try to find a Trial capacity
    if not capacity_id:
        print('No capacity specified, searching for Fabric Trial capacity...')
        capacity_id = get_trial_capacity_id(token)
        if capacity_id:
            print(f'Found Trial capacity: {capacity_id}')
        else:
            print('No Trial capacity found. Workspace will be created without capacity (use --capacity-id to specify).')

    # 1. Check if workspace already exists, otherwise create it
    print(f"Checking existing workspaces for '{workspace_name}'...")
    try:
        workspaces_response = fabric_api_call('GET', 'workspaces', token)
        existing_ws = next((w for w in workspaces_response.get('value', []) if w.get('displayName') == workspace_name), None)

        if existing_ws:
            ws_id = existing_ws['id']
            print(f"Found existing workspace: {ws_id}")
        else:
            workspace_data = {'displayName': workspace_name}
            if capacity_id:
                workspace_data['capacityId'] = capacity_id

            ws = fabric_api_call('POST', 'workspaces', token, workspace_data)
            ws_id = ws['id']
            print(f'Workspace Created: {ws_id}')
    except Exception as create_err:
        print(f"Error handling workspace creation/lookup: {create_err}")
        raise create_err

    # 2. Git Connect (if not skipped)
    if not args.skip_git:
        if not args.git_repo:
            print('Warning: --git-repo not provided. Skipping Git integration.')
            print('Provide --git-repo org/repo to enable GitHub integration, or use --skip-git')
        else:
            # Format gitProviderDetails payload according to Fabric v1 API requirements
            repo_parts = args.git_repo.split('/')
            owner = repo_parts[0] if len(repo_parts) == 2 else ''
            name = repo_parts[1] if len(repo_parts) == 2 else args.git_repo

            # Format directory path: must start with slash or be empty/root
            directory = args.git_directory.strip('/')
            directory_path = f"/{directory}" if directory else "/"

            git_config = {
                'gitProviderDetails': {
                    'gitProvider': args.git_provider,
                    'ownerName': owner,
                    'organizationName': owner,
                    'repositoryName': name,
                    'branchName': args.git_branch,
                    'directoryName': directory_path
                },
                'serviceType': 'GitHub'
            }
            try:
                # 1. Connect to Git
                print(f"Connecting workspace {ws_id} to Git ({args.git_provider}: {owner}/{name}, branch: {args.git_branch}, dir: {directory_path})...")
                fabric_api_call('POST', f'workspaces/{ws_id}/git/connect', token, git_config)
                print(f'Git Connected to {args.git_provider}: {args.git_repo}')
            except Exception as e:
                # If connection fails with 400 because it is already connected, try continuing
                print(f"Git Connect response/warning: {e}")

            try:
                # 2. Sync / Update from Git (Initialize connection / sync)
                print("Initiating Git sync (initializeConnectionAndSync / updateFromGit)...")
                # Try initializeConnectionAndSync first if supported, else updateFromGit
                try:
                    fabric_api_call('POST', f'workspaces/{ws_id}/git/initializeConnectionAndSync', token, {
                        'gitAction': 'Import',
                        'remoteCommitHash': ''
                    })
                    print('Initialize Connection and Sync Complete.')
                except Exception:
                    # Fallback to updateFromGit with minimal required payload
                    fabric_api_call('POST', f'workspaces/{ws_id}/git/updateFromGit', token, {
                        'head': args.git_branch,
                        'workspaceHead': args.git_branch
                    })
                    print('Sync from Git Complete.')
            except Exception as e:
                print(f"Git Update call failed: {e}")
                print("Note: Service Principals (OIDC) require tenant-level 'Service principals can use Fabric APIs' and 'Service principals can integrate with Git' tenant settings enabled in Fabric Admin Portal.")
                raise e
    else:
        print('Git integration skipped (--skip-git).')

if __name__ == '__main__':
    main()
