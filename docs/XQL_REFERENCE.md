# XQL Query Language Reference

Quick reference for XQL (XSIAM Query Language) syntax used in parsing rules, modeling rules, and queries.

## Basic Structure

### Parsing Rules (.xif)

```xql
[INGEST:vendor="vendor_name", product="product_name", target_dataset="dataset_name", no_hit=keep]
// Parsing logic here
filter _raw_log ~= "pattern"
| alter
    field1 = extract(_raw_log, "regex_pattern"),
    field2 = coalesce(json_field, "default")
| alter
    _time = parse_timestamp("%Y-%m-%d %H:%M:%S", timestamp_field);
```

### Modeling Rules (.xif)

```xql
[MODEL: dataset="datasetname_raw"]
// Modeling logic here
alter
    xdm.source.host.hostname = src_host,
    xdm.target.host.ipv4_addresses = arraycreate(dst_ip),
    xdm.event.type = "NETWORK"
| filter xdm.event.type != null;
```

## Core Operators

### Filter

```xql
// String matching
filter field = "value"
filter field != "value"
filter field ~= "regex_pattern"      // Regex match
filter field !~= "regex_pattern"     // Regex not match
filter field contains "substring"
filter field not contains "substring"

// Numeric comparisons
filter count > 10
filter timestamp >= to_timestamp("2024-01-01")

// Null checks
filter field != null
filter field = null

// Logical operators
filter field1 = "a" and field2 = "b"
filter field1 = "a" or field2 = "b"
filter not (field = "value")

// IN operator
filter field in ("value1", "value2", "value3")
```

### Alter (Create/Modify Fields)

```xql
alter
    new_field = "static_value",
    computed_field = field1 + field2,
    extracted = extract(raw_log, "pattern"),
    parsed_json = json_extract(json_field, "$.key")
```

### Extract Functions

```xql
// Regex extraction (returns first capture group)
extract(field, "User:\s*(\w+)")

// Extract with named groups
extract(field, "src=(?P<src_ip>\d+\.\d+\.\d+\.\d+)")

// JSON extraction
json_extract(json_field, "$.user.name")
json_extract_scalar(json_field, "$.count")
json_extract_array(json_field, "$.items")

// Array extraction
arrayindex(array_field, 0)    // First element
arraystring(array_field, ",") // Join with comma
```

### String Functions

```xql
// Case conversion
lowercase(field)
uppercase(field)

// Trimming
trim(field)
ltrim(field)
rtrim(field)

// Substring
substring(field, 0, 10)       // First 10 chars
strlen(field)                 // Length

// Replace
replace(field, "old", "new")
replex(field, "regex", "replacement")

// Concatenation
concat(field1, "-", field2)
format_string("%s: %d", str_field, num_field)

// Split
split(field, ",")             // Returns array
arrayindex(split(field, ","), 0)  // First element
```

### Numeric Functions

```xql
// Arithmetic
add(field, 10)
subtract(field, 5)
multiply(field, 2)
divide(field, 100)

// Rounding
floor(field)
ceil(field)
round(field, 2)              // 2 decimal places

// Conversion
to_integer(field)
to_float(field)
to_string(field)
```

### Timestamp Functions

```xql
// Parse timestamp
parse_timestamp("%Y-%m-%d %H:%M:%S", timestamp_string)
parse_timestamp("%Y-%m-%dT%H:%M:%S.%fZ", iso_timestamp)

// Format timestamp
format_timestamp("%Y-%m-%d", _time)

// Epoch conversion
to_timestamp(epoch_seconds)
to_epoch(_time, "SECONDS")
to_epoch(_time, "MILLIS")

// Current time
current_time()

// Time arithmetic
timestamp_diff(_time, other_time, "SECONDS")
add_time(_time, "1h")
subtract_time(_time, "24h")
```

### Conditional Functions

```xql
// Coalesce (first non-null)
coalesce(field1, field2, "default")

// If-then-else
if(condition, true_value, false_value)

// Case statement
case(
    field = "a", "Alpha",
    field = "b", "Beta",
    "Unknown"
)
```

### Array Functions

```xql
// Create array
arraycreate(value1, value2, value3)
arraycreate(coalesce(field1, ""), coalesce(field2, ""))

// Array operations
arrayconcat(array1, array2)
arraydistinct(array_field)
arrayfilter(array_field, "@element" != "")
arraymap(array_field, lowercase("@element"))
arraylength(array_field)

// Array to string
arraystring(array_field, ", ")
```

### IP Functions

```xql
// IP validation
incidr(ip_field, "10.0.0.0/8")

// IP extraction from text
extract(field, "(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
```

## XDM Field Mapping (Modeling Rules)

### Common XDM Fields

