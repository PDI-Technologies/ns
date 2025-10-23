# SuiteCloud SDK and Development Framework (SDF)

This document provides comprehensive information about the SuiteCloud Software Development Kit (SDK) and the SuiteCloud Development Framework (SDF), including architecture, project structure, CLI commands, and development workflows.

## Overview

### SuiteCloud SDK

The SuiteCloud Software Development Kit (SDK) provides tools for developing, testing, and deploying SuiteCloud projects. It includes command-line utilities for managing NetSuite customizations from local development environments.

### SuiteCloud Development Framework (SDF)

The SuiteCloud Development Framework (SDF) is a comprehensive development framework that enables teams to create customizations and applications within NetSuite using an integrated development environment on their local computers. SDF fundamentally transforms how developers approach NetSuite development by decoupling the development process from live NetSuite accounts.

**Key Benefits:**
- Develop locally without being connected to NetSuite accounts
- File-based project structure for version control
- Team collaboration through standard software development processes
- Integration with third-party revision control systems
- Automated deployment and validation
- Improved code portability across NetSuite environments

## Architecture

### Layered Architecture

SDF follows a layered architecture designed to provide both flexibility and robust customization capabilities:

```
┌─────────────────────────────────────────┐
│  SDF Framework Layer                    │
│  (Custom Applications & Extensions)     │
├─────────────────────────────────────────┤
│  NetSuite Layer                         │
│  (Business Data & Logic)                │
├─────────────────────────────────────────┤
│  Foundation Layer                       │
│  (Java, XML, ANT)                       │
└─────────────────────────────────────────┘
```

**Foundation Layer:**
- Core development tools including Java, XML, and ANT
- Provides underlying build and compilation capabilities

**NetSuite Layer:**
- Business data and logic that forms the core of NetSuite
- Access to NetSuite records, fields, and business processes

**SDF Framework Layer:**
- Where developers create custom applications and modifications
- Extends NetSuite's functionality using SuiteScript or JavaScript
- Enables unique business requirement implementations

### Deployment Architecture

SDF acts as a deployment mechanism between the SuiteCloud SDK and a NetSuite account:

1. **Local Development**: Developers manage NetSuite components locally within SuiteCloud SDK tools
2. **XML Representation**: NetSuite objects are represented as XML definitions in SuiteCloud projects
3. **Conversion & Deployment**: SDF converts XML definitions into NetSuite objects during deployment
4. **Validation**: SDF includes a validation process to detect discrepancies between project components and account components
5. **Overwriting**: SDF overwrites earlier versions of objects with the same script IDs and files with the same names

## Project Types

SDF supports two distinct types of SuiteCloud projects:

### Account Customization Project (ACP)

**Purpose**: Modifications created specifically for internal use within a single organization

**Characteristics:**
- Customizes existing NetSuite functionality
- Meets specific business requirements
- Not intended for commercial distribution
- Single-organization scope

**Use Cases:**
- Custom workflows for internal processes
- Company-specific forms and records
- Internal automation scripts
- Proprietary business logic

### SuiteApp Project

**Purpose**: Applications created for broader commercial distribution or use across multiple NetSuite accounts

**Characteristics:**
- Reusable solutions packaged for deployment
- Multiple NetSuite account compatibility
- Commercial distribution ready
- SuiteApp Marketplace eligible

**Use Cases:**
- Vertical industry solutions
- General business applications
- Commercial integrations
- Marketplace products

**Note**: Both project types utilize the same SuiteCloud project components and XML-based custom object definitions, but differ in their scope and intended audience.

## Project Structure

### File-Based Structure

SuiteCloud projects are organized as file-based structures stored on the local file system rather than directly in NetSuite accounts. This approach facilitates:
- Team-based development
- Quality assurance processes
- Integration testing
- Version control integration

### Directory Layout

```
my-netsuite-project/
├── manifest.xml              # Project metadata and dependencies
├── deploy.xml                # Deployment configuration and file ordering
├── src/                      # Source code directory
│   ├── FileCabinet/         # File Cabinet files
│   │   ├── SuiteScripts/    # SuiteScript files
│   │   │   ├── MyScript.js
│   │   │   └── lib/
│   │   │       └── helpers.js
│   │   └── Templates/       # Email templates, PDF templates
│   └── Objects/             # SDF custom objects (XML definitions)
│       ├── customrecord_*.xml
│       ├── customscript_*.xml
│       ├── workflow*.xml
│       └── savedcsvsimport*.xml
├── node_modules/            # Node.js dependencies (if applicable)
└── package.json             # Node.js project configuration (if applicable)
```

