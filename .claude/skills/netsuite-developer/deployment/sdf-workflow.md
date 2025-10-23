# SuiteCloud Development Framework (SDF) Workflow

Complete workflow for managing NetSuite customizations with SDF.

## Prerequisites

- Node.js v22 LTS
- Oracle JDK 17 or 21
- SuiteCloud CLI installed: `npm install -g @oracle/suitecloud-cli`
- NetSuite account with SDF enabled
- Developer role assigned

## Create Project

### Step 1: Create New SuiteCloud Project

```bash
# Interactive project creation
suitecloud project:create

# Prompts:
# - Project type: Account Customization Project or SuiteApp
# - Project name: my-netsuite-project
# - Parent directory: /opt/ns
```

### Step 2: Navigate to Project

```bash
cd my-netsuite-project
```

### Project Structure Created

```
my-netsuite-project/
├── manifest.xml              # Project metadata and dependencies
├── deploy.xml                # Deployment configuration
└── src/
    ├── FileCabinet/         # File Cabinet files
    │   └── SuiteScripts/    # SuiteScript files
    └── Objects/             # SDF custom objects (XML)
```

## Setup Authentication

### Method 1: Browser-Based Auth (Local Development)

```bash
suitecloud account:setup
```

**Process:**
1. Opens browser to NetSuite login
2. Select account and role
3. Creates authID (alias for account-role combination)
4. Saves credentials locally

**Prompts:**
- Authentication ID: `dev` (or your preferred alias)
- Account ID: Your NetSuite account number
- Role: Select from available roles

### Method 2: CI/CD Auth (Automated)

```bash
suitecloud account:setup:ci
```

**Requirements:**
- Token-Based Authentication (TBA) credentials
- Environment variables or configuration file

**Environment Variables:**
```bash
export NS_ACCOUNT_ID="your_account_id"
export NS_TOKEN_ID="your_token_id"
export NS_TOKEN_SECRET="your_token_secret"
```

### Manage Authentication IDs

```bash
# List all configured authIDs
suitecloud account:manageauth

# Operations:
# - List authIDs
# - Add new authID
# - Remove authID
# - Update default authID
```

## Development Workflow

### Import Existing Customizations

#### Import Files from NetSuite

```bash
# Import files from File Cabinet
suitecloud file:import

# Interactive prompts:
# - Select authID
# - Select folders to import
# - Confirm import
```

**Result:** Files copied to `src/FileCabinet/` preserving folder structure

#### Import Custom Objects

```bash
# Import SDF objects
suitecloud object:import

# Interactive prompts:
# - Select authID
# - Select object types (scripts, records, workflows, etc.)
# - Select specific objects
# - Confirm import
```

**Result:** XML definitions created in `src/Objects/`

### Create New Files

#### Create SuiteScript File

```bash
suitecloud file:create

# Prompts:
# - Script type (User Event, Client Script, etc.)
# - File path
# - Module dependencies
```

**Generated File:**
```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType UserEventScript
 */
define(['N/record', 'N/log'],
    (record, log) => {

        function beforeSubmit(scriptContext) {
            // Your code here
        }

        return {
            beforeSubmit: beforeSubmit
        };
    }
);
```

### Edit manifest.xml

Add dependencies required by your customizations:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest projecttype="ACCOUNTCUSTOMIZATION">
    <projectname>my-netsuite-project</projectname>
    <frameworkversion>1.0</frameworkversion>
    <dependencies>
        <features>
            <feature required="true">CUSTOMRECORDS</feature>
            <feature required="true">SERVERSIDESCRIPTING</feature>
            <feature required="true">WORKFLOW</feature>
        </features>
    </dependencies>
</manifest>
```

### Edit deploy.xml

Configure deployment order:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<deploy>
    <files>
        <!-- Libraries first -->
        <path>~/FileCabinet/SuiteScripts/lib/utils.js</path>
        <!-- Then main scripts -->
        <path>~/FileCabinet/SuiteScripts/user_event_sales_order.js</path>
    </files>
    <objects>
        <!-- Custom records first -->
        <path>~/Objects/customrecord_project.xml</path>
        <!-- Then scripts that use them -->
        <path>~/Objects/customscript_sales_order_ue.xml</path>
        <path>~/Objects/customdeploy_sales_order_ue.xml</path>
    </objects>
</deploy>
```

## Validate

### Client-Side Validation

```bash
# Validate project structure and syntax
suitecloud project:validate
```

**Checks:**
- XML syntax
- File references
- Project structure
- Dependency declarations

### Server-Side Validation

```bash
# Validate against target NetSuite account
suitecloud project:validate --server
```

**Additional Checks:**
- Object compatibility with account
- Feature availability
- Conflict detection
- Custom field references

## Deploy

### Standard Deployment

```bash
# Deploy to NetSuite account
suitecloud project:deploy

# Prompts:
# - Select authID
# - Confirm deployment
```

**Process:**
1. Validates project
2. Creates deployment package
3. Uploads to NetSuite
4. Applies customizations
5. Reports results

