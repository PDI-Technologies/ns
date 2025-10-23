---
name: react-pwa-designer
description: Build production-ready React progressive web applications with modern UI design. Use for React apps, PWA features, shadcn/ui components, or responsive web interfaces. Combines SuperDesign methodology with React best practices, shadcn MCP integration, and progressive web app development.
---

# React PWA Designer

A comprehensive skill for designing and building modern React progressive web applications using SuperDesign methodology, shadcn/ui components, and React best practices.

## When to Use This Skill

Trigger this skill when the user requests:
- Designing or building React applications
- Creating progressive web apps (PWAs)
- Implementing shadcn/ui components
- Building modern, responsive web interfaces
- Creating React component libraries
- Designing with Tailwind CSS and modern design systems
- Converting designs to React components

## Core Workflow

### Phase 1: Discovery & Planning

1. **Understand Requirements**
   - Clarify app purpose and target users
   - Identify key features and functionality
   - Determine PWA requirements (offline, installable, notifications)
   - Check if existing design system or brand guidelines exist

2. **Component Discovery**
   - Use `mcp__shadcn__getComponents()` to list available shadcn components
   - Use `mcp__shadcn__getComponent(component: "component-name")` for specific component details
   - Identify which components best match requirements

3. **Architecture Planning**
   - Define React component hierarchy
   - Plan state management approach (Context, Zustand, etc.)
   - Identify routing needs (React Router)
   - Plan data fetching strategy (React Query, SWR, etc.)

### Session Scoping Best Practices

**Critical for reviewable diffs and effective checkpoints:**

- ✅ **Limit to 15-20 files maximum per session**
- ✅ **Focus on single feature or component per iteration**
- ✅ **Complete cycle**: Implementation → Tests → Commit before next scope

**Good scoping examples:**
- "Create Button component with 3 variants" (~5 files)
- "Add form validation to LoginForm component" (~3 files)
- "Implement offline caching for user profile API" (~4 files)
- "Generate and validate PWA icons" (~2-3 files + verification)

**Avoid over-scoping:**
- ❌ "Build entire authentication system" (too broad - 30+ files)
- ❌ "Add all shadcn components to project" (too many files)
- ❌ "Implement complete PWA from scratch" (break into phases)

**Why this matters:**
- Human-reviewable diffs (Anthropic best practice: <20 files)
- Clear rollback points if issues occur
- Matches checkpoint mechanism capacity
- Prevents accumulation of unreviewable changes

### Phase 2: Design (SuperDesign Methodology)

**Reference**: See [SuperDesign.md](SuperDesign.md) for complete methodology details.

#### Step 1: Layout Design (ASCII Wireframes)
- Present component structure using ASCII art
- Show responsive breakpoints
- Indicate component composition
- **Get user approval before proceeding**

**Example Layout Format**:
```
┌─────────────────────────────────────────┐
│  Header (shadcn: NavigationMenu)        │
├─────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────────────────────┐ │
│ │ Sidebar │ │   Main Content          │ │
│ │ (Sheet) │ │   (Card components)     │ │
│ │         │ │                         │ │
│ │  Nav    │ │   ┌─────────────────┐   │ │
│ │  Links  │ │   │  Form (Input,   │   │ │
│ │         │ │   │  Button, Label) │   │ │
│ │         │ │   └─────────────────┘   │ │
│ └─────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────┤
│  Footer (Responsive grid)               │
└─────────────────────────────────────────┘

Mobile (< 768px):
┌─────────────────┐
│ Header + Burger │
├─────────────────┤
│                 │
│  Main Content   │
│  (Stacked)      │
│                 │
├─────────────────┤
│     Footer      │
└─────────────────┘
```

#### Step 2: Theme Design (Tool-Based)
- **MUST use tool calls** for theme generation (never text output!)
- Save CSS to `.superdesign/design_iterations/theme_[n].css`
- Consider shadcn theming with CSS variables
- Define color palette using oklch format
- Set typography using approved Google Fonts
- **Get user approval before proceeding**