### Core Project Files

#### manifest.xml

**Location**: Root of the SuiteCloud project folder

**Purpose**: Contains critical project metadata

**Contents:**
- Project name
- Framework version
- Dependencies on features
- Dependencies on records
- Dependencies on files
- Required NetSuite features
- Project type (Account Customization or SuiteApp)

**Example Structure:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest projecttype="ACCOUNTCUSTOMIZATION">
    <projectname>MyCustomizationProject</projectname>
    <frameworkversion>1.0</frameworkversion>
    <dependencies>
        <features>
            <feature required="true">CUSTOMRECORDS</feature>
            <feature required="true">SERVERSIDESCRIPTING</feature>
        </features>
    </dependencies>
</manifest>
```

#### deploy.xml

**Location**: Root of the SuiteCloud project folder

**Purpose**: Controls deployment process

**Contents:**
- File paths used throughout the project
- Order in which files are uploaded to File Cabinet
- Sequence in which objects are created in target NetSuite account
- Deployment configuration options

**Example Structure:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<deploy>
    <files>
        <path>~/FileCabinet/SuiteScripts/lib/helpers.js</path>
        <path>~/FileCabinet/SuiteScripts/MyScript.js</path>
    </files>
    <objects>
        <path>~/Objects/customrecord_myrecord.xml</path>
        <path>~/Objects/customscript_myscript.xml</path>
    </objects>
</deploy>
```

#### Object Files (XML Definitions)

**Location**: `src/Objects/` directory

**Purpose**: XML definitions of SDF custom objects

**Contents:**
- All properties needed to create or modify NetSuite objects
- Custom records
- Custom forms
- Workflows
- Saved searches
- Script records
- Script deployments

**Object Types Supported:**
- Custom Record Types (`customrecord_*.xml`)
- Custom Fields (`customfield_*.xml`)
- Custom Forms (`customform_*.xml`)
- Custom Lists (`customlist_*.xml`)
- Scripts (`customscript_*.xml`)
- Script Deployments (`customdeploy_*.xml`)
- Workflows (`workflow*.xml`)
- Saved Searches (`savedsearch*.xml`)
- Roles (`role*.xml`)
- Email Templates (`emailtemplate*.xml`)
- PDF Templates (`pdftemplate*.xml`)
- Saved CSV Imports (`savedcsvsimport*.xml`)

#### SuiteScript Files

**Location**: `src/FileCabinet/SuiteScripts/` directory

**Purpose**: JavaScript-based programming files

**Contents:**
- User Event Scripts
- Client Scripts
- Scheduled Scripts
- Map/Reduce Scripts
- RESTlets
- Suitelets
- Portlets
- Workflow Action Scripts
- Mass Update Scripts
- Library files

**Key Features:**
- Based on ECMAScript specification
- Modern JavaScript syntax support
- Access to comprehensive NetSuite APIs
- Module-based architecture (SuiteScript 2.x)

## SuiteCloud CLI

### Installation

#### Prerequisites

**Node.js Version:**
- Node.js v22 LTS

**Java Version (for certain operations):**
- Oracle JDK 17 or 21

#### Install SuiteCloud CLI for Node.js

**Global Installation:**
```bash
npm install -g @oracle/suitecloud-cli
```

**CI/CD Installation (Skip License Prompt):**
```bash
npm install -g --acceptSuiteCloudSDKLicense @oracle/suitecloud-cli
```

**Version Compatibility:**
- Version 3.0.1: NetSuite 2025.1 and 2025.2
- Version 3.0.0: NetSuite 2024.2 and 2025.1

### CLI Commands Reference

#### Project Management Commands

**project:create**
```bash
suitecloud project:create
```
- Creates a new SuiteCloud project on local machine
- Prompts for project type (Account Customization or SuiteApp)
- Initializes project structure with manifest and deploy files
- Use Case: Starting a new NetSuite customization project

**project:deploy**
```bash
suitecloud project:deploy
```
- Deploys local project folder to NetSuite account
- Project folder is zipped before deployment
- Only includes files/folders referenced in deploy.xml
- Use Case: Pushing local changes to NetSuite environment

