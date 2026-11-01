#!/bin/bash
set -e

# Configuration variables
APP_NAME="FabricGitHubFederatedCI"
REPO="marirainier/financial-platform"
BRANCH="main"

echo "1. Checking Azure login status..."
if ! az account show &>/dev/null; then
    echo "Please log in to Azure first using 'az login'"
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

echo "Using Subscription ID: $SUBSCRIPTION_ID"
echo "Using Tenant ID: $TENANT_ID"

echo "2. Creating Azure AD App Registration: $APP_NAME..."
APP_JSON=$(az ad app create --display-name "$APP_NAME" -o json)
APP_ID=$(echo "$APP_JSON" | grep -o '"appId": "[^"]*' | grep -o '[^"]*$')
OBJECT_ID=$(echo "$APP_JSON" | grep -o '"id": "[^"]*' | head -n 1 | grep -o '[^"]*$')

echo "App ID (Client ID): $APP_ID"
echo "Object ID: $OBJECT_ID"

echo "3. Creating Service Principal for the App..."
az ad sp create --id "$APP_ID" >/dev/null

echo "4. Creating Federated Credential for GitHub Actions ($REPO on branch $BRANCH)..."
cat << TRUST_EOF > /tmp/trust-config.json
{
  "name": "GitHubActionsBranchTrust",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:$REPO:ref:refs/heads/$BRANCH",
  "description": "Trust GitHub Actions tokens from main branch",
  "audiences": [
    "api://AzureADTokenExchange"
  ]
}
TRUST_EOF

az ad app federated-credential create --id "$OBJECT_ID" --parameters /tmp/trust-config.json
rm /tmp/trust-config.json

echo "=== Setup Complete! ==="
echo "Add these 3 secrets to your GitHub repository (Settings > Secrets and variables > Actions):"
echo "--------------------------------------------------------------------------------"
echo "AZURE_CLIENT_ID:      $APP_ID"
echo "AZURE_TENANT_ID:      $TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo "--------------------------------------------------------------------------------"
echo "NOTE: Remember to assign the App Registration ($APP_ID) as 'Admin' or 'Member' in your Microsoft Fabric Workspace access settings!"
