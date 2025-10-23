# Salesforce MCP Distilled Skill

## Overview

This is a **model-optimized version** of the salesforce-mcp skill, designed for efficient parsing and internalization by Claude models.

## Metrics

| Metric | Original | Distilled | Improvement |
|--------|----------|-----------|-------------|
| **Lines** | 884 | 305 | 65% reduction |
| **Target** | N/A | <500 | ✅ Achieved |
| **Focus** | Human + Model | Model-only | Optimized |

## What Was Removed

### Content Eliminated (579 lines)
- ✂️ Testing evidence sections (Phase 7)
- ✂️ Agent journey narratives
- ✂️ "Why this works" explanations
- ✂️ Performance metrics discussions
- ✂️ Success stories and examples
- ✂️ Workflow motivations
- ✂️ Redundant examples
- ✂️ Historical context
- ✂️ Verbose introductions
- ✂️ Multi-example demonstrations

### Structure Changes
- ❌ Removed: Narrative prose
- ✅ Added: Dense tables
- ❌ Removed: Explanatory sections
- ✅ Added: Direct patterns
- ❌ Removed: "Evidence-based" discussions
- ✅ Added: Anti-pattern lists

## What Was Kept

### Essential Content (100% coverage)
- ✅ Critical rules (NEVER use describe*)
- ✅ Optimal workflow (search → retrieve → query)
- ✅ Object quick reference (ChangeRequest, Case, Account)
- ✅ Tool selection matrix
- ✅ Query patterns (all SOQL templates)
- ✅ Relationship query rules
- ✅ Aggregation syntax
- ✅ Schema discovery alternatives
- ✅ Data manipulation patterns
- ✅ Anti-patterns list
- ✅ Field naming conventions
- ✅ Defensive LIMIT guidelines

### New Additions (from research)
1. **Aggregation ORDER BY rule** - Cannot use aliases
2. **FieldDefinition workaround** - Pattern-based when IsCustom unavailable
3. **Defensive LIMIT pattern** - Systematic guidance
4. **Account hierarchy discovery** - 3-step validation
5. **Multi-field validation** - Single query pattern

## Design Principles Applied

### From Claude Best Practices
1. **Concise** - Under 500 lines (305 actual)
2. **Assume intelligence** - No explanations of basics
3. **Direct instructions** - Imperative mood
4. **Progressive disclosure** - Could split further if needed
5. **Third person** - Description in frontmatter

### Model Optimization
- **Front-loaded critical rules** - NEVER use tools first
- **Tables over prose** - Quick scanning
- **Bullets over paragraphs** - Dense information
- **Code examples only** - No narrative wrappers
- **Anti-patterns explicit** - ❌ symbols for clarity

## When to Use Which Version

### Original (`salesforce-mcp/SKILL.md`)
- **Use for:** Human reference, training new team members
- **Contains:** Evidence, reasoning, testing narratives
- **Best for:** Understanding why patterns work

### Distilled (`salesforce-mcp-distilled/SKILL.md`)
- **Use for:** Model consumption, sub-agent tasks
- **Contains:** Pure patterns, rules, syntax
- **Best for:** Fast parsing, direct application

## File Structure

```
.claude/skills/
├── salesforce-mcp/
│   └── SKILL.md (884 lines - human + model)
└── salesforce-mcp-distilled/
    ├── SKILL.md (305 lines - model-optimized)
    └── README.md (this file)
```

## Future Optimization

If skill exceeds 500 lines, can split into:
- `SKILL.md` - Core patterns (keep under 300 lines)
- `REFERENCE.md` - Extended examples
- `OBJECTS.md` - Detailed object schemas

Current size (305 lines) requires no splitting.

## Testing Recommendations

Test distilled version with:
1. Claude Haiku (smallest model)
2. Complex multi-step Salesforce queries
3. Edge cases from testing docs
4. Verify all patterns accessible

Compare performance:
- Tokens consumed
- Query success rate
- Discovery overhead
- Response accuracy

## Maintenance

When updating:
1. Add new patterns to **both** versions
2. Original: Include reasoning/evidence
3. Distilled: Pattern only, no explanation
4. Keep distilled under 500 lines
5. Update this README with changes
