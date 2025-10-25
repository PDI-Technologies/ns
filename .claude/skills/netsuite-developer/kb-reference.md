# Knowledge Base Reference Index

Comprehensive index of local KB documentation for NetSuite development.

## Local KB Files

All KB files located in `/opt/ns/kb/`

### Core Documentation

#### [suitescript-modules.md](/opt/ns/kb/suitescript-modules.md)
**Complete SuiteScript module reference**

Modules covered:
- N/record - Record operations
- N/search - Search operations
- N/query - SuiteQL queries
- N/log - Logging
- N/runtime - Runtime information
- N/error - Error handling
- N/file - File operations
- N/http, N/https - HTTP requests
- N/email - Email operations
- N/ui/serverWidget - UI components
- N/task - Task scheduling
- N/transaction - Transaction operations
- N/workflow - Workflow operations
- N/currency - Currency operations
- N/format - Formatting
- N/encode - Encoding/decoding
- N/xml - XML parsing
- N/crypto - Cryptographic operations
- N/cache - Caching

#### [suitecloud-sdk-framework.md](/opt/ns/kb/suitecloud-sdk-framework.md)
**Complete SuiteCloud SDK and SDF guide**

Topics covered:
- SDF Architecture (layered architecture)
- Project Types (Account Customization vs SuiteApp)
- Project Structure (directory layout, manifest.xml, deploy.xml)
- Object Types (50+ supported types)
- CLI Commands (project, file, object, authentication)
- Development Workflows (local to NetSuite)
- CI/CD Integration (GitHub Actions, GitLab CI)
- Best Practices
- Troubleshooting

#### [authentication.md](/opt/ns/kb/authentication.md)
**NetSuite authentication methods**

Topics covered:
- OAuth 2.0 (current standard)
- Token-Based Authentication (TBA) - deprecated
- SuiteCloud SDK authentication
- CI/CD authentication setup
- Security best practices

#### [restlets.md](/opt/ns/kb/restlets.md)
**RESTlet development guide**

Topics covered:
- RESTlet basics
- HTTP methods (GET, POST, PUT, DELETE)
- Authentication for RESTlets
- Request/response handling
- Error handling patterns
- Security considerations
- Deployment configuration

#### [suitetalk-rest-api.md](/opt/ns/kb/suitetalk-rest-api.md)
**SuiteTalk REST API reference**

Topics covered:
- REST API basics
- Authentication
- Record operations (CRUD)
- Search operations
- SuiteQL queries
- Batch operations
- Rate limiting
- Best practices

#### [third-party-sdks.md](/opt/ns/kb/third-party-sdks.md)
**Third-party SDKs and tools**

SDKs covered:
- Python SDKs (netsuite, netsuite-sdk-py, suitepy)
- Node.js tools (@oracle/suitecloud-cli, netsuite-restlet-api)
- Java SOAP clients
- PHP SDK
- Rust library
- Go client
- Enterprise iPaaS (Celigo, Boomi, MuleSoft)
- ODBC/JDBC drivers

#### [open-source-projects.md](/opt/ns/kb/open-source-projects.md)
**Open-source NetSuite projects**

Projects covered:
- oracle-samples/netsuite-suitecloud-samples (117⭐)
- TypeScript typings
- API clients
- Testing frameworks (netsumo, mochafornetsuite)
- Integration tools (n8n nodes)
- Development tools

### New Patterns (2025-01)

**Critical NetSuite REST API & Integration Patterns**

#### [patterns/rest-api-queries.md](patterns/rest-api-queries.md) ⚠️ CRITICAL
**2-Step Data Fetching Pattern**
- Why query endpoint returns IDs ONLY
- Correct 2-step pattern for complete data (query IDs → fetch full records)
- Performance implications (9000 vendors = 9000+ API calls)
- Optimization strategies (incremental sync, parallel fetching, caching)
- **This is THE most common NetSuite REST API mistake**

