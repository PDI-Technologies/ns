# NetSuite Skills for Claude

Comprehensive skills for NetSuite development, integration, and business automation.

## Overview

This directory contains three comprehensive skills designed to support NetSuite integration application/service/solution development for accounting, finance, and operations teams.

### Skills Architecture

Following Claude Skills best practices, we use **3 comprehensive skills** instead of many specialized ones to:
- ✅ Minimize token overhead (~300 tokens vs 1000+ tokens)
- ✅ Avoid trigger conflicts between related skills
- ✅ Keep related knowledge together
- ✅ Use progressive disclosure for specialization
- ✅ Enable efficient file-based navigation

**Token Economy:**
- **Level 1** (Always loaded): 3 skill descriptions = ~300 tokens
- **Level 2** (When triggered): Single SKILL.md = ~200-500 tokens
- **Level 3+** (On-demand): Only specific files loaded via bash = 0 tokens until needed

## Available Skills

### 1. netsuite-developer 🛠️

**Directory:** `netsuite-developer/`

**Description:** Develops and deploys NetSuite customizations using SuiteScript 2.x and SuiteCloud Development Framework (SDF).

**Coverage:**
- All SuiteScript types (User Events, Client Scripts, Scheduled, Map/Reduce, RESTlets, Suitelets, Workflow Actions, Mass Update, Portlets)
- SuiteCloud Development Framework (SDF)
- CLI commands and workflows
- Project structure and deployment
- CI/CD integration
- Testing and debugging
- Performance optimization
- Error handling patterns

**Use When:**
- Writing NetSuite scripts
- Deploying customizations
- Setting up development workflows
- Configuring CI/CD pipelines
- Debugging issues
- Optimizing performance

**File Count:** 42 files

**Key Files:**
- [SKILL.md](netsuite-developer/SKILL.md) - Main navigation hub
- [suitescript/user-events.md](netsuite-developer/suitescript/user-events.md) - User Event patterns
- [deployment/sdf-workflow.md](netsuite-developer/deployment/sdf-workflow.md) - Complete SDF workflow
- [kb-reference.md](netsuite-developer/kb-reference.md) - Local KB index

---

### 2. netsuite-integrations 🔗

**Directory:** `netsuite-integrations/`

**Description:** Builds integrations between NetSuite and external systems including Salesforce, databases, and third-party services.

**Coverage:**
- RESTlet API development
- Salesforce integration (via MCP tools)
- Database integration (MSSQL, PostgreSQL, MySQL via MCP)
- SuiteTalk REST/SOAP APIs
- External API calls (N/https)
- Webhook handlers
- Authentication (OAuth 2.0, TBA, API keys)
- Error handling and retry patterns

**Use When:**
- Connecting NetSuite to CRM systems
- Integrating with databases
- Building REST APIs
- Calling external services
- Setting up webhooks
- Implementing bi-directional sync

**File Count:** 38 files

**Key Files:**
- [SKILL.md](netsuite-integrations/SKILL.md) - Main navigation hub
- [salesforce/mcp-tools.md](netsuite-integrations/salesforce/mcp-tools.md) - Salesforce MCP reference
- [restlet-apis/api-design.md](netsuite-integrations/restlet-apis/api-design.md) - API design patterns
- [databases/mcp-tools.md](netsuite-integrations/databases/mcp-tools.md) - Database MCP reference

---

### 3. netsuite-business-automation 📊

**Directory:** `netsuite-business-automation/`

**Description:** Automates accounting, finance, and operations workflows in NetSuite.

**Coverage:**
- Finance automation (journal entries, reconciliation, period close)
- Order-to-Cash (sales orders, fulfillment, invoicing, payments)
- Procure-to-Pay (requisitions, POs, vendor bills, expense reports)
- Revenue recognition
- Workflow automation
- Custom record design
- Approval routing

**Use When:**
- Building finance team automations
- Automating sales operations
- Implementing procurement processes
- Creating approval workflows
- Designing custom records
- Implementing revenue recognition

**File Count:** 34 files

**Key Files:**
- [SKILL.md](netsuite-business-automation/SKILL.md) - Main navigation hub
- [finance/journal-entries.md](netsuite-business-automation/finance/journal-entries.md) - JE automation
- [order-to-cash/sales-orders.md](netsuite-business-automation/order-to-cash/sales-orders.md) - O2C automation
- [procure-to-pay/requisitions-pos.md](netsuite-business-automation/procure-to-pay/requisitions-pos.md) - P2P automation

---

## Skills Statistics

