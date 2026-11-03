#!/bin/bash
# Local test script for fabric_orchestrator.py
# Usage: ./test_local.sh

set -e

echo "=== Fabric Orchestrator Local Test ==="
echo ""

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "ERROR: .env.local file not found!"
    echo "Create .env.local with the following variables:"
    echo "  GIT_PAT=your-github-personal-access-token"
    echo "  (FABRIC_TOKEN is now optional - will use Azure Identity)"
    exit 1
fi

# Load environment variables
export $(cat .env.local | grep -v '^#' | xargs)

# Validate required vars
if [ -z "$GIT_PAT" ]; then
    echo "ERROR: GIT_PAT not set in .env.local"
    exit 1
fi

echo "Running fabric_orchestrator.py..."
echo "Workspace: FinancialRevenuePlatform"
echo "Repo: marirainier/financial-platform"
echo "Branch: main"
echo "Directory: fabric"
echo ""

python infrastructure/fabric_orchestrator.py \
  --workspace-name "FinancialRevenuePlatform" \
  --git-provider GitHub \
  --git-repo "marirainier/financial-platform" \
  --git-branch "main" \
  --git-directory "fabric" \
  --git-pat "$GIT_PAT"

echo ""
echo "=== Test Complete ==="