#### [patterns/authentication-methods.md](patterns/authentication-methods.md)
**Multi-Method Authentication**
- TBA vs OAuth 2.0 comparison and migration path
- Credential vernacular (CONSUMER not CLIENT)
- Complete 4-credential TBA setup (Consumer Key/Secret + Token ID/Secret)
- Multi-method factory pattern for flexible auth
- OAuth 2.0 requirements for 2025+

#### [patterns/oauth-signatures.md](patterns/oauth-signatures.md)
**OAuth 1.0 Signature Bug Pattern**
- Critical bug: Query parameters MUST be in signature base string
- Step-by-step signature generation
- Common 401 "Invalid login attempt" fixes
- Signature debugging and verification

#### [patterns/custom-fields.md](patterns/custom-fields.md)
**Custom Field Handling**
- Field classification (custentity_*, custbody_*, custitem_*, custrecord_*)
- Discovering custom fields (20-40 per record type common)
- Reference field extraction (currency, terms, etc.)
- Flexible storage patterns (Pydantic `extra="allow"`, JSONB)
- Field lifecycle tracking (first_seen, last_seen, deprecated)

#### [testing/diagnostics-without-ui.md](testing/diagnostics-without-ui.md)
**Diagnostics Without NetSuite UI Access**
- Testing authentication programmatically
- Admin checklists for 401 Unauthorized errors
- Admin checklists for 403 Forbidden errors
- Diagnostic script patterns
- Actionable error messages

## Quick Lookup Guide

### By Development Task

| Task | KB File | Section |
|------|---------|---------|
| Create User Event | suitescript-modules.md | N/record, Entry Points |
| Create Client Script | suitescript-modules.md | Client-side modules |
| Create Scheduled Script | suitescript-modules.md | N/task, Scheduled |
| Create Map/Reduce | suitescript-modules.md | Map/Reduce Entry Points |
| Create RESTlet | restlets.md | Complete guide |
| Setup SDF Project | suitecloud-sdk-framework.md | Project Structure |
| Deploy with CLI | suitecloud-sdk-framework.md | CLI Commands |
| Setup OAuth 2.0 | authentication.md | OAuth 2.0 section |
| Setup CI/CD | suitecloud-sdk-framework.md | CI/CD Integration |
| Use SuiteTalk API | suitetalk-rest-api.md | Complete guide |
| Find Python SDK | third-party-sdks.md | Python section |
| Find Examples | open-source-projects.md | Complete list |

### By Module

| Module | KB File | Description |
|--------|---------|-------------|
| N/record | suitescript-modules.md | Load, create, update, delete records |
| N/search | suitescript-modules.md | Create and execute searches |
| N/query | suitescript-modules.md | SuiteQL queries |
| N/log | suitescript-modules.md | Logging and debugging |
| N/runtime | suitescript-modules.md | Runtime information |
| N/error | suitescript-modules.md | Error handling |
| N/file | suitescript-modules.md | File operations |
| N/http(s) | suitescript-modules.md | HTTP requests |
| N/email | suitescript-modules.md | Send emails |
| N/ui/serverWidget | suitescript-modules.md | Create UI components |
| N/task | suitescript-modules.md | Schedule tasks |
| N/workflow | suitescript-modules.md | Workflow operations |

### By Integration Type

| Integration | KB File | Details |
|-------------|---------|---------|
| REST API (External → NS) | restlets.md | Create RESTlet endpoints |
| REST API (NS → External) | suitescript-modules.md | N/http, N/https |
| SuiteTalk REST | suitetalk-rest-api.md | Use NetSuite REST API |
| Python Integration | third-party-sdks.md | Python SDKs |
| Node.js Integration | third-party-sdks.md | Node.js tools |
| Database Integration | third-party-sdks.md | ODBC/JDBC drivers |
| iPaaS Integration | third-party-sdks.md | Celigo, Boomi, etc. |

