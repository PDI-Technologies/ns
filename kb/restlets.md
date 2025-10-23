# RESTlets

## Definition
RESTlets are custom RESTful web service endpoints defined via NetSuite's SuiteScript 2.x platform that enable external applications and internal scripts to interact with NetSuite through HTTP requests.

## Script Structure
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType Restlet
 */
define(['N/record', 'N/search'], function(record, search) {

    function doGet(context) {
        // Handle GET requests
        return { status: 'success', data: {} };
    }

    function doPost(context) {
        // Handle POST requests
        return { status: 'created', id: 123 };
    }

    function doPut(context) {
        // Handle PUT requests
        return { status: 'updated' };
    }

    function doDelete(context) {
        // Handle DELETE requests
        return { status: 'deleted' };
    }

    return {
        get: doGet,
        post: doPost,
        put: doPut,
        delete: doDelete
    };
});
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4618456517

## Entry Points
- **get(context)** - Entry point for retrieving data (e.g., retrieving NetSuite records). Executed when GET request is sent. Returns HTTP response body. - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4557203242
- **post(context)** - Entry point for creating data (e.g., creating NetSuite records). Executed when POST request is sent. Returns HTTP response body. - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4557203242
- **put(context)** - Entry point for updating/upserting data (e.g., inserting/upserting NetSuite records). Executed when PUT request is sent. Returns HTTP response body. - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4557203242
- **delete(context)** - Entry point for deleting data (e.g., deleting NetSuite records). Executed when DELETE request is sent. Returns HTTP response body. - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4557203242

## Deployment Steps
1. Create RESTlet script file with @NScriptType Restlet annotation
2. Upload script to File Cabinet (Customization > Scripting > Scripts > New)
3. Create Script Record and configure settings
4. Set Status to "Testing" for debugging or "Released" for production - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_162015275927
5. Create Script Deployment record with unique Deployment ID
6. Set deployment status and audience (roles/employees who can execute)
7. Note the Script ID (e.g., customscript_my_restlet) and Deployment ID (e.g., customdeploy_my_restlet)

## Calling RESTlets

### Internal (SuiteScript 2.x)
```javascript
/**
 * @NApiVersion 2.x
 */
define(['N/https'], function(https) {
    var response = https.requestRestlet({
        scriptId: 'customscript_my_restlet',
        deploymentId: 'customdeploy_my_restlet',
        body: JSON.stringify({ recordId: 123 }),
        headers: {
            'Content-Type': 'application/json'
        }
    });
    return response.body;
});
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4418229131

### Internal (SuiteScript 1.0)
```javascript
nlapiRequestRestlet(scriptId, deploymentId, urlParams, body, headers, httpMethod);
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4417231053

### External (HTTP)
```bash
curl -X POST \
  https://{account}.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script={scriptId}&deploy={deployId} \
  -H "Authorization: OAuth oauth_consumer_key=\"...\", oauth_token=\"...\", oauth_signature_method=\"HMAC-SHA256\", oauth_timestamp=\"...\", oauth_nonce=\"...\", oauth_version=\"1.0\", oauth_signature=\"...\"" \
  -H "Content-Type: application/json" \
  -d '{"recordId": 123}'
```

## URL Format
**Pattern**: `https://{account}.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script={scriptId}&deploy={deployId}`

**Dynamic URL Generation (Internal)**:
```javascript
require(['N/url'], function(url) {
    var restletUrl = url.resolveScript({
        scriptId: 'customscript_my_restlet',
        deploymentId: 'customdeploy_my_restlet_deploy',
        params: { 'myparam': 'value' }
    });
    // Returns: '/app/site/hosting/scriptlet.nl?script=customscript_my_restlet&deploy=customdeploy_my_restlet_deploy&myparam=value'
});
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4618456734

## Governance
- **Usage units**: RESTlets operate within standard SuiteScript governance limits (5000 units per execution context)
- **String limit**: 10MB maximum for request/response payload
- Each RESTlet execution counts against script governance limits
- Different operations consume different units (e.g., record.load = 4 units, search = 10 units)

## Error Handling
**HTTP Success Codes**:
- **200 OK** - Request executed successfully. May include SuiteScript errors in response body if handled by script.

**HTTP Error Codes**:
- Standard HTTP error codes (400, 401, 403, 404, 500, etc.) returned for various failure scenarios

**SuiteScript Errors**:
- Errors can be caught and handled within RESTlet code using try-catch blocks
- Unhandled errors return error details in response body

https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4634920277

## Debugging
1. Set script deployment Status to "Testing"
2. Ensure script does not include HTTP authorization header during debugging
3. Navigate to Customization > Scripting > Script Debugger
4. Click "Debug Existing" button to start debugging session

https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_162015275927

## Use Cases
- Custom business logic requiring multiple record operations
- Complex workflows not supported by standard REST API
- File Cabinet operations
- Integration with external systems requiring custom data transformations
- Batch operations (creating/updating multiple records)
- Domain-specific logic and validation

## Official Documentation URLs
- **RESTlet Overview**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_161460646050
- **Script Type Reference**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4032860783
- **Entry Points**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4557203242
- **Script Examples**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4387799403
- **Calling from SuiteScript**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4418229131
- **N/scriptTypes/restlet Module**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440793315
- **Error Handling**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4634920277
- **Debugging**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_162015275927
- **URL Resolution**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4618456734
- **HTTP Methods**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4618434109