### Deploy with Options

```bash
# Deploy to specific account
suitecloud project:deploy --authid production

# Deploy without prompts (CI/CD)
suitecloud project:deploy --authid ci-deploy --yes

# Deploy and skip warning validation
suitecloud project:deploy --skipwarning
```

### View Deployment Status

Monitor deployment progress in NetSuite:
- Setup > SuiteCloud > Manage SuiteCloud Projects
- View deployment logs and status

## Update from NetSuite

### Sync Objects

When changes are made directly in NetSuite:

```bash
# Update local objects with NetSuite versions
suitecloud object:update

# Prompts:
# - Select authID
# - Select objects to update
# - Confirm overwrite
```

⚠️ **Warning:** This overwrites local files with NetSuite versions

### Import New Files

```bash
# Import new files added in NetSuite
suitecloud file:import
```

## Package Project

### Create Deployment Package

```bash
# Create ZIP file for distribution
suitecloud project:package

# Output: project.zip
```

**Use Cases:**
- Manual deployment
- Backup
- Distribution to other accounts

## Common Workflows

### New Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/new-automation

# 2. Create or import objects
suitecloud file:create
suitecloud object:import

# 3. Develop locally (edit files)

# 4. Validate
suitecloud project:validate

# 5. Deploy to dev environment
suitecloud project:deploy --authid dev

# 6. Test in NetSuite

# 7. Commit changes
git add .
git commit -m "Add new automation feature"

# 8. Deploy to staging
suitecloud project:deploy --authid staging

# 9. After approval, deploy to production
suitecloud project:deploy --authid production
```

### Fix Production Issue

```bash
# 1. Create hotfix branch
git checkout -b hotfix/critical-bug

# 2. Import current production state
suitecloud object:update --authid production

# 3. Fix issue locally

# 4. Validate
suitecloud project:validate --server --authid production

# 5. Deploy to production
suitecloud project:deploy --authid production

# 6. Commit fix
git add .
git commit -m "Fix critical bug in sales order processing"

# 7. Merge back to main
git checkout main
git merge hotfix/critical-bug
```

### Sync from NetSuite

When team members make changes directly in NetSuite:

```bash
# 1. Pull latest from git
git pull origin main

# 2. Update objects from NetSuite
suitecloud object:update --authid dev

# 3. Review changes
git diff

# 4. Commit synced changes
git add .
git commit -m "Sync changes from NetSuite"

# 5. Push to repository
git push origin main
```

## Troubleshooting

### Authentication Fails

```bash
# Re-authenticate
suitecloud account:setup --authid dev

# Check authID configuration
suitecloud account:manageauth
```

### Validation Errors

```bash
# Check manifest.xml for missing dependencies
# Verify all files referenced in deploy.xml exist
# Ensure XML syntax is correct

# Run validation with verbose logging
suitecloud project:validate --server --log debug
```

### Deployment Fails

**Common Issues:**
1. **Missing dependencies**: Add required features to manifest.xml
2. **Script ID conflicts**: Change script IDs in XML files
3. **File path errors**: Verify paths in deploy.xml match actual files
4. **Feature not enabled**: Enable required NetSuite features in account

**Resolution:**
```bash
# Check deployment logs in NetSuite
# Fix identified issues
# Re-validate
suitecloud project:validate --server

# Re-deploy
suitecloud project:deploy
```

### Object Update Conflicts

When local and NetSuite versions differ:

```bash
# Option 1: Keep NetSuite version
suitecloud object:update  # Overwrites local

# Option 2: Keep local version
# Simply deploy without updating
suitecloud project:deploy

# Option 3: Manual merge
# 1. Update to get NetSuite version
suitecloud object:update
# 2. Review differences
git diff
# 3. Manually merge changes
# 4. Commit merged version
```

## Best Practices

### Version Control
- ✅ Commit frequently with clear messages
- ✅ Use feature branches for development
- ✅ Review changes before committing
- ✅ Tag releases
- ❌ Don't commit authentication credentials
- ❌ Don't commit temporary files

### Project Structure
- ✅ Organize scripts by type/module
- ✅ Use consistent naming conventions
- ✅ Keep library files separate
- ✅ Document custom object relationships
- ❌ Don't nest files too deeply

### Deployment
- ✅ Always validate before deploying
- ✅ Deploy to dev/staging before production
- ✅ Test thoroughly in each environment
- ✅ Have rollback plan ready
- ❌ Don't deploy untested code
- ❌ Don't skip validation

### Collaboration
- ✅ Sync from NetSuite regularly
- ✅ Communicate changes to team
- ✅ Use pull requests for code review
- ✅ Document custom workflows
- ❌ Don't make conflicting changes
- ❌ Don't bypass review process

## Related Documentation
- [CLI Commands Reference](cli-commands.md)
- [Project Structure Guide](project-structure.md)
- [CI/CD Integration](ci-cd.md)
- [Local KB: SuiteCloud SDK](/opt/ns/kb/suitecloud-sdk-framework.md)