**shadcn Theme Integration**:
- shadcn uses CSS variables: `--background`, `--foreground`, `--primary`, etc.
- Ensure theme is compatible with shadcn component styling
- Include dark mode variants if needed

#### Step 3: Animation Design (Micro-Syntax)
- Define component transitions
- Specify interaction states
- Plan loading and error states
- Consider accessibility (prefers-reduced-motion)
- **Get user approval before proceeding**

**Example Animation Spec**:
```
# REACT PWA ANIMATIONS

## Component Transitions
modalOpen: 300ms ease-out [Y+20→0, α0→1, blur(8px)→0]
cardHover: 200ms ease-out [Y0→-4, shadow↗]
buttonPress: 150ms [S1→0.98→1]

## Page Transitions (React Router)
pageEnter: 400ms ease-out [X+30→0, α0→1]
pageExit: 300ms ease-in [X0→-30, α1→0]

## Loading States
skeleton: 2000ms ∞ [bg: muted↔accent]
spinnerRotate: 1000ms ∞ linear [R360°]

## Micro-interactions
formFocus: 200ms [ring-2, ring-primary]
successPulse: 600ms [S1→1.1→1, bg→success]
```

#### Step 4: Component Implementation

**Create React components using shadcn/ui**:

1. **Install shadcn components** (document commands, don't run):
   ```bash
   npx shadcn@latest init
   npx shadcn@latest add [component-name]
   ```

2. **Component structure**:
   - Use shadcn components as building blocks
   - Compose custom components from shadcn primitives
   - Follow React best practices (hooks, composition)
   - Implement proper TypeScript types

3. **File organization**:
   ```
   src/
   ├── components/
   │   ├── ui/              # shadcn components
   │   ├── features/        # Feature components
   │   └── layouts/         # Layout components
   ├── hooks/               # Custom hooks
   ├── lib/
   │   └── utils.ts         # Utilities (cn, etc.)
   ├── styles/
   │   └── globals.css      # Theme CSS
   └── App.tsx
   ```

### Phase 3: Progressive Web App (PWA) Implementation

#### 1. PWA Icons (CRITICAL - Read First!)

**⚠️ BEFORE generating icons:**
→ **MUST READ**: `reference/pwa-icon-validation.md`

**Why:** Icon dimension mismatches are the #1 cause of PWA installation failure. This file contains:
- Exact icon size requirements (192x192, 512x512, 180x180)
- Verification commands to catch errors before deployment
- Common mistakes and how to avoid them

**Key takeaway:** Icon file dimensions MUST match manifest declarations exactly, or installation will fail with no error message.

#### 2. PWA Manifest

Create `public/manifest.json`:
```json
{
  "name": "App Name",
  "short_name": "App",
  "description": "App description",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#ffffff",
  "background_color": "#ffffff",
  "prefer_related_applications": false,
  "icons": [
    {
      "src": "/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/apple-touch-icon.png",
      "sizes": "180x180",
      "type": "image/png"
    }
  ]
}
```

#### 3. Service Worker Strategy

**Option A: Vite PWA Plugin** (Recommended for most projects):
- Automatic service worker generation
- Workbox integration
- Simple configuration

**Option B: Manual Implementation** (For advanced control):
→ **Reference**: `templates/service-worker.ts`

**When to read service-worker.ts:**
- Need custom caching strategies
- Want full control over cache management
- Implementing advanced offline features

Manual implementation includes:
- TypeScript types
- Stale-while-revalidate strategy
- Offline fallback support
- Automatic cache cleanup

#### 4. PWA Features Checklist

- ✅ Responsive design (mobile-first)
- ✅ HTTPS deployment
- ✅ Service worker registered
- ✅ Web manifest with icons (verified with `file` command!)
- ✅ Offline functionality
- ✅ Install prompt handling
- ✅ Fast load times (<3s)
- ✅ Accessible (WCAG AA)

### Phase 4: Development Best Practices

#### React Patterns
- **Use hooks properly**: useState, useEffect, useMemo, useCallback
- **Composition over inheritance**: Build complex UIs from simple components
- **Prop drilling solution**: Context API or state management library
- **Error boundaries**: Catch and handle component errors
- **Suspense & lazy loading**: Code splitting for performance

#### State Management

**→ See `reference/state-management-patterns.md`** for complete decision trees and implementation patterns

#### TypeScript

**→ See `reference/code-quality-tooling.md`** for TypeScript best practices, type patterns, and ESLint/Prettier configuration

#### Performance Optimization
- Use React.memo for expensive components
- Implement virtualization for long lists (react-virtual)
- Optimize images (WebP, lazy loading)
- Code split routes and heavy components
- Monitor bundle size (Vite bundle analyzer)

## Supporting Files

This skill includes progressive disclosure resources loaded only when needed:

### Reference Files (`reference/`)
- **shadcn-components.md** - Quick component reference (use BEFORE MCP calls)
- **react-hooks.md** - Common React hooks patterns
- **code-quality-tooling.md** - ESLint, TypeScript, Prettier configuration and type hygiene
- **state-management-patterns.md** - Choosing between useState, Context, Zustand, React Query
- **dynamic-styling-patterns.md** - State-driven styling decisions (CSS Variables, Tailwind, inline styles)
- **layout-patterns.md** - Flex scrolling, grid placement, conditional transitions, text overflow
- **implementation-examples.md** - Complete code examples (Dashboard, Auth Flow)
- **component-patterns.md** - Feature-First structure, shadcn extensions, data fetching, compound components
- **setup-guide.md** - Dependencies, installation, configuration
- **pwa-checklist.md** - Detailed PWA requirements
- **accessibility.md** - WCAG AA patterns and examples
- **common-pitfalls.md** - Anti-patterns to avoid

### Templates (`templates/`)
- **component-boilerplate.tsx** - React component template
- **custom-hook-template.ts** - Custom hook structure
- **manifest.json** - PWA manifest boilerplate
- **vite.config.ts** - Vite + PWA configuration
- **tailwind.config.js** - Tailwind + shadcn config
- **tsconfig.json** - TypeScript configuration

## Tool Usage Guide

### When to Use shadcn MCP Tools

**Use `mcp__shadcn__getComponents()`**:
- At the start of a project to see available components
- When user asks "what components are available?"
- To remind yourself of component names

**Use `mcp__shadcn__getComponent(component: "name")`**:
- To get implementation details for a specific component
- To see component variants and props
- To understand component dependencies
- Before implementing or customizing a component

**Example workflow**:
```
User: "I need a modal dialog with a form"

1. Call: mcp__shadcn__getComponents()
   → Find: "dialog", "form", "input", "button", "label"

2. Call: mcp__shadcn__getComponent(component: "dialog")
   → Get implementation details

3. Call: mcp__shadcn__getComponent(component: "form")
   → Get form implementation

4. Combine into custom component
```

### External Knowledge Sources (Optional)

**Use this knowledge cascade when reference files don't have the answer:**

```
1. Archon RAG      → Internal org knowledge (if available)
2. Context7        → Official library documentation
3. Perplexity MCP  → Latest web knowledge & trends
```

---

#### 1. Archon RAG (Priority 1: Internal Knowledge)

**Use FIRST if your organization has internal PWA/React documentation in Archon.**

**Search for internal patterns and standards**:
```typescript
// Search general documentation
mcp__archon__rag_search_knowledge_base({
  query: "PWA service worker",
  match_count: 3
})

// Search code examples
mcp__archon__rag_search_code_examples({
  query: "React offline hooks",
  match_count: 3
})
```

**Targeted search for specific internal docs**:
```typescript
// 1. Get available sources
mcp__archon__rag_get_available_sources()

// 2. Find relevant source
// Returns: { id: "src_abc123", title: "Company PWA Standards" }

// 3. Search that specific source
mcp__archon__rag_search_knowledge_base({
  query: "icon validation",
  source_id: "src_abc123",
  match_count: 5
})
```

**When to use Archon**:
- ✅ Organization has PWA implementation standards
- ✅ Internal React component library exists
- ✅ Company-specific security/compliance patterns
- ✅ Team has accumulated PWA best practices

---

#### 2. Context7 (Priority 2: Official Library Docs)

**Use for authoritative, up-to-date library documentation.**

**Resolve library name to Context7 ID**:
```typescript
// ALWAYS call this first to get the library ID
mcp__context7__resolve_library_id({
  libraryName: "react"
})
// Returns Context7-compatible ID: "/facebook/react"

mcp__context7__resolve_library_id({
  libraryName: "vite-plugin-pwa"
})
// Returns: "/vite-pwa/vite-plugin-pwa"
```

**Get library documentation**:
```typescript
// Use the ID from resolve-library-id
mcp__context7__get_library_docs({
  context7CompatibleLibraryID: "/facebook/react",
  topic: "hooks",           // Optional: focus on specific topic
  tokens: 5000              // Optional: control doc size
})

// PWA-specific libraries
mcp__context7__get_library_docs({
  context7CompatibleLibraryID: "/vite-pwa/vite-plugin-pwa",
  topic: "offline",
  tokens: 5000
})

// Workbox for service workers
mcp__context7__get_library_docs({
  context7CompatibleLibraryID: "/GoogleChrome/workbox",
  topic: "caching strategies",
  tokens: 5000
})
```

**When to use Context7**:
- ✅ Need official React documentation (hooks, APIs, patterns)
- ✅ PWA library documentation (Vite PWA plugin, Workbox)
- ✅ Latest API changes or new features
- ✅ Authoritative implementation examples
- ✅ Version-specific documentation (e.g., `/vercel/next.js/v14.3.0`)

**Common libraries for React PWA projects**:
- `/facebook/react` - React core
- `/vite-pwa/vite-plugin-pwa` - Vite PWA plugin
- `/GoogleChrome/workbox` - Service worker library
- `/tanstack/react-query` - Data fetching
- `/pmndrs/zustand` - State management
- `/shadcn/ui` - Component library

---

#### 3. Perplexity MCP (Priority 3: Latest Web Knowledge)

**Use for current trends, recent changes, or when other sources don't have the answer.**

**Simple queries** (cheap & fast):
```typescript
mcp__perplexity__ask_perplexity({
  query: "What's the latest PWA best practice for iOS in 2025?",
  query_type: "simple",
  attachment_paths: []
})

mcp__perplexity__ask_perplexity({
  query: "React 19 PWA compatibility issues",
  query_type: "simple",
  attachment_paths: []
})
```

**Complex queries** (deep analysis):
```typescript
mcp__perplexity__ask_perplexity({
  query: "Analyze current state of PWA support across browsers in 2025 and recommend implementation strategy for maximum compatibility",
  query_type: "complex",
  attachment_paths: []
})

// With code context
mcp__perplexity__ask_perplexity({
  query: "Review this service worker implementation and suggest 2025 best practices for caching strategy",
  query_type: "complex",
  attachment_paths: ["/absolute/path/to/sw.ts"]  // Must be absolute path
})
```

**When to use Perplexity**:
- ✅ Need latest 2025 PWA trends or browser changes
- ✅ Cross-browser compatibility questions
- ✅ Recent library releases or deprecations
- ✅ Emerging patterns not yet in documentation
- ✅ Troubleshooting new/uncommon issues

**Query types**:
- `simple` - Straightforward questions (10x cheaper, 3x faster)
- `complex` - Multi-step reasoning, deep analysis (slower, more expensive)

---

#### Knowledge Source Decision Tree

```
Question: Need PWA implementation guidance
│
├─ Internal org patterns? → Use Archon RAG
│
├─ Official library docs? → Use Context7
│  └─ React, Vite PWA, Workbox, etc.
│
├─ Latest trends/changes? → Use Perplexity MCP
│  └─ Browser updates, new standards
│
└─ General best practice? → Check reference files FIRST
   └─ pwa-checklist.md, pwa-icon-validation.md, etc.
```

---

#### Query Best Practices (All Sources)

**Keep queries SHORT and FOCUSED (2-5 keywords for Archon):**

```typescript
// ✅ GOOD - Concise, specific
{ query: "PWA offline caching", match_count: 3 }
{ query: "React service worker", match_count: 3 }
{ libraryName: "workbox" }  // Context7
{ query: "iOS PWA 2025 support" }  // Perplexity

// ❌ BAD - Too long, unfocused
{ query: "how to implement progressive web app with service workers and offline caching using React hooks and TypeScript with proper error handling" }
```

**From Archon documentation:**
> Vector search works best with 2-5 keywords, NOT long sentences or keyword dumps.

## MCP Tool Reference

### Available MCP Tools

**UI Components**:
| Tool | Use Case | Parameters |
|------|----------|------------|
| `mcp__shadcn__getComponents()` | List all shadcn components | None |
| `mcp__shadcn__getComponent()` | Get component implementation details | `component: "button"` |

**Knowledge Sources (Priority Order)**:
| Priority | Tool | Use Case | Parameters |
|----------|------|----------|------------|
| **1** | `mcp__archon__rag_search_knowledge_base()` | Search internal org docs | `query`, `match_count`, `source_id?` |
| **1** | `mcp__archon__rag_search_code_examples()` | Find internal code examples | `query`, `match_count`, `source_id?` |
| **1** | `mcp__archon__rag_get_available_sources()` | List available internal docs | None |
| **2** | `mcp__context7__resolve_library_id()` | Get Context7 library ID | `libraryName` |
| **2** | `mcp__context7__get_library_docs()` | Get official library docs | `context7CompatibleLibraryID`, `topic?`, `tokens?` |
| **3** | `mcp__perplexity__ask_perplexity()` | Search latest web knowledge | `query`, `query_type`, `attachment_paths` |

### When NOT to Use MCP

⚠️ **Check reference files FIRST** to save tokens:

- For common shadcn components → Check `reference/shadcn-components.md`
- For React hooks patterns → Check `reference/react-hooks.md`
- For linting/TypeScript setup → Check `reference/code-quality-tooling.md`
- For state management decisions → Check `reference/state-management-patterns.md`
- For styling decisions (CSS Variables, Tailwind, inline) → Check `reference/dynamic-styling-patterns.md`
- For PWA requirements → Check `reference/pwa-checklist.md`
- For accessibility → Check `reference/accessibility.md`
- For common mistakes → Check `reference/common-pitfalls.md`

Only use MCP tools when you need:
- Detailed implementation code not in references
- Specific variant information
- Advanced composition patterns
- Latest API changes

## Troubleshooting Guide

### PWA-Specific Issues

**IF experiencing PWA installation or functionality problems:**
→ **READ**: `reference/pwa-troubleshooting.md`

This comprehensive guide covers:

| Symptom | Section to Read |
|---------|-----------------|
| Install prompt not showing | "Install Prompt Not Appearing" (11-point checklist) |
| Service worker not registering | "Service Worker Not Registering" (4 common causes) |
| Offline mode not working | "Offline Mode Not Working" |
| Icons not displaying | "Icons Not Displaying Correctly" |
| Updates not applying | "Updates Not Applying" |
| iOS-specific problems | "iOS-Specific Issues" |

**Quick diagnostic:** Copy/paste the diagnostic script from troubleshooting guide into browser console for instant health check.

---

### React & General Issues

**For React, Tailwind, shadcn, and general troubleshooting:**
→ **READ**: `reference/pwa-troubleshooting.md`

Common issues covered:
- Tailwind classes not working
- shadcn components not styling correctly
- TypeScript errors with shadcn
- Build size optimization
- Service worker registration
- Offline mode configuration
- Icon dimension validation

## Quick Decision Trees

### Component Selection

```
Need interactive element?
├─ Button/action → <Button>
├─ Link/navigation → <Link> or <a>
├─ Input field → <Input> or <Textarea>
├─ Toggle → <Switch> or <Checkbox>
└─ Selection → <Select> or <RadioGroup>

Need layout container?
├─ Content box → <Card>
├─ Modal → <Dialog>
├─ Side panel → <Sheet>
├─ Dropdown → <DropdownMenu>
└─ Sections → <Tabs> or <Accordion>

Need feedback?
├─ Loading → <Skeleton> or <Progress>
├─ Notification → <Toast> or <Alert>
├─ Hint → <Tooltip>
└─ Confirmation → <AlertDialog>
```

### State Management Choice

```
What kind of state?
├─ Local to component → useState
├─ Shared (2-3 components) → Props or useContext
├─ Complex app state → Zustand or Jotai
├─ Server data → React Query or SWR
└─ Form state → React Hook Form + Zod
```

## File Naming & Organization

### Design Iterations
Save to `.superdesign/design_iterations/`:
- `{project-name}_layout_1.txt` - ASCII layouts
- `{project-name}_theme_1.css` - Generated themes
- `{project-name}_animations_1.md` - Animation specs
- `{project-name}_v1.tsx` - React components

### Component Files
```
ComponentName.tsx          # Main component
ComponentName.stories.tsx  # Storybook stories (optional)
ComponentName.test.tsx     # Tests
```

## Implementation Examples

**For complete code examples:**
→ **READ**: `reference/implementation-examples.md`

Includes:
- **Dashboard with Data Table** - Layout design, component discovery, full implementation with filters and pagination
- **Authentication Flow** - Login page with react-hook-form, zod validation, and React Router navigation

## Dependencies & Setup

**For installation and configuration:**
→ **READ**: `reference/setup-guide.md`

Includes:
- **Required packages** - React, Tailwind, shadcn/ui dependencies with explanations
- **Optional packages** - Forms, state management, PWA, testing libraries
- **Installation steps** - Vite setup, Tailwind config, shadcn init
- **Configuration files** - vite.config.ts, tailwind.config.js, tsconfig.json templates

## Critical Reminders

1. ✅ **ALWAYS use actual tool calls** - Never output "Called tool: ..." as text
2. ✅ **Get user approval** at each workflow step before proceeding
3. ✅ **Use tool calls for theme generation** - Never output CSS as text
4. ✅ **Save to .superdesign/design_iterations/** for all design artifacts
5. ✅ **Check shadcn MCP** for component details before implementation
6. ✅ **Follow React best practices** - hooks, TypeScript, composition
7. ✅ **Consider PWA requirements** - offline, responsive, performance
8. ✅ **Avoid bootstrap blue colors** - use modern design systems
9. ✅ **Make it responsive** - mobile-first approach
10. ✅ **Include accessibility** - ARIA labels, keyboard navigation, semantic HTML

## Accessibility Checklist

- ✅ Semantic HTML elements
- ✅ ARIA labels for interactive elements
- ✅ Keyboard navigation support (Tab, Enter, Escape)
- ✅ Focus indicators visible
- ✅ Color contrast meets WCAG AA (4.5:1 for text)
- ✅ Screen reader tested
- ✅ Reduced motion respected (@media prefers-reduced-motion)
- ✅ Form errors announced
- ✅ Alt text for images
- ✅ Proper heading hierarchy

## Performance Checklist

- ✅ Lighthouse score > 90
- ✅ First Contentful Paint < 1.8s
- ✅ Largest Contentful Paint < 2.5s
- ✅ Time to Interactive < 3.8s
- ✅ Cumulative Layout Shift < 0.1
- ✅ Bundle size monitored
- ✅ Code splitting implemented
- ✅ Images optimized (WebP, lazy loading)
- ✅ Critical CSS inlined
- ✅ Service worker caching strategy

## Component Patterns

**For common React patterns and compositional techniques:**
→ **READ**: `reference/component-patterns.md`

Includes:
- **Feature-First Component Structure** - Organizing by feature, not file type
- **shadcn + Custom Component Extension** - Adding variants to shadcn components
- **Data Fetching Hook Pattern** - React Query and SWR patterns
- **Compound Component Pattern** - Shared state between sub-components
- **Render Props Pattern** - Logic reuse with flexible rendering

---

**Remember**: This skill combines design methodology with engineering excellence. Always prioritize user experience, accessibility, and performance while maintaining clean, maintainable code.
