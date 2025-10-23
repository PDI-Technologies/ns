# Third-Party SDKs and Integration Tools

## Python

### netsuite (jacobsvante/netsuite)
- Package: https://pypi.org/project/netsuite/
- GitHub: https://github.com/jacobsvante/netsuite
- Install: `pip install netsuite`
- Features:
  - Async requests to NetSuite SuiteTalk SOAP/REST Web Services and RESTlets
  - SOAP API support via `pip install netsuite[soap_api]`
  - CLI support via `pip install netsuite[cli]`
  - Faster JSON handling via `pip install netsuite[orjson]`
  - All features via `pip install netsuite[all]`
- Status: Active
- Latest Version: v0.12.0 (March 4, 2024)

### netsuite-python
- Package: https://pypi.org/project/netsuite-python/
- Install: `pip install netsuite-python`
- Features:
  - CLI utilities for NetSuite authorization setup
  - Simplifies NetSuite authorization without frontend client
- Status: Active (recent documentation updates)

### netsuite-sdk-py (fylein/netsuite-sdk-py)
- Package: https://pypi.org/project/netsuite-sdk-py/
- GitHub: https://github.com/fylein/netsuite-sdk-py
- Install: `pip install netsuite-sdk-py`
- Features:
  - SOAP client using Zeep library
  - Access to NetSuite resources via SOAP API
- Status: Active

### gs-netsuite-api
- Package: https://pypi.org/project/gs-netsuite-api/
- Install: `pip install gs-netsuite-api`
- Features:
  - NetSuite API integration
- Status: Active (versions 1.4.0, 1.4.1, 1.4.2 published Sept-Oct 2024)

### suitepy (kslater3/suitepy)
- GitHub: https://github.com/kslater3/suitepy
- Install: Available via GitHub
- Features:
  - Python library for NetSuite REST API
- Status: Active

### python-netsuite
- Package: https://pypi.org/project/python-netsuite/
- Install: `pip install python-netsuite`
- Features:
  - Legacy NetSuite Python SDK
- Status: **Archived** (Last updated 2016)

## Node.js

### @oracle/suitecloud-cli
- Package: https://www.npmjs.com/package/@oracle/suitecloud-cli
- GitHub: Oracle NetSuite official repository
- Install: `npm install -g @oracle/suitecloud-cli`
- Install (CI, skip license prompt): `npm install -g --acceptSuiteCloudSDKLicense @oracle/suitecloud-cli`
- Features:
  - Official Oracle NetSuite SuiteCloud CLI
  - Account setup and management
  - File and object management
  - Project validation and deployment
  - Interactive development tool for local/NetSuite communication
- Requirements: Node.js v22 LTS, Oracle JDK 17 or 21
- Status: Active
- Latest Version: v3.0.1 (compatible with NetSuite 2025.1, 2025.2)

### netsuite-restlet-api (nearform/netsuite-restlet-api)
- Package: https://www.npmjs.com/package/netsuite-restlet-api
- GitHub: https://github.com/nearform/netsuite-restlet-api
- Install: `npm i netsuite-restlet-api`
- Features:
  - JavaScript API client for NetSuite RESTlets
  - TypeScript support (83.2% TypeScript, 16.8% JavaScript)
- Status: Active
- Latest Release: v1.0.4 (March 5, 2025)
- Last Commit: May 19, 2025
- Stars: 0
- Forks: 0

### netsuite-api-client (julbrs/netsuite-api-client)
- GitHub: https://github.com/julbrs/netsuite-api-client
- Install: Available via npm
- Features:
  - Combines REST calls and SuiteQL queries
  - ESM only with TypeScript types
  - Merges netsuite-rest and suiteql packages
- Status: Active
- Last Commit: March 3, 2025

## Java

### NetSuite SOAP Client Libraries
- Maven: Available on Maven Central Repository
- Features:
  - SOAP-based NetSuite integration
  - Access to SuiteTalk Web Services
- Status: Active
- Note: Specific Maven dependency information requires Maven Central search

## PHP

### netsuitephp/netsuite-php
- Package: https://packagist.org/packages/netsuitephp/netsuite-php
- GitHub: https://github.com/netsuitephp/netsuite-php
- Install: `composer require netsuitephp/netsuite-php`
- Features:
  - PHP SDK for NetSuite SuiteTalk Web Services
  - SOAP API integration
- Status: Check GitHub for maintenance status

## Other Languages

