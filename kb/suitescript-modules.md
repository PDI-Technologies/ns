# SuiteScript 2.x Modules

## N/https
### Methods
- **https.get(options)** - Performs a secure HTTPS GET request
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4296361104
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567628658

- **https.post(options)** - Performs a secure HTTPS POST request
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440793315
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567628658

- **https.put(options)** - Performs a secure HTTPS PUT request
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4418229131

- **https.delete(options)** - Performs a secure HTTPS DELETE request
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4418229131

- **https.request(options)** - General HTTPS request method
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440793315
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4418229131

- **https.requestRestlet(options)** - Request to NetSuite RESTlet
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4418229131

- **https.requestSuiteTalkRest(options)** - Request to SuiteTalk REST API
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4418229131

### Options Structure
```javascript
{
  url: string,           // Target URL
  method: https.Method,  // HTTP method (GET, POST, PUT, DELETE)
  headers: {},          // Request headers
  body: string          // Request body
}
```

### Hash Method
- **https.hash(options)** - Creates hash for https.SecureString
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_459472900389

https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4205693274

---

## N/record
### Methods
- **record.create(options)** - Creates new record
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440822690
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4296361104

- **record.load(options)** - Loads existing record
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440822690
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4296361104

- **record.copy(options)** - Copies existing record
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440822690

- **record.delete(options)** - Deletes record
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440822690

- **record.submitFields(options)** - Submits specific field changes
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440822690

- **record.transform(options)** - Transforms one record type to another
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440822690

- **record.attach(options)** - Attaches file to record
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440822690

- **record.detach(options)** - Detaches file from record
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440822690

### Field Operations
- **getValue({fieldId})** - Gets field value
- **setValue({fieldId, value})** - Sets field value
- **getSublistValue({sublistId, fieldId, line})** - Gets sublist field value

### Async Versions Available
All methods have `.promise()` variants for asynchronous operations.

https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4407050795
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_3763056139
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N3194671
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4612521061
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4858836386

---

## N/search
### Methods
- **search.create({type, filters, columns})** - Creates new search
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4413162576
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4752724744

- **search.load({id})** - Loads saved search
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4752724744

- **search.createColumn(options)** - Creates search column
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

- **search.createFilter(options)** - Creates search filter
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

- **search.createSetting(options)** - Creates search setting
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

- **search.delete(options)** - Deletes search
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

- **search.duplicates(options)** - Finds duplicate records
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

- **search.global(options)** - Performs global search
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

- **search.lookupFields(options)** - Looks up specific fields
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

### Search Operators (search.Operator)
- is, isnot, isnotempty, isempty
- contains, doesnotcontain
- startswith, doesnotstartwith
- greaterthan, greaterthanorequalto
- lessthan, lessthanorequalto
- onorafter, onorbefore, after, before
- anyof, noneof
- haskeyword, haskey

https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345767603

### Search Types (search.Type)
- CUSTOMER, VENDOR, EMPLOYEE, SALES_ORDER, etc.

### Search Components
- **search.Sort** - Sorting options (ASCENDING, DESCENDING)
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345767603

- **search.Summary** - Summary functions (GROUP, SUM, AVG, MAX, MIN, COUNT)
  - https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345767603

### Async Versions Available
All methods have `.promise()` variants for asynchronous operations.

https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4243798608
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4407050795
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440793315
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4460505281
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4205693274
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4321345532
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345775747
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4486559010

---

## N/runtime
### Methods
- **runtime.getCurrentUser()** - Returns current user information
- **runtime.getCurrentScript()** - Returns current script information

https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

---

## N/encode
### Methods
- **encode.convert({string, inputEncoding, outputEncoding})** - Converts string encoding

Supported encodings: UTF-8, BASE_64, BASE_64_URL_SAFE, HEX

https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

---

## Script Types

### @NScriptType Restlet
RESTful web service entry point for external integrations
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType Restlet
 */
define(['N/https'], function(https) {
    function get(context) { /* implementation */ }
    function post(context) { /* implementation */ }
    return { get: get, post: post };
});
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4296361104
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567628658

### @NScriptType ScheduledScript
Runs on scheduled basis for batch processing
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType ScheduledScript
 */
define(['N/search', 'N/log'], function(search, log) {
    function execute(context) { /* implementation */ }
    return { execute: execute };
});
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4243798608
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4296361104

### @NScriptType MapReduceScript
Large-scale data processing with parallel execution
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType MapReduceScript
 */
define(['N/search'], function(search) {
    function getInputData() { /* implementation */ }
    function map(context) { /* implementation */ }
    function reduce(context) { /* implementation */ }
    function summarize(context) { /* implementation */ }
    return {
        getInputData: getInputData,
        map: map,
        reduce: reduce,
        summarize: summarize
    };
});
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4426027147

### @NScriptType MassUpdateScript
Updates multiple records in bulk
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType MassUpdateScript
 */
define(['N/record'], function(record) {
    function each(context) { /* implementation */ }
    return { each: each };
});
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4243798608

### @NScriptType Suitelet
Custom web pages and forms within NetSuite UI
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType Suitelet
 */
define(['N/ui/serverWidget'], function(ui) {
    function onRequest(context) { /* implementation */ }
    return { onRequest: onRequest };
});
```

### @NScriptType UserEventScript
Triggers on record operations (create, edit, view, delete)
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType UserEventScript
 */
define(['N/record'], function(record) {
    function beforeLoad(context) { /* implementation */ }
    function beforeSubmit(context) { /* implementation */ }
    function afterSubmit(context) { /* implementation */ }
    return {
        beforeLoad: beforeLoad,
        beforeSubmit: beforeSubmit,
        afterSubmit: afterSubmit
    };
});
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4296361104
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4483165708

### @NScriptType ClientScript
Executes in browser on user actions
```javascript
/**
 * @NApiVersion 2.x
 * @NScriptType ClientScript
 */
define(['N/search'], function(search) {
    function pageInit(context) { /* implementation */ }
    function fieldChanged(context) { /* implementation */ }
    function saveRecord(context) { /* implementation */ }
    return {
        pageInit: pageInit,
        fieldChanged: fieldChanged,
        saveRecord: saveRecord
    };
});
```
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4413162576
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567628658

---

## Official Documentation URLs

### Primary References
- **N/https Module**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4418229131
- **N/record Module**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440822690
- **N/search Module**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122
- **N/runtime Module**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122
- **N/encode Module**: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122

### Main API Reference
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4407050795
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345764122
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4440793315

### Script Samples
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4567628658
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4296361104
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4243798608

### Additional Resources
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4612521061
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345775747
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4486559010
- https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_4345767603
