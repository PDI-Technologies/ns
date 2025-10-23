/**
 * @NApiVersion 2.1
 * @NScriptType ScheduledScript
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
