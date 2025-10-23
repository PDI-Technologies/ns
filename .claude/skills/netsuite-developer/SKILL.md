---
name: netsuite-developer
description: Develops and deploys NetSuite customizations using SuiteScript 2.x (User Events, Client Scripts, Scheduled, Map/Reduce, RESTlets, Suitelets) and SuiteCloud Development Framework (SDF). Handles project creation, validation, deployment via CLI, CI/CD pipelines, and debugging. Use when writing NetSuite scripts, deploying customizations, or setting up development workflows.
---

# NetSuite Developer

Comprehensive skill for developing, testing, and deploying NetSuite customizations using SuiteScript 2.x and SuiteCloud Development Framework (SDF).

## Quick Start

### Common Tasks
- **Create User Event Script**: See [suitescript/user-events.md](suitescript/user-events.md)
- **Create Client Script**: See [suitescript/client-scripts.md](suitescript/client-scripts.md)
- **Create RESTlet API**: See [suitescript/restlets.md](suitescript/restlets.md)
- **Deploy Project**: See [deployment/sdf-workflow.md](deployment/sdf-workflow.md)
- **Setup CI/CD**: See [deployment/ci-cd.md](deployment/ci-cd.md)

### Script Type Selection Guide

| Script Type | Runs On | Use Case | Entry Points |
|-------------|---------|----------|--------------|
| **User Event** | Server | Record lifecycle automation | beforeLoad, beforeSubmit, afterSubmit |
| **Client Script** | Browser | UI validation, field changes | pageInit, fieldChanged, saveRecord |
| **Scheduled** | Server | Time-based batch processing | execute |
| **Map/Reduce** | Server | Large-scale data processing | getInputData, map, reduce, summarize |
| **RESTlet** | Server | Custom REST API endpoints | get, post, put, delete |
| **Suitelet** | Server | Custom web pages/forms | onRequest |
| **Workflow Action** | Server | Custom workflow actions | onAction |
| **Mass Update** | Server | Bulk record updates | each |
| **Portlet** | Server | Dashboard widgets | portlet |

## Knowledge Base Resources

### Local KB Documentation
- **SuiteScript Modules**: [/opt/ns/kb/suitescript-modules.md](/opt/ns/kb/suitescript-modules.md)
- **SuiteCloud SDK/SDF**: [/opt/ns/kb/suitecloud-sdk-framework.md](/opt/ns/kb/suitecloud-sdk-framework.md)
- **Authentication**: [/opt/ns/kb/authentication.md](/opt/ns/kb/authentication.md)
- **RESTlets**: [/opt/ns/kb/restlets.md](/opt/ns/kb/restlets.md)
- **SuiteTalk REST API**: [/opt/ns/kb/suitetalk-rest-api.md](/opt/ns/kb/suitetalk-rest-api.md)
- **Third-Party SDKs**: [/opt/ns/kb/third-party-sdks.md](/opt/ns/kb/third-party-sdks.md)
- **Open Source Projects**: [/opt/ns/kb/open-source-projects.md](/opt/ns/kb/open-source-projects.md)

See also: [kb-reference.md](kb-reference.md) for indexed navigation

### Archon Vector KB Search
For official NetSuite documentation and code examples:

```javascript
// Search knowledge base
mcp__archon__rag_search_knowledge_base(
  query="your search terms",
  source_id="netsuite",  // if available
  match_count=5
)

// Search code examples
mcp__archon__rag_search_code_examples(
  query="your search terms",
  source_id="netsuite",  // if available
  match_count=3
)
```

### Context7 Documentation
For external library documentation:

```javascript
// Resolve library ID
mcp__context7__resolve-library-id(libraryName="netsuite")

// Get library docs
mcp__context7__get-library-docs(
  context7CompatibleLibraryID="/oracle-samples/netsuite-suitecloud-samples",
  topic="your topic",
  tokens=5000
)
```

## SuiteScript Development

### Script Types

**User Event Scripts** (Server-side, Record Lifecycle)
- See [suitescript/user-events.md](suitescript/user-events.md)
- Entry points: beforeLoad, beforeSubmit, afterSubmit
- Use cases: Validation, automation, custom logic on records

**Client Scripts** (Browser-side, UI Interactions)
- See [suitescript/client-scripts.md](suitescript/client-scripts.md)
- Entry points: pageInit, fieldChanged, saveRecord, validateField, lineInit, etc.
- Use cases: Real-time validation, dynamic UI, field dependencies

**Scheduled Scripts** (Server-side, Time-based)
- See [suitescript/scheduled.md](suitescript/scheduled.md)
- Entry point: execute
- Use cases: Batch processing, nightly jobs, periodic maintenance

**Map/Reduce Scripts** (Server-side, High-volume)
- See [suitescript/map-reduce.md](suitescript/map-reduce.md)
- Entry points: getInputData, map, reduce, summarize
- Use cases: Large data processing, bulk updates, complex calculations

