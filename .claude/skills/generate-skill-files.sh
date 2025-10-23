#!/bin/bash

# NetSuite Skills - File Generator Script
# Generates placeholder files for all skill documentation

set -e

SKILLS_DIR="/opt/ns/.claude/skills"

echo "🚀 NetSuite Skills File Generator"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to create a placeholder markdown file
create_placeholder() {
    local filepath="$1"
    local title="$2"
    local description="$3"

    if [ ! -f "$filepath" ]; then
        cat > "$filepath" << EOF
# $title

$description

## Overview

[Content to be added]

## Topics

### Topic 1

[Content to be added]

### Topic 2

[Content to be added]

## Examples

\`\`\`javascript
// Example code to be added
\`\`\`

## Best Practices

- Best practice 1
- Best practice 2
- Best practice 3

## Related Documentation

- [Related Doc 1](link)
- [Related Doc 2](link)
EOF
        echo -e "${GREEN}✓${NC} Created: $filepath"
    else
        echo -e "${YELLOW}⊙${NC} Exists: $filepath"
    fi
}

# Function to create JavaScript template
create_js_template() {
    local filepath="$1"
    local script_type="$2"

    if [ ! -f "$filepath" ]; then
        cat > "$filepath" << 'EOF'
/**
 * @NApiVersion 2.1
 * @NScriptType SCRIPT_TYPE
 */
define(['N/record', 'N/log'],
    (record, log) => {

        function entryPoint(context) {
            try {
                // Your code here
                log.debug('Script Executed', 'Success');
            } catch (e) {
                log.error('Script Error', e);
            }
        }

        return {
            entryPoint: entryPoint
        };
    }
);
EOF
        sed -i "s/SCRIPT_TYPE/$script_type/g" "$filepath"
        echo -e "${GREEN}✓${NC} Created: $filepath"
    else
        echo -e "${YELLOW}⊙${NC} Exists: $filepath"
    fi
}

echo -e "${BLUE}Creating netsuite-developer files...${NC}"
echo ""

# netsuite-developer/suitescript
create_placeholder "$SKILLS_DIR/netsuite-developer/suitescript/client-scripts.md" \
    "Client Scripts" \
    "Client-side scripts for browser-based validation and UI interactions."

create_placeholder "$SKILLS_DIR/netsuite-developer/suitescript/scheduled.md" \
    "Scheduled Scripts" \
    "Time-based batch processing scripts for automated jobs."

create_placeholder "$SKILLS_DIR/netsuite-developer/suitescript/map-reduce.md" \
    "Map/Reduce Scripts" \
    "Large-scale data processing with Map/Reduce pattern."

create_placeholder "$SKILLS_DIR/netsuite-developer/suitescript/restlets.md" \
    "RESTlet Scripts" \
    "Custom REST API endpoints for external integrations."

create_placeholder "$SKILLS_DIR/netsuite-developer/suitescript/suitelets.md" \
    "Suitelet Scripts" \
    "Custom web pages and forms in NetSuite."

create_placeholder "$SKILLS_DIR/netsuite-developer/suitescript/workflow-actions.md" \
    "Workflow Action Scripts" \
    "Custom actions for NetSuite workflows."

create_placeholder "$SKILLS_DIR/netsuite-developer/suitescript/mass-update.md" \
    "Mass Update Scripts" \
    "Bulk record update scripts via UI."

create_placeholder "$SKILLS_DIR/netsuite-developer/suitescript/portlets.md" \
    "Portlet Scripts" \
    "Dashboard widgets and custom portlets."

# netsuite-developer/deployment
create_placeholder "$SKILLS_DIR/netsuite-developer/deployment/cli-commands.md" \
    "CLI Commands Reference" \
    "Complete reference for SuiteCloud CLI commands."

create_placeholder "$SKILLS_DIR/netsuite-developer/deployment/project-structure.md" \
    "Project Structure Guide" \
    "SDF project structure and file organization."

create_placeholder "$SKILLS_DIR/netsuite-developer/deployment/ci-cd.md" \
    "CI/CD Integration" \
    "Continuous integration and deployment workflows."

create_placeholder "$SKILLS_DIR/netsuite-developer/deployment/ci-cd-best-practices.md" \
    "CI/CD Best Practices" \
    "Best practices for NetSuite CI/CD pipelines."

# netsuite-developer/patterns
create_placeholder "$SKILLS_DIR/netsuite-developer/patterns/error-handling.md" \
    "Error Handling Patterns" \
    "Comprehensive error handling strategies."

create_placeholder "$SKILLS_DIR/netsuite-developer/patterns/governance.md" \
    "Governance Management" \
    "Managing governance units and optimization."

create_placeholder "$SKILLS_DIR/netsuite-developer/patterns/performance.md" \
    "Performance Optimization" \
    "Performance optimization techniques."

create_placeholder "$SKILLS_DIR/netsuite-developer/patterns/security.md" \
    "Security Best Practices" \
    "Security patterns and practices."

create_placeholder "$SKILLS_DIR/netsuite-developer/patterns/code-organization.md" \
    "Code Organization" \
    "Code structure and organization patterns."

# netsuite-developer/testing
create_placeholder "$SKILLS_DIR/netsuite-developer/testing/unit-testing.md" \
    "Unit Testing" \
    "Unit testing frameworks and patterns."

create_placeholder "$SKILLS_DIR/netsuite-developer/testing/debugging.md" \
    "Debugging Techniques" \
    "Debugging strategies and tools."

create_placeholder "$SKILLS_DIR/netsuite-developer/testing/testing-workflow.md" \
    "Testing Workflow" \
    "Complete testing workflow and checklist."

create_placeholder "$SKILLS_DIR/netsuite-developer/testing/troubleshooting.md" \
    "Troubleshooting Guide" \
    "Common issues and solutions."

# netsuite-developer/examples
create_placeholder "$SKILLS_DIR/netsuite-developer/examples/sales-order-automation.md" \
    "Sales Order Automation Example" \
    "Complete sales order automation implementation."

create_placeholder "$SKILLS_DIR/netsuite-developer/examples/invoice-processing.md" \
    "Invoice Processing Example" \
    "Automated invoice processing implementation."

create_placeholder "$SKILLS_DIR/netsuite-developer/examples/customer-portal.md" \
    "Customer Portal Example" \
    "Custom customer portal with Suitelet."

create_placeholder "$SKILLS_DIR/netsuite-developer/examples/inventory-management.md" \
    "Inventory Management Example" \
    "Inventory management automation."

create_placeholder "$SKILLS_DIR/netsuite-developer/examples/integration-endpoints.md" \
    "Integration Endpoints Example" \
    "RESTlet integration endpoints."

# netsuite-developer/templates
create_js_template "$SKILLS_DIR/netsuite-developer/templates/user-event.js" "UserEventScript"
create_js_template "$SKILLS_DIR/netsuite-developer/templates/client-script.js" "ClientScript"
create_js_template "$SKILLS_DIR/netsuite-developer/templates/scheduled-script.js" "ScheduledScript"
create_js_template "$SKILLS_DIR/netsuite-developer/templates/map-reduce-script.js" "MapReduceScript"
create_js_template "$SKILLS_DIR/netsuite-developer/templates/restlet.js" "Restlet"
create_js_template "$SKILLS_DIR/netsuite-developer/templates/suitelet.js" "Suitelet"

echo ""
echo -e "${BLUE}Creating netsuite-integrations files...${NC}"
echo ""

# netsuite-integrations/restlet-apis
create_placeholder "$SKILLS_DIR/netsuite-integrations/restlet-apis/api-design.md" \
    "RESTlet API Design" \
    "RESTful API design principles and patterns."

create_placeholder "$SKILLS_DIR/netsuite-integrations/restlet-apis/authentication.md" \
    "RESTlet Authentication" \
    "Authentication methods for RESTlet APIs."

create_placeholder "$SKILLS_DIR/netsuite-integrations/restlet-apis/crud-patterns.md" \
    "CRUD Patterns" \
    "Create, Read, Update, Delete patterns."

create_placeholder "$SKILLS_DIR/netsuite-integrations/restlet-apis/error-handling.md" \
    "API Error Handling" \
    "Error handling for RESTlet APIs."

# netsuite-integrations/salesforce
create_placeholder "$SKILLS_DIR/netsuite-integrations/salesforce/customer-sync.md" \
    "Customer Synchronization" \
    "Salesforce Account ↔ NetSuite Customer sync."

create_placeholder "$SKILLS_DIR/netsuite-integrations/salesforce/order-sync.md" \
    "Order Synchronization" \
    "Salesforce Opportunity ↔ NetSuite Sales Order sync."

create_placeholder "$SKILLS_DIR/netsuite-integrations/salesforce/quote-to-cash.md" \
    "Quote-to-Cash Flow" \
    "Complete quote-to-cash integration."

# netsuite-integrations/databases
create_placeholder "$SKILLS_DIR/netsuite-integrations/databases/export-to-db.md" \
    "Export to Database" \
    "NetSuite to external database export."

create_placeholder "$SKILLS_DIR/netsuite-integrations/databases/import-from-db.md" \
    "Import from Database" \
    "External database to NetSuite import."

create_placeholder "$SKILLS_DIR/netsuite-integrations/databases/scheduled-sync.md" \
    "Scheduled Synchronization" \
    "Scheduled database sync patterns."

create_placeholder "$SKILLS_DIR/netsuite-integrations/databases/mcp-tools.md" \
    "Database MCP Tools" \
    "Using MSSQL, PostgreSQL, MySQL MCP tools."

# netsuite-integrations/suitetalk
create_placeholder "$SKILLS_DIR/netsuite-integrations/suitetalk/rest-api.md" \
    "SuiteTalk REST API" \
    "Using NetSuite REST API."

create_placeholder "$SKILLS_DIR/netsuite-integrations/suitetalk/soap-api.md" \
    "SuiteTalk SOAP API" \
    "Using NetSuite SOAP API."

create_placeholder "$SKILLS_DIR/netsuite-integrations/suitetalk/bulk-operations.md" \
    "Bulk Operations" \
    "Bulk data operations with SuiteTalk."

# netsuite-integrations/external-apis
create_placeholder "$SKILLS_DIR/netsuite-integrations/external-apis/http-requests.md" \
    "HTTP Requests" \
    "Making HTTP requests from NetSuite."

create_placeholder "$SKILLS_DIR/netsuite-integrations/external-apis/webhook-handlers.md" \
    "Webhook Handlers" \
    "Receiving webhooks in NetSuite."

# netsuite-integrations/authentication
create_placeholder "$SKILLS_DIR/netsuite-integrations/authentication/oauth2.md" \
    "OAuth 2.0" \
    "OAuth 2.0 authentication."

create_placeholder "$SKILLS_DIR/netsuite-integrations/authentication/tba.md" \
    "Token-Based Authentication" \
    "TBA setup and usage."

create_placeholder "$SKILLS_DIR/netsuite-integrations/authentication/api-keys.md" \
    "API Keys" \
    "Custom API key patterns."

create_placeholder "$SKILLS_DIR/netsuite-integrations/authentication/retry-patterns.md" \
    "Retry Patterns" \
    "Retry and error recovery patterns."

create_placeholder "$SKILLS_DIR/netsuite-integrations/authentication/logging.md" \
    "Logging and Monitoring" \
    "Integration logging and monitoring."

# netsuite-integrations/examples
create_placeholder "$SKILLS_DIR/netsuite-integrations/examples/restlet-integration.md" \
    "RESTlet Integration Example" \
    "Complete RESTlet integration."

create_placeholder "$SKILLS_DIR/netsuite-integrations/examples/salesforce-bidirectional.md" \
    "Salesforce Bi-Directional Sync" \
    "Complete Salesforce integration."

create_placeholder "$SKILLS_DIR/netsuite-integrations/examples/database-export.md" \
    "Database Export Pipeline" \
    "Complete database export implementation."

echo ""
echo -e "${BLUE}Creating netsuite-business-automation files...${NC}"
echo ""

# netsuite-business-automation/finance
create_placeholder "$SKILLS_DIR/netsuite-business-automation/finance/journal-entries.md" \
    "Journal Entry Automation" \
    "Automated journal entry creation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/finance/reconciliation.md" \
    "Account Reconciliation" \
    "Account reconciliation automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/finance/period-close.md" \
    "Period Close Automation" \
    "Month-end close automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/finance/revenue-recognition.md" \
    "Revenue Recognition" \
    "Revenue recognition automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/finance/intercompany.md" \
    "Intercompany Transactions" \
    "Intercompany transaction automation."

# netsuite-business-automation/order-to-cash
create_placeholder "$SKILLS_DIR/netsuite-business-automation/order-to-cash/sales-orders.md" \
    "Sales Order Automation" \
    "Sales order processing automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/order-to-cash/fulfillment.md" \
    "Fulfillment Automation" \
    "Order fulfillment automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/order-to-cash/invoicing.md" \
    "Invoicing Automation" \
    "Invoice generation automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/order-to-cash/payments.md" \
    "Payment Processing" \
    "Payment processing automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/order-to-cash/revenue.md" \
    "Revenue Recognition" \
    "Revenue recognition for O2C."

# netsuite-business-automation/procure-to-pay
create_placeholder "$SKILLS_DIR/netsuite-business-automation/procure-to-pay/requisitions-pos.md" \
    "Requisitions and Purchase Orders" \
    "Requisition and PO automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/procure-to-pay/receiving.md" \
    "Receiving Automation" \
    "Item receipt automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/procure-to-pay/vendor-bills.md" \
    "Vendor Bill Processing" \
    "Vendor bill automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/procure-to-pay/expense-reports.md" \
    "Expense Report Automation" \
    "Expense report processing."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/procure-to-pay/payments.md" \
    "Payment Automation" \
    "Vendor payment automation."

# netsuite-business-automation/workflows
create_placeholder "$SKILLS_DIR/netsuite-business-automation/workflows/approval-routing.md" \
    "Approval Routing" \
    "Approval workflow patterns."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/workflows/notification-automation.md" \
    "Notification Automation" \
    "Automated notifications."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/workflows/custom-workflows.md" \
    "Custom Workflow Actions" \
    "Custom workflow action scripts."

# netsuite-business-automation/custom-records
create_placeholder "$SKILLS_DIR/netsuite-business-automation/custom-records/record-design.md" \
    "Custom Record Design" \
    "Designing custom record types."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/custom-records/relationship-management.md" \
    "Relationship Management" \
    "Managing record relationships."

# netsuite-business-automation/examples
create_placeholder "$SKILLS_DIR/netsuite-business-automation/examples/finance-automation.md" \
    "Finance Automation Example" \
    "Complete finance automation."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/examples/order-to-cash-workflow.md" \
    "Order-to-Cash Workflow" \
    "Complete O2C workflow."

create_placeholder "$SKILLS_DIR/netsuite-business-automation/examples/procure-to-pay-system.md" \
    "Procure-to-Pay System" \
    "Complete P2P system."

echo ""
echo -e "${GREEN}✅ File generation complete!${NC}"
echo ""
echo "Summary:"
echo "--------"
find "$SKILLS_DIR" -type f -name "*.md" | wc -l | xargs echo "Markdown files:"
find "$SKILLS_DIR" -type f -name "*.js" | wc -l | xargs echo "JavaScript templates:"
echo ""
echo "Next steps:"
echo "1. Review generated placeholder files"
echo "2. Fill in content as needed"
echo "3. Test skills with Claude"
echo ""
