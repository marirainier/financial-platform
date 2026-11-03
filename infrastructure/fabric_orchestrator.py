import requests
import argparse
import os
import subprocess
import time
import sys

try:
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential
    AZURE_IDENTITY_AVAILABLE = True
except ImportError:
    AZURE_IDENTITY_AVAILABLE = False
    print("WARNING: azure-identity not installed. Run: pip install azure-identity")

# Fabric API scope
FABRIC_SCOPE = "https://analysis.windows.net/powerbi/api/.default"

# Trial Capacity ID (FTL64)
TRIAL_CAPACITY_ID = "a9e1b8fe-399f-4c91-8f3c-92ff18f4b73f"

# Pre-configured GitHub Source Control connection (owned by SPN)
SPN_GITHUB_CONNECTION_ID = "281f1021-cfd3-4f20-a4b4-296bdf3a619c"

def get_fabric_token():
    """
    Get Fabric bearer token using Azure Identity.
    Works with:
    - GitHub Actions OIDC (via AZURE_CLIENT_ID, AZURE_TENANT_ID)
    - Azure CLI (az login)
    - Managed Identity (in Azure)
    - Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
    """
    if not AZURE_IDENTITY_AVAILABLE:
        raise RuntimeError("azure-identity package not installed. Run: pip install azure-identity")

    credential = DefaultAzureCredential()

    try:
        token_obj = credential.get_token(FABRIC_SCOPE)
        return token_obj.token
    except Exception as e:
        print(f"ERROR: Failed to acquire Fabric token: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure azure-identity is installed: pip install azure-identity")
        print("  2. For GitHub Actions: Check AZURE_CLIENT_ID and AZURE_TENANT_ID secrets")
        print("  3. For local dev: Run 'az login' and 'az account set --subscription <sub-id>'")
        print("  4. Verify the service principal has Fabric workspace permissions")
        raise