**RESTlet Scripts** (Server-side, API Endpoints)
- See [suitescript/restlets.md](suitescript/restlets.md)
- Entry points: get, post, put, delete
- Use cases: External integrations, custom APIs, mobile apps

**Suitelet Scripts** (Server-side, Web Pages)
- See [suitescript/suitelets.md](suitescript/suitelets.md)
- Entry point: onRequest
- Use cases: Custom forms, portals, interactive pages

**Workflow Action Scripts** (Server-side, Workflows)
- See [suitescript/workflow-actions.md](suitescript/workflow-actions.md)
- Entry point: onAction
- Use cases: Custom workflow steps, complex business logic

**Mass Update Scripts** (Server-side, Bulk Operations)
- See [suitescript/mass-update.md](suitescript/mass-update.md)
- Entry point: each
- Use cases: Bulk record updates via UI

**Portlet Scripts** (Server-side, Dashboards)
- See [suitescript/portlets.md](suitescript/portlets.md)
- Entry point: portlet
- Use cases: Dashboard widgets, custom metrics displays

### Module Reference

**Core Modules**
- **N/record**: Record operations (load, create, update, delete)
- **N/search**: Create and execute searches
- **N/query**: SuiteQL queries (advanced)
- **N/log**: Logging and debugging
- **N/runtime**: Runtime information (user, script, execution context)
- **N/error**: Error handling and custom errors

**Data Modules**
- **N/file**: File operations
- **N/dataset**: Dataset operations
- **N/format**: Date and number formatting
- **N/encode**: Encoding/decoding
- **N/xml**: XML parsing

**Communication Modules**
- **N/http**: HTTP requests (client-side)
- **N/https**: HTTPS requests (server-side)
- **N/email**: Send emails
- **N/url**: URL operations

**UI Modules**
- **N/ui/serverWidget**: Create forms, fields, sublists
- **N/ui/dialog**: Alert, confirm, create dialogs
- **N/ui/message**: Display messages

**Business Modules**
- **N/transaction**: Transaction operations
- **N/task**: Schedule tasks (map/reduce, scheduled scripts)
- **N/workflow**: Workflow operations
- **N/redirect**: Redirect to pages

**Utility Modules**
- **N/cache**: Cache operations
- **N/crypto**: Cryptographic operations
- **N/currency**: Currency operations
- **N/commerce**: Commerce operations

For detailed module documentation, see [/opt/ns/kb/suitescript-modules.md](/opt/ns/kb/suitescript-modules.md)

## SuiteCloud Development Framework (SDF)

### Project Management

