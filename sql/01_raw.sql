-- RAW layer: the JSON file loaded as-is. Nothing is filtered or renamed here,
-- so we can always compare later layers back to what the source gave us.
CREATE TABLE raw.events AS
SELECT *
FROM read_json_auto('{RAW_PATH}', format = 'newline_delimited');
