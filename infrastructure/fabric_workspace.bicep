resource workspace 'Microsoft.Fabric/workspaces@2023-11-01' = {
  name: 'fabric-financial-'
  location: resourceGroup().location
  properties: {
    displayName: 'Financial Revenue Projections ()'
  }
}