```xql
// Source fields
xdm.source.host.hostname
xdm.source.host.ipv4_addresses
xdm.source.host.ipv6_addresses
xdm.source.host.mac_addresses
xdm.source.user.username
xdm.source.user.domain
xdm.source.port
xdm.source.process.name
xdm.source.process.pid

// Target fields
xdm.target.host.hostname
xdm.target.host.ipv4_addresses
xdm.target.user.username
xdm.target.port
xdm.target.url
xdm.target.file.path
xdm.target.file.filename
xdm.target.file.sha256

// Event fields
xdm.event.type
xdm.event.outcome
xdm.event.outcome_reason
xdm.event.operation
xdm.event.description
xdm.event.id

// Network fields
xdm.network.protocol
xdm.network.application_protocol
xdm.network.direction
xdm.network.session_id

// Auth fields
xdm.auth.auth_method
xdm.auth.privilege_level

// Alert fields
xdm.alert.severity
xdm.alert.name
xdm.alert.description
```

### Event Type Values

```xql
xdm.event.type = "NETWORK"
xdm.event.type = "FILE"
xdm.event.type = "PROCESS"
xdm.event.type = "REGISTRY"
xdm.event.type = "AUTH"
xdm.event.type = "AUDIT"
xdm.event.type = "EMAIL"
xdm.event.type = "WEB"
```

### Outcome Values

```xql
xdm.event.outcome = XDM_CONST.outcome_success
xdm.event.outcome = XDM_CONST.outcome_failure
xdm.event.outcome = XDM_CONST.outcome_partial
xdm.event.outcome = XDM_CONST.outcome_unknown
```

## Common Patterns

### Parse Syslog

```xql
filter _raw_log ~= "^\<\d+\>"
| alter
    priority = to_integer(extract(_raw_log, "^\<(\d+)\>")),
    timestamp_str = extract(_raw_log, "^\<\d+\>(\w{3}\s+\d+\s+\d+:\d+:\d+)"),
    hostname = extract(_raw_log, "^\<\d+\>\w{3}\s+\d+\s+\d+:\d+:\d+\s+(\S+)"),
    message = extract(_raw_log, "^\<\d+\>\w{3}\s+\d+\s+\d+:\d+:\d+\s+\S+\s+(.*)")
| alter _time = parse_timestamp("%b %d %H:%M:%S", timestamp_str);
```

### Parse JSON Logs

```xql
filter _raw_log ~= "^\{"
| alter
    event_type = json_extract_scalar(_raw_log, "$.event_type"),
    src_ip = json_extract_scalar(_raw_log, "$.source.ip"),
    dst_ip = json_extract_scalar(_raw_log, "$.destination.ip"),
    user = json_extract_scalar(_raw_log, "$.user.name"),
    timestamp = json_extract_scalar(_raw_log, "$.timestamp")
| alter _time = parse_timestamp("%Y-%m-%dT%H:%M:%S.%fZ", timestamp);
```

### Parse Key-Value Pairs

```xql
alter
    src = extract(_raw_log, "src=(\S+)"),
    dst = extract(_raw_log, "dst=(\S+)"),
    action = extract(_raw_log, "action=(\S+)"),
    user = extract(_raw_log, "user=(\S+)")
```

### Handle Multiple Formats

```xql
alter
    src_ip = coalesce(
        json_extract_scalar(_raw_log, "$.source_ip"),
        extract(_raw_log, "src[_\-]?ip[=:]?\s*(\d+\.\d+\.\d+\.\d+)"),
        extract(_raw_log, "from\s+(\d+\.\d+\.\d+\.\d+)")
    )
```

### Model Authentication Event

```xql
[MODEL: dataset="auth_raw"]
alter
    xdm.source.user.username = src_user,
    xdm.source.host.ipv4_addresses = arraycreate(coalesce(src_ip, "")),
    xdm.target.host.hostname = dst_host,
    xdm.event.type = "AUTH",
    xdm.event.outcome = if(
        status = "success", XDM_CONST.outcome_success,
        status = "failure", XDM_CONST.outcome_failure,
        XDM_CONST.outcome_unknown
    ),
    xdm.auth.auth_method = auth_method
| filter xdm.source.user.username != null;
```

## Debugging Tips

1. **Test filters incrementally** - Start with broad filters and narrow down
2. **Use `limit`** - Add `| limit 10` when testing to see sample results
3. **Check null values** - Many parsing issues come from null fields
4. **Use coalesce for defaults** - Prevents null propagation
5. **Validate regex separately** - Test regex patterns before embedding

## Reference

- [XQL Language Reference](https://docs-cortex.paloaltonetworks.com/r/Cortex-XQL-Language-Reference)
- [XDM Schema Reference](https://docs-cortex.paloaltonetworks.com/r/Cortex-XDR-XQL-Reference/XDM-Field-Mappings)