**project:validate**
```bash
suitecloud project:validate
```
- Validates project folder or ZIP file
- Ensures compliance with SuiteCloud standards
- Detects errors before deployment
- Use Case: Pre-deployment validation, CI/CD quality gates

**project:package**
```bash
suitecloud project:package
```
- Generates ZIP file from project
- Respects deploy.xml structure
- Use Case: Preparing projects for distribution or backup

**project:adddependencies**
```bash
suitecloud project:adddependencies
```
- Automatically adds missing dependencies to manifest file
- Ensures all required components are declared
- Use Case: Resolving dependency issues after importing objects

#### File Management Commands

**file:create**
```bash
suitecloud file:create
```
- Creates new SuiteScript files in selected folder
- Uses correct template with SuiteScript modules pre-injected
- Interactive prompts for script type and location
- Use Case: Generating new SuiteScript files with proper structure

**file:import**
```bash
suitecloud file:import
```
- Imports files from NetSuite account to local project
- Cannot import files from SuiteApps (Account Customization only)
- Interactive folder selection
- Use Case: Syncing existing NetSuite files to local project

**file:upload**
```bash
suitecloud file:upload
```
- Uploads files from local project to File Cabinet
- Direct file upload without full deployment
- Use Case: Quick file updates, testing individual files

**file:list**
```bash
suitecloud file:list
```
- Lists all files in NetSuite account's File Cabinet
- Shows folder structure and file paths
- Use Case: Auditing File Cabinet contents, finding file paths

#### Object Management Commands

**object:import**
```bash
suitecloud object:import
```
- Imports custom SDF objects from NetSuite to local project
- Auto-imports referenced SuiteScript files (Account Customization only)
- Interactive object selection
- Use Case: Bringing existing customizations into local project

**object:list**
```bash
suitecloud object:list
```
- Lists all custom SDF objects deployed in NetSuite account
- Shows object types and script IDs
- Use Case: Discovering what objects exist in NetSuite

**object:update**
```bash
suitecloud object:update
```
- Overwrites local objects with matching objects from NetSuite
- Syncs with latest server state
- Use Case: Pulling changes made directly in NetSuite

#### Authentication Commands

**account:setup**
```bash
suitecloud account:setup
```
- Sets up account for use with SuiteCloud CLI
- Configures default authentication ID for project
- Requires browser-based login to NetSuite
- Creates authID (custom alias for account-role combination)
- Use Case: Initial authentication setup for local development

**account:setup:ci**
```bash
suitecloud account:setup:ci
```
- CI/CD authentication without browser interaction
- Enables fully automated deployment workflows
- Token-based authentication
- Use Case: Continuous integration pipelines, automated deployments

**account:manageauth**
```bash
suitecloud account:manageauth
```
- Manages authentication IDs (authIDs) for all projects
- List, add, remove, or update authIDs
- Multiple NetSuite environment support
- Use Case: Managing credentials for dev/staging/production environments

**account:savetoken**
```bash
suitecloud account:savetoken
```
- Saves Token-Based Authentication (TBA) token
- Programmatic authentication setup
- Use Case: Script-based deployments, automation

#### Additional Commands

**suitecloud package**
```bash
suitecloud package
```
- Packages project into deployable format
- Bundles customizations for efficient upload
- Use Case: Preparing for deployment, creating distribution packages

**suitecloud validate**
```bash
suitecloud validate
```
- Validates project files and configurations
- Checks syntax errors and NetSuite standards adherence
- Client-side and server-side validation options
- Use Case: Pre-deployment checks, quality assurance

### Command Options and Flags

**Common Options:**
- `--authid <authid>`: Specify authentication ID to use
- `--project <path>`: Specify project path
- `--help`: Display help information
- `--version`: Display CLI version

**Validation Options:**
- `-server`: Perform server-side validation (requires authentication)
- `-l <logfile>`: Specify log file location

**Import Options:**
- `--appid <appid>`: Filter by application ID
- `--scriptid <scriptid>`: Filter by script ID
- `--type <types>`: Filter by object type

## Development Workflows

### Standard Development Workflow (Local to NetSuite)

#### Step 1: Project Initialization
```bash
# Create new project
suitecloud project:create

# Navigate to project directory
cd my-netsuite-project
```

#### Step 2: Authentication Configuration
```bash
# Set up authentication
suitecloud account:setup

# Verify authentication
suitecloud account:manageauth
```

