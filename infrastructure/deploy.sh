#!/bin/bash
set -e
echo 'Provisioning Fabric Workspace via Bicep...'
az deployment group create --resource-group \ --template-file infrastructure/fabric_workspace.bicep --parameters environment=\
echo 'Workspace provisioned.'
