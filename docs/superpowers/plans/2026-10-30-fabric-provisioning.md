# Updated Fabric Git-Integrated Methodology Plan

**Goal:** Implement a Git-Integrated Fabric platform using the Workspace-as-Code methodology.

**Approach:**
1. **Bootstrap Workspace**: Use the Fabric REST API to create a workspace shell.
2. **Git Integration**: Use the Fabric REST API to connect this workspace to your GitHub repository (using a Personal Access Token).
3. **Automated Sync**: Invoke the "Update from Git" API to pull all Fabric items defined in the `fabric/` folder into the workspace automatically.

---

### Task 1: Fabric-Native Workspace Orchestrator

**Files:**
- Create: `infrastructure/fabric_orchestrator.py`
- Modify: `infrastructure/deploy.sh`

- [ ] **Step 1: Write `infrastructure/fabric_orchestrator.py`**
Script using `requests` to:
1. `POST /workspaces` (Create Workspace).
2. `POST /workspaces/{id}/gitConnect` (Connect to Git branch).
3. `POST /workspaces/{id}/gitUpdate` (Initial sync from Git).

- [ ] **Step 2: Update `infrastructure/deploy.sh`**
Replace previous Bicep calls with a direct call to `fabric_orchestrator.py`.

- [ ] **Step 3: Commit**
```bash
git add infrastructure/fabric_orchestrator.py infrastructure/deploy.sh
git commit -m "feat: implement Fabric-native Git integration orchestrator"
```

---

### Task 2: Git-Integration-Ready Repository Structure

**Files:**
- Create: `fabric/.gitignore`
- Create: `fabric/workspace.json` (Workspace metadata definition)

- [ ] **Step 1: Add Git-Ready Metadata**
Ensure `fabric/` directory contains standard Fabric-exported format.

- [ ] **Step 2: Commit**
```bash
git add fabric/
git commit -m "chore: add Fabric workspace-as-code artifacts"
```

---

### Task 3: Final CI/CD Integration

**Files:**
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Update CI/CD Pipeline**
Update the pipeline to run `infrastructure/fabric_orchestrator.py` instead of ARM deployments.

- [ ] **Step 2: Commit**
```bash
git add .github/workflows/deploy.yml
git commit -m "feat: complete CI/CD migration to Git-integrated Fabric workflow"
```