#### Step 3: Development and File Management

**Option A: Starting from Existing NetSuite Customizations**
```bash
# Import existing files from NetSuite
suitecloud file:import

# Import existing custom objects
suitecloud object:import
```

**Option B: Creating New Customizations**
```bash
# Create new SuiteScript file
suitecloud file:create

# Manually create XML object definitions in src/Objects/
```

#### Step 4: Local Development

- Edit SuiteScript files in `src/FileCabinet/SuiteScripts/`
- Modify XML object definitions in `src/Objects/`
- Update manifest.xml with dependencies
- Configure deploy.xml with file/object ordering

#### Step 5: Project Validation
```bash
# Client-side validation
suitecloud project:validate

# Server-side validation (requires authentication)
suitecloud validate -server -authid <authid>
```

#### Step 6: Deployment
```bash
# Deploy to NetSuite
suitecloud project:deploy
```

#### Step 7: Synchronization (If Needed)

**When changes are made directly in NetSuite:**
```bash
# Sync objects back to local project
suitecloud object:update

# Import new/modified files
suitecloud file:import
```

### Team Collaboration Workflow

#### Initial Setup (Each Team Member)

```bash
# Clone repository
git clone <repository-url>
cd <project-directory>

# Install dependencies (if Node.js project)
npm install

# Set up local authentication
suitecloud account:setup
```

#### Development Cycle

```bash
# Create feature branch
git checkout -b feature/my-customization

# Import latest objects from NetSuite (if needed)
suitecloud object:import

# Develop locally
# ... make changes to files ...

# Validate before committing
suitecloud project:validate

# Commit changes
git add .
git commit -m "Add custom record type for project tracking"

# Push to remote
git push origin feature/my-customization
```

#### Code Review and Merge

```bash
# Create pull request (via GitHub/GitLab/etc.)

# After approval, merge to main branch
git checkout main
git pull origin main

# Deploy to development environment
suitecloud project:deploy --authid dev

# After testing, deploy to production
suitecloud project:deploy --authid production
```

### CI/CD Workflow

#### Pipeline Configuration Example

```yaml
# Example CI/CD pipeline (pseudo-code)
stages:
  - validate
  - package
  - deploy-dev
  - deploy-staging
  - deploy-production

validate:
  script:
    - npm install -g --acceptSuiteCloudSDKLicense @oracle/suitecloud-cli
    - suitecloud account:setup:ci --authid ci-dev
    - suitecloud project:validate

package:
  script:
    - suitecloud project:package
  artifacts:
    - project.zip

deploy-dev:
  script:
    - suitecloud project:deploy --authid ci-dev
  only:
    - develop

deploy-staging:
  script:
    - suitecloud project:deploy --authid ci-staging
  only:
    - staging

deploy-production:
  script:
    - suitecloud project:deploy --authid ci-production
  only:
    - main
  when: manual
```

#### CI/CD Best Practices

**Authentication:**
- Use `account:setup:ci` for non-interactive authentication
- Store credentials securely in CI/CD secrets
- Create separate authIDs for each environment

**Validation:**
- Run `project:validate` as mandatory step
- Fail pipeline if validation errors occur
- Consider server-side validation for comprehensive checks

**Deployment Strategy:**
- Automatic deployment to dev/staging from feature branches
- Manual approval gate for production deployments
- Tag releases in version control

**Artifacts:**
- Package projects with `project:package`
- Store deployment packages as artifacts
- Enable rollback capabilities

## Best Practices

### Project Organization

**Folder Structure:**
- Keep SuiteScript files organized by type (User Events, Client Scripts, Libraries)
- Use subdirectories for logical grouping
- Follow consistent naming conventions

**Naming Conventions:**
- **Script IDs**: Use descriptive prefixes (e.g., `customscript_ue_sales_order_validate`)
- **Files**: Match file names to script IDs for easy identification
- **Objects**: Use clear, descriptive names in XML definitions

### Development Practices

**Version Control:**
- Store all SuiteCloud projects in Git or other VCS
- Commit frequently with clear commit messages
- Use branching strategy (feature branches, develop, main)
- Never commit sensitive credentials

**Code Reviews:**
- Implement peer code review process
- Use pull requests for all changes
- Review both SuiteScript code and XML object definitions
- Check deploy.xml for correct file ordering

