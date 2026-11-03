# GitHub Secrets Setup Guide

This guide explains how to configure the required secrets for the Fabric deployment workflows.

## Required Secrets

Go to: **Settings > Secrets and variables > Actions** in your GitHub repository
(https://github.com/marirainier/financial-platform/settings/secrets/actions)

### 1. GIT_PAT (GitHub Personal Access Token) ⚠️ **REQUIRED**

**Create a Classic PAT:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: `Fabric Git Integration`
4. Expiration: Choose appropriate (90 days, 1 year, or no expiration)
5. **Required Scopes:**
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
   - ✅ `admin:repo_hook` (Read/write repository hooks)
   - ✅ `read:org` (Read org and team membership - optional but recommended)
6. Click "Generate token"
7. **Copy the token immediately** (you won't see it again!)
8. Add to GitHub Secrets:
   - Name: `GIT_PAT`
   - Value: Paste the token (e.g., `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

### 2. AZURE_CLIENT_ID
- Value: The App Registration (Client) ID from Azure AD
- Get from: Azure Portal > App Registrations > Your App > Overview > Application (client) ID

### 3. AZURE_TENANT_ID
- Value: Your Azure AD Tenant ID
- Get from: Azure Portal > Azure Active Directory > Overview > Tenant ID

### 4. AZURE_SUBSCRIPTION_ID (Optional but recommended)
- Value: Your Azure Subscription ID
- Get from: Azure Portal > Subscriptions > Your Subscription > Subscription ID

## How Authentication Works Now

The workflow uses **Azure Identity's `DefaultAzureCredential`** which automatically:

1. **In GitHub Actions**: Picks up the OIDC token from `azure/login` action (using `AZURE_CLIENT_ID` and `AZURE_TENANT_ID`)
2. **Locally with Azure CLI**: Uses `az login` credentials
3. **In Azure (VM/App Service)**: Uses Managed Identity
4. **With Service Principal**: Uses `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` env vars

**No more `FABRIC_TOKEN` secret needed!** The Python script acquires the token automatically.

## Azure AD App Registration Setup

Run the setup script to create the federated credential:

```bash
chmod +x infrastructure/setup_federated_auth.sh
./infrastructure/setup_federated_auth.sh
```

This creates:
- Azure AD App Registration
- Service Principal
- Federated Credential for GitHub Actions (main branch)

Then add the three output values as GitHub secrets:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID` 
- `AZURE_SUBSCRIPTION_ID`

**Important:** Assign the App Registration as **Admin** or **Member** in your Microsoft Fabric Workspace access settings!

## Verification Steps

After adding secrets, verify they work:

1. **Check GIT_PAT locally:**
   ```bash
   # Test the PAT has correct scopes
   curl -H "Authorization: token YOUR_GIT_PAT" https://api.github.com/user
   ```

2. **Test Azure auth locally:**
   ```bash
   az login
   az account set --subscription <your-subscription-id>
   python -c "from azure.identity import DefaultAzureCredential; print(DefaultAzureCredential().get_token('https://analysis.windows.net/powerbi/api/.default').token[:20] + '...')"
   ```

3. **Trigger workflow manually:**
   - Go to Actions tab
   - Select "Deploy Fabric Workspace" workflow
   - Click "Run workflow" > "Run workflow"

4. **Check workflow logs:**
   - Look for "GIT_PAT is empty or not set!" error (means secret not configured)
   - Look for "ERROR connecting to Git: 400" (means PAT invalid or wrong scopes)
   - Look for "Successfully acquired Fabric token" (auth working)

## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `GIT_PAT is empty or not set!` | Secret not added to repo | Add GIT_PAT secret |
| `ERROR connecting to Git: 401` | PAT invalid/expired | Regenerate PAT |
| `ERROR connecting to Git: 403` | Insufficient scopes | Add `repo`, `workflow`, `admin:repo_hook` scopes |
| `ERROR connecting to Git: 400` | Bad payload/repo format | Check repo name format (owner/repo) |
| `Failed to acquire Fabric token` | Azure auth failed | Check AZURE_CLIENT_ID, AZURE_TENANT_ID, run `az login` locally |
| `azure-identity not installed` | Missing dependency | Run `pip install azure-identity` |

## Token Security

- **Never commit PATs to the repository**
- **Use fine-grained PATs if possible** (but classic PATs work for this use case)
- **Rotate tokens periodically** (every 90 days recommended)
- **Remove unused tokens** from GitHub settings

## Testing Locally

You can test the orchestrator locally (no FABRIC_TOKEN needed if logged in with Azure CLI):

```bash
# Set GIT_PAT only (FABRIC_TOKEN optional - auto-acquired via Azure Identity)
export GIT_PAT="your-github-pat"

# Run orchestrator
python infrastructure/fabric_orchestrator.py \
  --workspace-name "FinancialRevenuePlatform" \
  --git-provider GitHub \
  --git-repo "marirainier/financial-platform" \
  --git-branch "main" \
  --git-directory "fabric" \
  --git-pat "$GIT_PAT"

# Or with explicit token (for testing)
python infrastructure/fabric_orchestrator.py \
  --workspace-name "FinancialRevenuePlatform" \
  --git-provider GitHub \
  --git-repo "marirainier/financial-platform" \
  --git-branch "main" \
  --git-directory "fabric" \
  --git-pat "$GIT_PAT" \
  --fabric-token "your-manual-token"
```

## Workflow Files Reference

The following workflows use these secrets:
- `.github/workflows/deploy.yml` - Main deployment workflow
- `.github/workflows/ci.yml` - CI pipeline with optional deploy

Both reference: `${{ secrets.GIT_PAT }}`, `${{ secrets.AZURE_CLIENT_ID }}`, `${{ secrets.AZURE_TENANT_ID }}`

**No more `FABRIC_TOKEN` secret or `az CLI` token fetching step needed!**