| Skill | Files | Directories | Size | Token Overhead |
|-------|-------|-------------|------|----------------|
| netsuite-developer | 42 | 7 | ~150KB | ~100 tokens |
| netsuite-integrations | 38 | 7 | ~120KB | ~100 tokens |
| netsuite-business-automation | 34 | 6 | ~100KB | ~100 tokens |
| **Total** | **114** | **20** | **~370KB** | **~300 tokens** |

## File Organization Pattern

Each skill follows this structure:

```
skill-name/
├── SKILL.md                    # Main navigation hub (always loaded when triggered)
├── category-1/                 # Logical grouping
│   ├── topic-a.md             # Loaded on-demand via bash
│   ├── topic-b.md             # Only when Claude navigates to it
│   └── topic-c.md             # Zero tokens until accessed
├── category-2/
│   └── ...
├── examples/                   # Code examples
│   └── example-1.md
└── templates/                  # Reusable templates (if applicable)
    └── template.js
```

**Progressive Disclosure in Action:**

1. User asks: "How do I create a User Event script?"
2. Claude sees skill description (Level 1: 100 tokens)
3. Claude loads `netsuite-developer/SKILL.md` (Level 2: ~400 tokens)
4. SKILL.md references `suitescript/user-events.md`
5. Claude reads ONLY that file via bash (Level 3: ~2000 tokens)
6. **Other 41 files remain unloaded** (0 tokens)

**Total Context Used:** ~2500 tokens instead of loading everything at once

## Local Knowledge Base Integration

All skills reference the local KB in `/opt/ns/kb/`:

### KB Files Referenced

| KB File | Size | Skills Using It | Purpose |
|---------|------|-----------------|---------|
| suitescript-modules.md | 12KB | developer, integrations | Module reference |
| suitecloud-sdk-framework.md | 28KB | developer | SDF complete guide |
| authentication.md | 8KB | all | Auth methods |
| restlets.md | 7KB | developer, integrations | RESTlet guide |
| suitetalk-rest-api.md | 5.5KB | integrations | SuiteTalk reference |
| third-party-sdks.md | 8KB | integrations | SDK catalog |
| open-source-projects.md | 7KB | developer | GitHub projects |

### KB Access Pattern

Skills reference KB files for comprehensive information:

```javascript
// In skill documentation:
// "For detailed module documentation, see /opt/ns/kb/suitescript-modules.md"

// Claude uses Read tool:
Read file_path="/opt/ns/kb/suitescript-modules.md"

// Result: Zero tokens until explicitly loaded
```

## MCP Tool Integration

Skills leverage available MCP servers:

### Archon MCP (Vector KB)
```javascript
// Search NetSuite documentation
mcp__archon__rag_search_knowledge_base(
  query="User Event beforeSubmit pattern",
  source_id="netsuite",
  match_count=5
)

// Search code examples
mcp__archon__rag_search_code_examples(
  query="N/record load update",
  source_id="netsuite",
  match_count=3
)
```

### Salesforce MCP
```javascript
// Query Salesforce
mcp__pdi-salesforce-sse3__query(
  soql="SELECT Id, Name FROM Account WHERE Industry = 'Technology'",
  pageSize=20
)

// Create Salesforce record
mcp__pdi-salesforce-sse3__create(
  sObjectType="Contact",
  record={FirstName: "Jane", LastName: "Smith"}
)
```

### Database MCP
```javascript
// Query database
mcp__mssql__query(
  query="SELECT * FROM customers WHERE modified_date > @date",
  host="db.server.com",
  database="analytics",
  dbType="mssql"
)
```

### Context7 MCP
```javascript
// Get NetSuite documentation
mcp__context7__get-library-docs(
  context7CompatibleLibraryID="/oracle-samples/netsuite-suitecloud-samples",
  topic="SuiteScript examples",
  tokens=8000
)
```

## Development Workflow

### Using the Skills

1. **Ask Claude for Help:**
   ```
   "I need to create a User Event script that validates sales orders"
   ```

2. **Claude Triggers Skill:**
   - Recognizes "User Event script" keywords
   - Loads `netsuite-developer` skill
   - Reads `SKILL.md` for navigation

3. **Progressive Navigation:**
   - `SKILL.md` points to `suitescript/user-events.md`
   - Claude reads only that specific file
   - Provides targeted information

4. **Multiple Resources:**
   - May also reference `/opt/ns/kb/suitescript-modules.md`
   - May search Archon for code examples
   - Combines all sources for comprehensive answer

### Extending the Skills

To add new content:

1. **Identify the Right Skill:**
   - Development/deployment → `netsuite-developer`
   - Integration → `netsuite-integrations`
   - Business process → `netsuite-business-automation`

2. **Find the Right Category:**
   - Look at existing subdirectories
   - Add to appropriate category