def fabric_api_call(method, endpoint, token, data=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f'https://api.fabric.microsoft.com/v1/{endpoint}'
    response = requests.request(method, url, headers=headers, json=data)

    if not response.ok:
        print(f"API Error ({response.status_code}) on {method} {url}: {response.text}")
        if response.status_code == 401:
            print("ERROR: Authentication failed. Token may be expired or invalid.")
        elif response.status_code == 403:
            print("ERROR: Forbidden. Check workspace/gateway permissions for the service principal.")
        elif response.status_code == 400:
            print("ERROR: Bad request. Check payload format and required fields.")
        elif response.status_code == 409:
            print("ERROR: Conflict. Resource may already exist.")
    response.raise_for_status()

    if response.status_code == 202:
        print("Operation Accepted (202). Polling...")
        time.sleep(10)
    return response.json() if response.text else {}

def validate_git_pat(pat: str) -> bool:
    """Validate that the PAT is not empty and has reasonable format."""
    if not pat or not pat.strip():
        print("ERROR: GIT_PAT is empty or not set!")
        print("Please add GIT_PAT secret to GitHub repository settings:")
        print("  Settings > Secrets and variables > Actions > New repository secret")
        print("  Name: GIT_PAT")
        print("  Value: Your GitHub Personal Access Token (classic)")
        print("  Required scopes: repo, workflow, admin:repo_hook")
        return False
    if len(pat.strip()) < 20:
        print(f"WARNING: GIT_PAT appears too short ({len(pat.strip())} chars).")
        print("GitHub classic PATs are typically 40 characters.")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace-name', default='FinancialRevenuePlatform')
    parser.add_argument('--workspace-id', help='Optional: Workspace ID (overrides workspace-name lookup)')
    parser.add_argument('--git-provider', choices=['GitHub', 'AzureDevOps'], default='GitHub')
    parser.add_argument('--git-repo', help='GitHub: owner/repo, ADO: org/project/repo')
    parser.add_argument('--git-branch', default='main')
    parser.add_argument('--git-directory', default='/fabric')
    parser.add_argument('--git-pat', required=True)
    parser.add_argument('--fabric-token', help='Optional: Fabric bearer token (overrides auto-auth)')
    parser.add_argument('--skip-git-connection', action='store_true', help='Skip Git connection creation (for testing)')
    args = parser.parse_args()

    if not validate_git_pat(args.git_pat):
        sys.exit(1)

    if args.fabric_token:
        token = args.fabric_token
        print("Using provided FABRIC_TOKEN")
    else:
        print("Acquiring Fabric token via Azure Identity...")
        try:
            token = get_fabric_token()
            print("Successfully acquired Fabric token")
        except Exception as e:
            sys.exit(1)

    # 1. Resolve/Create Workspace
    if args.workspace_id:
        ws_id = args.workspace_id
        print(f"Using workspace ID directly: {ws_id}")
        workspaces = fabric_api_call('GET', 'workspaces', token)
        ws = next((w for w in workspaces.get('value', []) if w.get('id') == ws_id), None)
        if not ws:
            print(f"ERROR: Workspace ID {ws_id} not found in tenant")
            sys.exit(1)
    else:
        workspaces = fabric_api_call('GET', 'workspaces', token)
        ws = next((w for w in workspaces.get('value', []) if w.get('displayName') == args.workspace_name), None)
        if not ws:
            print(f"Workspace '{args.workspace_name}' not found, creating...")
            try:
                ws = fabric_api_call('POST', 'workspaces', token, {'displayName': args.workspace_name})
                print(f"Created workspace: {args.workspace_name}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 409:
                    print("Workspace name conflict, searching...")
                    workspaces = fabric_api_call('GET', 'workspaces', token)
                    ws = next((w for w in workspaces.get('value', [])
                              if w.get('displayName', '').lower() == args.workspace_name.lower()), None)
                    if not ws:
                        print("ERROR: Workspace not found after 409 conflict")
                        sys.exit(1)
                else:
                    raise
        ws_id = ws['id']
        print(f"Using workspace: {args.workspace_name} (ID: {ws_id})")

    # 2. Assign to Trial Capacity
    print(f"Assigning workspace to Trial Capacity ({TRIAL_CAPACITY_ID})...")
    try:
        fabric_api_call('POST', f'workspaces/{ws_id}/assignToCapacity', token, {
            'capacityId': TRIAL_CAPACITY_ID
        })
        print("Workspace assigned to Trial capacity.")
    except requests.exceptions.HTTPError as e:
        print(f"WARNING: Capacity assignment might have failed: {e.response.text}")

    # 3. Git Integration
    try:
        status = fabric_api_call('GET', f'workspaces/{ws_id}/git/status', token)
        print("Workspace is already connected to Git.")
        git_connected = True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in (404, 400):
            print("Workspace not connected to Git. Connecting...")
            git_connected = False
        else:
            raise

    if not git_connected and not args.skip_git_connection:
        print("Setting up Git integration...")

        repo_parts = args.git_repo.split('/')
        if len(repo_parts) < 2:
            print(f"ERROR: Invalid git-repo format. Expected 'owner/repo', got '{args.git_repo}'")
            sys.exit(1)

        if args.git_provider == 'GitHub':
            # Use the pre-configured SPN-owned GitHub connection
            github_connection_id = SPN_GITHUB_CONNECTION_ID
            print(f"Using SPN GitHub connection: {github_connection_id}")

            git_config = {
                'gitProviderDetails': {
                    'gitProviderType': 'GitHub',
                    'branchName': args.git_branch,
                    'directoryName': args.git_directory,
                    'repositoryName': repo_parts[-1],
                    'ownerName': repo_parts[0]
                },
                'myGitCredentials': {
                    'source': 2,  # Service Connection
                    'connectionId': github_connection_id
                }
            }
        else:
            # AzureDevOps - can use Automatic with OIDC
            git_config = {
                'gitProviderDetails': {
                    'gitProviderType': 'AzureDevOps',
                    'branchName': args.git_branch,
                    'directoryName': args.git_directory,
                    'repositoryName': repo_parts[-1],
                    'organizationName': repo_parts[0],
                    'projectName': repo_parts[1]
                },
                'myGitCredentials': {
                    'source': 1  # Automatic (OIDC)
                }
            }

        try:
            fabric_api_call('POST', f'workspaces/{ws_id}/git/connect', token, git_config)
            print("Git connection established.")
        except requests.exceptions.HTTPError as e:
            print(f"ERROR connecting to Git: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            sys.exit(1)

        # Initialize
        try:
            fabric_api_call('POST', f'workspaces/{ws_id}/git/initializeConnection', token,
                          {'initializationStrategy': 'PreferRemote'})
            print("Git initialized.")
        except requests.exceptions.HTTPError as e:
            print(f"ERROR initializing connection: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            sys.exit(1)

    # 4. Sync from Git
    if not args.skip_git_connection:
        try:
            commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
            print(f"Syncing to commit: {commit_hash}")

            # First sync needs different conflict resolution for empty workspace
            # Check if workspace has any items first
            try:
                items = fabric_api_call('GET', f'workspaces/{ws_id}/items', token)
                has_items = len(items.get('value', [])) > 0
            except:
                has_items = False

            sync_payload = {
                'mode': 'All',
                'remoteCommitHash': commit_hash,
                'conflictResolution': {
                    'conflictResolutionType': 'Workspace',
                    'conflictResolutionPolicy': 'PreferRemote'
                },
                'options': {'allowOverrideItems': True}
            }

            # For first sync on empty workspace, use different approach
            if not has_items:
                print("First sync on empty workspace - using force sync...")
                sync_payload['options']['allowOverrideItems'] = True

            fabric_api_call('POST', f'workspaces/{ws_id}/git/updateFromGit', token, sync_payload)
            print("Sync Complete.")
        except subprocess.CalledProcessError:
            print("ERROR: Failed to get git commit hash.")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            print(f"ERROR during sync: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            sys.exit(1)

    print("\n✅ Fabric workspace provisioning complete!")
    print(f"   Workspace: {args.workspace_name} ({ws_id})")
    print(f"   Capacity: Trial (FTL64)")
    if not args.skip_git_connection:
        print(f"   Git: Connected to {args.git_repo}")

if __name__ == '__main__':
    main()