**Create New Project**
- See [deployment/sdf-workflow.md](deployment/sdf-workflow.md#create-project)
- Command: `suitecloud project:create`

**Project Structure**
- See [deployment/project-structure.md](deployment/project-structure.md)
- manifest.xml, deploy.xml, src/FileCabinet, src/Objects

**Validate Project**
- See [deployment/sdf-workflow.md](deployment/sdf-workflow.md#validate)
- Command: `suitecloud project:validate`

**Deploy Project**
- See [deployment/sdf-workflow.md](deployment/sdf-workflow.md#deploy)
- Command: `suitecloud project:deploy`

### CLI Commands Reference

**Project Commands**
- See [deployment/cli-commands.md](deployment/cli-commands.md#project)
- project:create, project:deploy, project:validate, project:package, project:adddependencies

**File Commands**
- See [deployment/cli-commands.md](deployment/cli-commands.md#files)
- file:create, file:import, file:upload, file:list

**Object Commands**
- See [deployment/cli-commands.md](deployment/cli-commands.md#objects)
- object:import, object:list, object:update

**Authentication Commands**
- See [deployment/cli-commands.md](deployment/cli-commands.md#authentication)
- account:setup, account:manageauth, account:savetoken, account:setup:ci

### CI/CD Integration

**GitHub Actions**
- See [deployment/ci-cd.md](deployment/ci-cd.md#github-actions)
- Automated validation and deployment workflows

**GitLab CI**
- See [deployment/ci-cd.md](deployment/ci-cd.md#gitlab-ci)
- Pipeline configuration examples

**Jenkins**
- See [deployment/ci-cd.md](deployment/ci-cd.md#jenkins)
- Build job setup

**Best Practices**
- See [deployment/ci-cd-best-practices.md](deployment/ci-cd-best-practices.md)
- Environment management, secrets, deployment strategies

## Development Patterns

### Error Handling
- See [patterns/error-handling.md](patterns/error-handling.md)
- Try-catch patterns, error logging, error recovery
- Custom error types, user messaging

### Governance Management
- See [patterns/governance.md](patterns/governance.md)
- Understanding governance units
- Optimization techniques
- Yield patterns for scheduled scripts

### Performance Optimization
- See [patterns/performance.md](patterns/performance.md)
- Search optimization
- Caching strategies
- Batch processing
- Lazy loading

### Security Best Practices
- See [patterns/security.md](patterns/security.md)
- Input validation
- SQL injection prevention
- XSS protection
- Role-based security

### Code Organization
- See [patterns/code-organization.md](patterns/code-organization.md)
- Module structure
- Library files
- Code reuse patterns

## Testing and Debugging

### Unit Testing
- See [testing/unit-testing.md](testing/unit-testing.md)
- Testing frameworks for SuiteScript
- Mock objects and data
- Test patterns

### Debugging Techniques
- See [testing/debugging.md](testing/debugging.md)
- Using N/log effectively
- Browser developer tools
- Debugging User Events vs Client Scripts

### Testing Workflows
- See [testing/testing-workflow.md](testing/testing-workflow.md)
- Local testing strategies
- Sandbox testing
- Production deployment checklist

### Common Issues
- See [testing/troubleshooting.md](testing/troubleshooting.md)
- Script errors and solutions
- Performance issues
- Deployment problems

## Code Examples

### Sales Order Automation
- See [examples/sales-order-automation.md](examples/sales-order-automation.md)
- User Event for validation and automation
- Client Script for real-time updates

### Invoice Processing
- See [examples/invoice-processing.md](examples/invoice-processing.md)
- Scheduled Script for batch invoice creation
- RESTlet for external invoice submission

### Customer Portal
- See [examples/customer-portal.md](examples/customer-portal.md)
- Suitelet for custom portal
- Client Script for interactive forms

### Inventory Management
- See [examples/inventory-management.md](examples/inventory-management.md)
- Map/Reduce for inventory adjustments
- Scheduled Script for reorder point monitoring

### Integration Endpoints
- See [examples/integration-endpoints.md](examples/integration-endpoints.md)
- RESTlet for external system integration
- Error handling and validation

## Templates

### Script Templates
- See [templates/](templates/)
- User Event template
- Client Script template
- Scheduled Script template
- Map/Reduce template
- RESTlet template
- Suitelet template

### Project Templates
- See [templates/sdf-project/](templates/sdf-project/)
- SDF project structure
- manifest.xml template
- deploy.xml template

### CI/CD Templates
- See [templates/ci-cd/](templates/ci-cd/)
- GitHub Actions workflow
- GitLab CI pipeline
- Jenkins Jenkinsfile

## Reference Documentation

### Complete File Index

**SuiteScript Development:**
- [suitescript/user-events.md](suitescript/user-events.md)
- [suitescript/client-scripts.md](suitescript/client-scripts.md)
- [suitescript/scheduled.md](suitescript/scheduled.md)
- [suitescript/map-reduce.md](suitescript/map-reduce.md)
- [suitescript/restlets.md](suitescript/restlets.md)
- [suitescript/suitelets.md](suitescript/suitelets.md)
- [suitescript/workflow-actions.md](suitescript/workflow-actions.md)
- [suitescript/mass-update.md](suitescript/mass-update.md)
- [suitescript/portlets.md](suitescript/portlets.md)

**Deployment:**
- [deployment/sdf-workflow.md](deployment/sdf-workflow.md)
- [deployment/cli-commands.md](deployment/cli-commands.md)
- [deployment/project-structure.md](deployment/project-structure.md)
- [deployment/ci-cd.md](deployment/ci-cd.md)
- [deployment/ci-cd-best-practices.md](deployment/ci-cd-best-practices.md)

**Patterns:**
- [patterns/error-handling.md](patterns/error-handling.md)
- [patterns/governance.md](patterns/governance.md)
- [patterns/performance.md](patterns/performance.md)
- [patterns/security.md](patterns/security.md)
- [patterns/code-organization.md](patterns/code-organization.md)

**Testing:**
- [testing/unit-testing.md](testing/unit-testing.md)
- [testing/debugging.md](testing/debugging.md)
- [testing/testing-workflow.md](testing/testing-workflow.md)
- [testing/troubleshooting.md](testing/troubleshooting.md)

**Examples:**
- [examples/sales-order-automation.md](examples/sales-order-automation.md)
- [examples/invoice-processing.md](examples/invoice-processing.md)
- [examples/customer-portal.md](examples/customer-portal.md)
- [examples/inventory-management.md](examples/inventory-management.md)
- [examples/integration-endpoints.md](examples/integration-endpoints.md)

**Templates:**
- [templates/user-event.js](templates/user-event.js)
- [templates/client-script.js](templates/client-script.js)
- [templates/scheduled-script.js](templates/scheduled-script.js)
- [templates/map-reduce-script.js](templates/map-reduce-script.js)
- [templates/restlet.js](templates/restlet.js)
- [templates/suitelet.js](templates/suitelet.js)

**Knowledge Base:**
- [kb-reference.md](kb-reference.md)