### netsuite-rs (jacobsvante/netsuite-rs)
- GitHub: https://github.com/jacobsvante/netsuite-rs
- Language: Rust
- Features:
  - Rust library for NetSuite REST APIs
- Status: Active

### go-netsuite-soap (omniboost/go-netsuite-soap)
- GitHub: https://github.com/omniboost/go-netsuite-soap
- Language: Go
- Features:
  - Go client library for NetSuite REST API
- Status: Active

## Enterprise iPaaS Platforms

### Celigo
- Website: https://www.celigo.com/
- Product: Integrator.io
- Features:
  - #1 global leader in NetSuite integration
  - 5,000+ NetSuite customers
  - 80+ prebuilt integrations (Salesforce, Shopify, Amazon, HubSpot, etc.)
  - Real-time data synchronization
  - Visual workflow builder
  - AI-powered error handling
  - Suitelet support with unlimited dynamic lookups
  - Advanced data validation and error handling
  - Enterprise-grade security (GDPR, SOC-2 compliant)
  - Built on SuiteScript 2.0 and SuiteCloud Development Framework (SDF)
- Use Cases: Quote-to-cash, procure-to-pay, expense management automation

### Boomi (Dell Boomi)
- Website: https://boomi.com/
- Features:
  - NetSuite connector for iPaaS integration
  - Low-code integration platform
  - Pre-built NetSuite connectors
- Use Cases: Enterprise application integration, data synchronization

### MuleSoft (Salesforce)
- Website: https://www.mulesoft.com/
- Product: Anypoint Platform with NetSuite Connector
- Features:
  - NetSuite connector available on Anypoint Exchange
  - API-led integration approach
  - Enterprise integration patterns
- Use Cases: API management, system integration, data transformation

### Jitterbit
- Website: https://www.jitterbit.com/
- Features:
  - NetSuite integration templates
  - Low-code integration platform
  - Pre-built NetSuite endpoints
- Use Cases: Application integration, data migration

### Workato
- Website: https://www.workato.com/
- Features:
  - NetSuite connector with pre-built recipes
  - Enterprise automation platform
  - Workflow automation
- Use Cases: Business process automation, application integration

## ODBC/JDBC Drivers

### Devart ODBC Driver for NetSuite
- Website: https://www.devart.com/odbc/netsuite/
- Features:
  - Direct connectivity to NetSuite via ODBC
  - SQL access to NetSuite data
  - Support for Windows, macOS, Linux
  - 32-bit and 64-bit versions
  - Compatible with BI tools (Tableau, Power BI, Excel)
- Use Cases: Reporting, analytics, data migration

### CData JDBC Driver for NetSuite
- Website: https://www.cdata.com/drivers/netsuite/jdbc/
- Features:
  - JDBC connectivity to NetSuite
  - SQL-92 compliant
  - Support for JDBC applications
  - Real-time data access
- Use Cases: Java applications, ETL tools, database integration

## RESTlet Frameworks

### ns-restlet-framework (felipechang/ns-restlet-framework)
- GitHub: https://github.com/felipechang/ns-restlet-framework
- Features:
  - NetSuite RESTlet development framework
  - Structured approach to RESTlet creation
- Status: Active

## Community Resources

### Official NetSuite Developer Portal
- URL: https://developers.netsuite.com/
- Resources:
  - SuiteCloud Development Framework documentation
  - SuiteScript API reference
  - SuiteTalk (SOAP/REST) documentation
  - Code samples and tutorials

### SuiteAnswers
- URL: https://support.netsuite.com/
- Resources:
  - Knowledge base articles
  - Technical documentation
  - Community forums

### NetSuite Professionals Community
- Platform: Various online forums and user groups
- Resources:
  - Developer discussions
  - Integration best practices
  - Troubleshooting support

## Authentication Methods (2025 Updates)

### Current Supported Methods
- OAuth 2.0 (Recommended)
- Token-Based Authentication (TBA)

### Deprecated Methods
- OAuth 1.0 (Removed in 2025.1 release)

## SuiteCloud SDK Updates (2025.1+)

### New Features
- Secure Credentials Storage with PKCS#12 encryption
- Visual Studio Code 2025.1 SuiteCloud Extension
- Node.js 22 LTS support
- Oracle JDK 17 and 21 support

## References

- PyPI: https://pypi.org/
- npm: https://www.npmjs.com/
- Maven Central: https://search.maven.org/
- Packagist: https://packagist.org/
- GitHub: https://github.com/
- Oracle NetSuite Developers: https://developers.netsuite.com/
- SuiteCloud CLI Documentation: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_1558708800.html