**Documentation:**
- Document custom objects and their purpose
- Add JSDoc comments to SuiteScript functions
- Maintain README.md with project setup instructions
- Document authentication setup for each environment

**Testing:**
- Test locally before committing
- Validate projects before deployment
- Use development/sandbox accounts for testing
- Implement automated tests where possible

### Deployment Best Practices

**deploy.xml Management:**
- Maintain well-organized deploy.xml
- Specify exact files and folders to include
- Order objects properly (dependencies first)
- Exclude temporary files and development artifacts

**Environment Management:**
- Create separate authIDs for each environment
- Use consistent naming: `dev`, `staging`, `production`
- Never deploy directly to production without testing
- Document environment-specific configurations

**Validation:**
- Always run `project:validate` before deployment
- Use server-side validation for comprehensive checks
- Fix all validation errors before proceeding
- Integrate validation into pre-commit hooks

**Deployment Process:**
- Deploy to development environment first
- Test thoroughly in staging
- Schedule production deployments during maintenance windows
- Have rollback plan ready
- Document deployment steps

### Authentication Management

**Security:**
- Never commit authentication credentials to version control
- Use environment variables for CI/CD credentials
- Rotate TBA tokens regularly
- Limit role permissions to minimum required

**Organization:**
- Document all authIDs and their purposes
- Keep authentication configuration separate from code
- Use descriptive authID names
- Maintain list of who has access to each environment

## CI/CD Integration

### Key Benefits

**Scriptable Authentication:**
- Token-based authentication eliminates manual credential entry
- `account:setup:ci` enables fully automated pipelines
- Secure credential storage in CI/CD secrets

**Automated Validation:**
- Run `project:validate` as part of build process
- Catch errors before production deployment
- Enforce coding standards and best practices

**Conditional Deployment:**
- Deploy only when validation succeeds
- Environment-specific deployment conditions
- Manual approval gates for production

**Multiple Environment Support:**
- Manage different authIDs for each environment
- Promote code through environments systematically
- Consistent deployment process across all stages

### CI/CD Pipeline Steps

**Typical Pipeline Stages:**

1. **Checkout**: Clone repository from version control
2. **Setup**: Install SuiteCloud CLI with `--acceptSuiteCloudSDKLicense`
3. **Authenticate**: Run `account:setup:ci` with environment credentials
4. **Validate**: Execute `project:validate` to check for errors
5. **Package**: Create deployment package with `project:package`
6. **Deploy**: Run `project:deploy` to target environment
7. **Verify**: Run post-deployment tests (if applicable)

### Platform-Specific Examples

**GitHub Actions:**
```yaml
name: Deploy to NetSuite

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '22'

      - name: Install SuiteCloud CLI
        run: npm install -g --acceptSuiteCloudSDKLicense @oracle/suitecloud-cli

      - name: Authenticate
        run: suitecloud account:setup:ci
        env:
          NS_ACCOUNT: ${{ secrets.NS_ACCOUNT }}
          NS_TOKEN_ID: ${{ secrets.NS_TOKEN_ID }}
          NS_TOKEN_SECRET: ${{ secrets.NS_TOKEN_SECRET }}

      - name: Validate
        run: suitecloud project:validate

      - name: Deploy
        run: suitecloud project:deploy
```

**GitLab CI:**
```yaml
stages:
  - validate
  - deploy

validate:
  stage: validate
  image: node:22
  script:
    - npm install -g --acceptSuiteCloudSDKLicense @oracle/suitecloud-cli
    - suitecloud account:setup:ci
    - suitecloud project:validate

deploy:
  stage: deploy
  image: node:22
  script:
    - npm install -g --acceptSuiteCloudSDKLicense @oracle/suitecloud-cli
    - suitecloud account:setup:ci
    - suitecloud project:deploy
  only:
    - main
```

## Relationship to Other NetSuite Technologies

### SuiteScript Integration

**SuiteScript 2.1:**
- Latest version with modern ECMAScript features
- Arrow functions, const/let declarations, template literals
- Module-based architecture (N/record, N/search, N/query, etc.)
- Comprehensive platform APIs

**Script Types Managed by SDF:**
- User Event Scripts (beforeLoad, beforeSubmit, afterSubmit)
- Client Scripts (pageInit, fieldChanged, saveRecord)
- Scheduled Scripts (execute)
- Map/Reduce Scripts (getInputData, map, reduce, summarize)
- RESTlets (get, post, put, delete)
- Suitelets (onRequest)
- Portlets (portlet)
- Workflow Action Scripts
- Mass Update Scripts