3. **Create the File:**
   - Use placeholder template from `generate-skill-files.sh`
   - Follow existing file patterns
   - Add comprehensive examples

4. **Update SKILL.md:**
   - Add reference to new file in appropriate section
   - Update file index at bottom
   - Provide navigation path

5. **Test:**
   - Ask Claude questions that should trigger your new content
   - Verify navigation works correctly
   - Ensure information is accurate

## Maintenance

### Regenerating Placeholder Files

If you need to recreate placeholder files:

```bash
cd /opt/ns/.claude/skills
./generate-skill-files.sh
```

**Note:** Existing files will not be overwritten.

### Updating KB References

When KB files change:

1. Update references in relevant SKILL.md files
2. Update `netsuite-developer/kb-reference.md`
3. Test that links still work

### Adding New Skills

If you need a fourth skill (not recommended unless necessary):

1. Create directory: `.claude/skills/new-skill/`
2. Add `SKILL.md` with proper frontmatter
3. Follow the three-tier structure
4. Update this README
5. **Consider:** Can this be merged into existing skills?

## Best Practices

### DO's ✅

- Keep SKILL.md files under 500 lines
- Use progressive disclosure (file references)
- Reference KB files for comprehensive info
- Include MCP tool examples
- Add code examples in documentation
- Use clear navigation paths
- Test with real user questions

### DON'Ts ❌

- Don't create specialized micro-skills
- Don't duplicate content across skills
- Don't exceed 1024 chars in descriptions
- Don't nest file references > 1 level
- Don't forget to update file indexes
- Don't skip SKILL.md navigation updates

## Testing

### Test Skill Loading

Ask Claude:

```
"List all available skills"
```

**Expected:** All three skills should appear.

### Test Progressive Disclosure

Ask Claude:

```
"Show me an example of a User Event script"
```

**Expected:** Claude should:
1. Load `netsuite-developer` skill
2. Navigate to `suitescript/user-events.md`
3. Provide code example
4. **NOT load** other unrelated files

### Test KB Integration

Ask Claude:

```
"What modules are available in SuiteScript 2.x?"
```

**Expected:** Claude should reference `/opt/ns/kb/suitescript-modules.md`

### Test MCP Integration

Ask Claude:

```
"How do I query Salesforce from NetSuite?"
```

**Expected:** Claude should:
1. Load `netsuite-integrations` skill
2. Reference Salesforce MCP tools
3. Show MCP tool usage examples

## Troubleshooting

### Skill Not Loading

**Symptom:** Claude doesn't use the skill

**Checks:**
1. Verify SKILL.md exists in correct location
2. Check YAML frontmatter syntax (three dashes)
3. Verify description includes trigger keywords
4. Confirm description is under 1024 characters

**Fix:**
```bash
# Validate YAML
cat /opt/ns/.claude/skills/netsuite-developer/SKILL.md | head -n 5

# Should show:
# ---
# name: netsuite-developer
# description: [description text]
# ---
```

### Wrong Skill Triggered

**Symptom:** Claude loads wrong skill for request

**Cause:** Overlapping descriptions

**Fix:** Make descriptions more specific with "Use when..." clauses

### File Not Found

**Symptom:** Claude can't find referenced file

**Checks:**
1. Verify file exists: `ls /opt/ns/.claude/skills/skill-name/path/to/file.md`
2. Check file path in SKILL.md matches actual location
3. Verify forward slashes in paths

**Fix:** Update SKILL.md references or create missing file

### Too Many Tokens

**Symptom:** Context window filling up

**Cause:** Files too large or too many files loaded

**Fix:**
1. Split large files (>500 lines) into smaller files
2. Review what files are being loaded
3. Improve navigation to load only necessary files

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-23 | Initial release with 3 comprehensive skills |

## Contributing

To contribute to these skills:

1. Follow existing patterns
2. Test thoroughly before committing
3. Update this README for structural changes
4. Document MCP tool usage
5. Provide working code examples

## Support

For issues or questions:

1. Check existing documentation in SKILL.md files
2. Review this README
3. Check KB files in `/opt/ns/kb/`
4. Search Archon vector KB for NetSuite documentation

## License

Internal use for NetSuite development team.

## Related Resources

- **Local KB:** `/opt/ns/kb/`
- **Official NetSuite Docs:** https://developers.netsuite.com/
- **SuiteCloud SDK Docs:** https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_1558708800.html
- **Claude Skills Docs:** https://docs.claude.com/en/docs/agents-and-tools/agent-skills/

---

**Last Updated:** October 23, 2025
**Total Files:** 114 markdown files + 7 JavaScript templates
**Total Skills:** 3 comprehensive skills
**Context Overhead:** ~300 tokens (always loaded)
