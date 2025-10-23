# NetSuite Operations

![NS Banner](assets/banner.png)

This repository hosts software components, integrations, and documentation for NetSuite implementations at PDI Technologies. The contents support operational workflows across multiple business functions by providing standardized interfaces, reusable modules, and technical reference materials.

## Purpose

NetSuite serves as a critical ERP system within PDI's technology infrastructure. This repository consolidates resources that extend NetSuite's capabilities, streamline integration patterns, and document best practices for development teams working with the platform.

## Structure

The repository organizes resources into distinct categories:

### Knowledge Base

Technical documentation covering NetSuite development patterns and integration approaches:

- **Authentication** - OAuth 2.0, token-based authentication, and credential management for SuiteTalk and RESTlet endpoints
- **RESTlets** - Custom REST endpoint development using SuiteScript 2.x
- **SuiteScript Modules** - Reference documentation for N/https, N/record, N/search, and other core modules
- **SuiteTalk REST API** - Standard REST web services for record operations and metadata queries
- **SuiteCloud SDK Framework** - CLI tools, project structure, and deployment workflows
- **Third-Party SDKs** - Integration libraries for Node.js, Python, and other platforms
- **Open Source Projects** - Community tools and frameworks for NetSuite development

<div align="center">
  <img src="assets/architecture.png" alt="System Architecture" width="400"/>
</div>

## Repository Contents

All documentation resides in the `kb/` directory as markdown files. Each document provides specific technical details, code examples, and references to Oracle's official NetSuite documentation.

The `.claude/` directory contains development workflow configurations and is excluded from production deployments.

## Usage

Clone this repository to access reference materials during NetSuite development work:

```bash
git clone https://github.com/PDI-Technologies/ns.git
cd ns
```

Documentation files can be viewed directly in any markdown reader or through the GitHub web interface.

## Contributing

This repository follows standard git workflows. Create feature branches for additions or updates, then submit pull requests for review before merging to main.

Maintain consistency with existing documentation structure. Include code examples where applicable and link to official Oracle NetSuite documentation for authoritative references.

## Technical Stack

- **NetSuite SuiteCloud Platform** - Primary integration target
- **SuiteScript 2.x** - Server-side JavaScript execution environment
- **SuiteTalk REST/SOAP** - Web services APIs
- **SuiteCloud SDK** - Command-line development tools

## License

Internal PDI Technologies repository. All rights reserved.