### SuiteTalk Integration

**SuiteTalk Web Services:**
- SOAP API and REST API for external integrations
- SDF manages custom objects accessible via SuiteTalk
- Authentication credentials (TBA) used for both SDF and SuiteTalk

**Use Cases:**
- External system integrations
- Data synchronization
- Automated record operations
- Third-party application connections

### File Cabinet Integration

**File Management:**
- SDF manages File Cabinet files locally in `src/FileCabinet/`
- Files deployed via `file:upload` or `project:deploy`
- Folder structure preserved during deployment

**File Types:**
- SuiteScript files (.js)
- HTML templates (.html)
- CSS stylesheets (.css)
- Images and media files
- PDF templates
- Email templates
- CSV files
- Documentation files

## Development Tools

### SuiteCloud Extension

**Description**: User interface for NetSuite platform development

**Features:**
- Visual project management
- Integrated development environment
- GUI-based deployment
- Object browser and editor

**Use Case**: Developers who prefer GUI tools over command-line

### SuiteCloud IDE Plug-in

**Description**: Integrated development environment packaged for NetSuite

**Supported IDEs:**
- Eclipse
- WebStorm
- VS Code (SuiteCloud Extension for VS Code 2025.1+)

**Features:**
- SuiteScript syntax highlighting
- Code completion for NetSuite modules
- Integrated debugging
- SDF project management
- Direct deployment from IDE

**Use Case**: Full-featured IDE experience with NetSuite integration

### SuiteCloud CLI

**Description**: Command-line interface for development automation

**Features:**
- Scriptable workflows
- CI/CD integration
- Batch operations
- Shell script support
- Works with any text editor/IDE

**Use Case**: Automation, CI/CD pipelines, power users, team workflows

## Version History and Updates

### Latest Version (2025)

**SuiteCloud CLI v3.0.1:**
- NetSuite 2025.1 and 2025.2 compatibility
- Node.js 22 LTS support
- Oracle JDK 17 and 21 support

**SuiteCloud SDK Updates (2025.1+):**
- Secure Credentials Storage with PKCS#12 encryption
- Visual Studio Code 2025.1 SuiteCloud Extension
- Enhanced authentication features
- Improved validation capabilities

### Authentication Changes (2025)

**OAuth 2.0 Mandatory (February 2025):**
- OAuth 1.0 completely removed from SuiteCloud SDK
- TBA functionality removed from CI environments (2024.2)
- All integrations must use OAuth 2.0

**Migration Required:**
- Update all authentication workflows to OAuth 2.0
- Replace TBA tokens with OAuth 2.0 credentials
- Update CI/CD pipelines for new authentication

## Troubleshooting

### Common Issues

**Validation Errors:**
- Check manifest.xml for missing dependencies
- Verify deploy.xml references all required files
- Ensure object XML syntax is correct
- Check for circular dependencies

**Authentication Failures:**
- Verify authID is configured correctly
- Check TBA token expiration
- Ensure role has sufficient permissions
- Confirm account ID is correct

**Deployment Failures:**
- Review validation output for errors
- Check File Cabinet folder permissions
- Verify object dependencies are met
- Ensure no conflicting customizations exist

**Import Issues:**
- Confirm object exists in NetSuite account
- Check that features are enabled (e.g., CUSTOMRECORDS)
- Verify role has permission to view objects
- Ensure SuiteApp objects use correct commands

## References

### Official Documentation

- **SuiteCloud Development Framework Guide**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_1558708800.html
- **NetSuite Developer Portal**: https://developers.netsuite.com/
- **SuiteScript API Reference**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4267255811.html
- **SuiteCloud CLI Documentation**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4724784139.html

### Package Repositories

- **NPM (@oracle/suitecloud-cli)**: https://www.npmjs.com/package/@oracle/suitecloud-cli
- **Context7 Library ID**: `/oracle-samples/netsuite-suitecloud-samples`

### Community Resources

- **GitHub Samples**: https://github.com/oracle-samples/netsuite-suitecloud-samples
- **SuiteAnswers**: https://support.netsuite.com/
- **NetSuite Professionals Community**: Various forums and user groups

## Last Updated

October 23, 2025