### By Deployment Method

| Method | KB File | Section |
|--------|---------|---------|
| SDF/CLI | suitecloud-sdk-framework.md | Complete guide |
| GitHub Actions | suitecloud-sdk-framework.md | CI/CD - GitHub Actions |
| GitLab CI | suitecloud-sdk-framework.md | CI/CD - GitLab CI |
| Manual Upload | suitetalk-rest-api.md | File operations |

## Search Patterns

### Archon Vector KB

```javascript
// Search for NetSuite documentation
mcp__archon__rag_search_knowledge_base(
  query="User Event beforeSubmit",
  source_id="netsuite",  // if available
  match_count=5
)

// Search for code examples
mcp__archon__rag_search_code_examples(
  query="N/record load update",
  source_id="netsuite",  // if available
  match_count=3
)
```

### Context7 Documentation

```javascript
// Get NetSuite SuiteCloud samples
mcp__context7__get-library-docs(
  context7CompatibleLibraryID="/oracle-samples/netsuite-suitecloud-samples",
  topic="SuiteScript examples",
  tokens=8000
)

// Get Oracle NetSuite documentation
mcp__context7__get-library-docs(
  context7CompatibleLibraryID="/websites/oracle_en_cloud_saas_netsuite",
  topic="your topic",
  tokens=10000
)
```

## Common Workflows

### Starting New Script Development

1. Check script type in suitescript-modules.md
2. Review module usage in suitescript-modules.md
3. Reference examples in open-source-projects.md
4. Check authentication if needed in authentication.md
5. Review deployment in suitecloud-sdk-framework.md

### Setting Up Integration

1. Decide integration type (RESTlet, SuiteTalk, SDK)
2. RESTlet: Read restlets.md
3. SuiteTalk: Read suitetalk-rest-api.md
4. SDK: Read third-party-sdks.md
5. Authentication: Read authentication.md

### Deploying Customizations

1. Read suitecloud-sdk-framework.md - Project Structure
2. Read suitecloud-sdk-framework.md - CLI Commands
3. Setup authentication from authentication.md
4. Follow deployment workflow in suitecloud-sdk-framework.md
5. Setup CI/CD from suitecloud-sdk-framework.md - CI/CD section

### Troubleshooting Issues

1. Check error type
2. Script errors: suitescript-modules.md - Error Handling
3. Deployment errors: suitecloud-sdk-framework.md - Troubleshooting
4. Authentication errors: authentication.md
5. API errors: suitetalk-rest-api.md or restlets.md

## Updates and Maintenance

### KB File Locations
All files in: `/opt/ns/kb/`

### Reading KB Files
```bash
# Use Read tool to access KB files
Read file_path="/opt/ns/kb/suitescript-modules.md"

# Or use bash
cat /opt/ns/kb/suitescript-modules.md
```

### KB File Sizes
- suitescript-modules.md: ~12KB
- suitecloud-sdk-framework.md: ~28KB (1008 lines)
- authentication.md: ~8KB
- restlets.md: ~7KB
- suitetalk-rest-api.md: ~5.5KB
- third-party-sdks.md: ~8KB
- open-source-projects.md: ~7KB

**Total KB Size**: ~75KB

## Integration with Skill Files

This skill's documentation complements the KB:

| Skill File | KB Complement | Relationship |
|------------|---------------|--------------|
| suitescript/user-events.md | suitescript-modules.md | Specific patterns + General reference |
| suitescript/restlets.md | restlets.md | Implementation details + Overview |
| deployment/sdf-workflow.md | suitecloud-sdk-framework.md | Workflow + Complete reference |
| deployment/cli-commands.md | suitecloud-sdk-framework.md | Command details + Architecture |

**Usage Pattern:**
1. Start with skill files for specific task
2. Reference KB for comprehensive information
3. Use Archon/Context7 for external documentation
4. Combine all sources for complete understanding
