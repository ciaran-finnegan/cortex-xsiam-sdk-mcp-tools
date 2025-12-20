# Sample Prompts for XSIAM Content Development

This guide provides ready-to-use prompts for developing XSIAM content with LLM coding assistants. Each prompt leverages the MCP tools for pattern search and SDK operations.

## How to Ensure the LLM Uses the Index

LLM coding assistants won't automatically use the pattern index - you need to explicitly tell them to. Here's how:

### Method 1: Reference Tools by Name

Always mention the specific MCP tool in your prompt:

```
Use the find_similar_playbooks tool to find playbooks that...
```

```
Call search_patterns to find examples of...
```

### Method 2: Add a System Instruction

Add this to your project's context file (CLAUDE.md, .cursorrules, etc.):

```markdown
## XSIAM Content Development

When creating or modifying XSIAM playbooks, scripts, or integrations:

1. ALWAYS use the pattern search MCP tools FIRST to find relevant examples:
   - find_similar_playbooks - for playbook patterns
   - find_similar_scripts - for script patterns
   - find_integration_patterns - for integration patterns
   - find_xql_examples - for XQL syntax

2. Use the examples from the index as templates - they represent
   validated, production-quality patterns from the official content library.

3. Do NOT rely on training data for XSIAM syntax - always verify
   against indexed examples.
```

### Method 3: Explicit Instructions in Each Prompt

Start prompts with clear instructions:

```
Before writing any code, use the MCP pattern search tools to find
similar examples from the XSIAM content library. Base your implementation
on those patterns rather than general knowledge.
```

### Why This Matters

- The index contains **4,700+ validated examples** from the official Cortex content library
- These examples follow current best practices and correct syntax
- LLM training data may be outdated or contain errors
- The index is updated weekly with the latest patterns

## Pattern Search Prompts

### Finding Playbook Patterns

#### Enrichment Playbooks

```
Use find_similar_playbooks to find playbooks that enrich IP addresses
from multiple threat intelligence sources. Show me the top 5 results
with their pack names.
```

```
Search for playbooks that perform domain enrichment with fallback
sources when the primary source is unavailable.
```

```
Find playbooks that enrich file hashes using sandbox detonation
and return the full YAML content of the best match.
```

#### Incident Response Playbooks

```
Use find_similar_playbooks to find playbooks for phishing investigation
that include email analysis and user notification.
```

```
Find playbooks that handle malware incidents with endpoint isolation
and forensic collection.
```

```
Search for ransomware response playbooks that include containment,
eradication, and recovery phases.
```

#### Remediation & Blocking Playbooks

```
Find playbooks that block IP addresses on Palo Alto firewalls
with an approval workflow before execution.
```

```
Search for playbooks that isolate endpoints across multiple EDR
platforms (CrowdStrike, Microsoft Defender, Carbon Black).
```

```
Use find_similar_playbooks to find playbooks that quarantine
malicious files and notify the security team.
```

#### Cloud Security Playbooks

```
Find playbooks for AWS security incident response that revoke
compromised credentials and rotate keys.
```

```
Search for Azure AD investigation playbooks that check for
suspicious sign-ins and conditional access policy violations.
```

```
Find playbooks that remediate misconfigured S3 buckets
and cloud storage permissions.
```

### Finding Script Patterns

#### Data Parsing & Transformation

```
Use find_similar_scripts to find scripts that parse email headers
and extract sender information, SPF/DKIM results.
```

```
Find scripts that extract IOCs (URLs, IPs, hashes, domains)
from unstructured text or documents.
```

```
Search for scripts that convert between data formats
(JSON to CSV, XML to JSON, etc.).
```

#### Network & Security Analysis

```
Find scripts that validate IP addresses and check if they
belong to private, reserved, or public ranges.
```

```
Search for scripts that perform WHOIS lookups and extract
registrant information.
```

```
Use find_similar_scripts to find scripts that calculate
file hashes (MD5, SHA1, SHA256) from content.
```

#### User & Identity Operations

```
Find scripts that query Active Directory for user information
including group membership and last login.
```

```
Search for scripts that disable user accounts across multiple
identity providers (AD, Okta, Azure AD).
```

```
Find scripts that generate random passwords meeting
complexity requirements.
```

### Finding Integration Patterns

#### API Authentication Patterns

```
Use find_integration_patterns to find integrations that implement
OAuth2 authentication with token refresh.
```

```
Find integrations that use API key authentication with
rate limiting and retry logic.
```

```
Search for integrations that implement certificate-based
authentication (mTLS).
```

#### Common Integration Types

```
Find integrations for SIEM platforms that fetch alerts
and update incident status.
```

```
Search for EDR integrations that support endpoint isolation,
file quarantine, and process termination.
```

```
Use find_integration_patterns to find ticketing system
integrations (ServiceNow, Jira, Zendesk patterns).
```

```
Find threat intelligence platform integrations that
query indicators and return enrichment data.
```

### Finding XQL Examples

#### Parsing Rules

```
Use find_xql_examples to find parsing rules that extract
authentication events from Windows Security logs.
```

```
Find XQL parsing rules for firewall logs that extract
source IP, destination IP, port, and action.
```

```
Search for parsing rules that handle syslog format with
timestamp extraction and normalization.
```

```
Find XQL examples for parsing JSON-formatted logs
with nested fields.
```

#### Modeling Rules

```
Use find_xql_examples with rule_type="modeling" to find rules
that map network events to XDM schema.
```

```
Find modeling rules that map authentication events
to xdm.auth and xdm.source.user fields.
```

```
Search for XQL modeling rules that handle process execution
events with command line parsing.
```

### Finding Classifier & Mapper Patterns

```
Use find_classifier_examples to find classifiers that
categorize events by severity and type.
```

```
Find incoming mappers that transform ServiceNow tickets
to XSOAR incident fields.
```

```
Search for outgoing mappers that sync incident updates
back to external ticketing systems.
```

---

## Content Development Prompts

### Creating New Playbooks

```
I need to create a playbook that:
1. Receives an alert with a suspicious IP address
2. Enriches the IP using VirusTotal and AbuseIPDB
3. If malicious, blocks the IP on the firewall
4. Creates a ticket in ServiceNow
5. Notifies the SOC team via Slack

First, use find_similar_playbooks to find similar patterns,
then create the playbook following the best practices from
the examples.
```

```
Create an employee offboarding playbook that:
1. Disables the user account in Active Directory
2. Revokes OAuth tokens in Okta
3. Removes from all security groups
4. Archives the user's mailbox
5. Generates an offboarding report

Search for similar identity management playbooks first.
```

### Creating New Scripts

```
I need a script that:
1. Takes a list of URLs as input
2. Extracts the domain from each URL
3. Checks if the domain is in our whitelist
4. Returns only the non-whitelisted domains

Use find_similar_scripts to find URL parsing examples,
then create the script.
```

```
Create a script that:
1. Accepts an email file (.eml) as input
2. Extracts all attachments
3. Calculates SHA256 hash of each attachment
4. Returns a table with filename, size, and hash

Search for email parsing scripts first.
```

### Creating New Integrations

```
I need to create an integration for the Acme Security API that:
1. Uses API key authentication (X-API-Key header)
2. Has commands for: get-alerts, update-alert, get-asset
3. Implements pagination for list commands
4. Handles rate limiting with exponential backoff

Use find_integration_patterns to find similar REST API
integrations, then scaffold using init_integration.
```

---

## Validation & Quality Prompts

### Pre-Commit Validation

```
Run validate_content and lint_content on Packs/MyPack.
Summarize any errors and suggest fixes based on similar
validated content in the index.
```

```
Format and validate my new playbook at
Packs/MyPack/Playbooks/MyPlaybook.yml.
If there are errors, search for similar working playbooks
and show me the correct structure.
```

### Documentation Generation

```
Generate documentation for my integration at
Packs/MyPack/Integrations/MyIntegration/MyIntegration.yml
using generate_docs. Compare the output with similar
integrations in the index to ensure completeness.
```

---

## Troubleshooting Prompts

### Finding Error Solutions

```
My playbook is failing with "Context data not found".
Search for playbooks that use similar context paths
and show me the correct syntax for accessing nested data.
```

```
My XQL parsing rule isn't extracting the timestamp correctly.
Find XQL examples that parse timestamps in ISO 8601 format
and show me the correct parse_timestamp syntax.
```

### Understanding Patterns

```
I don't understand how sub-playbooks pass data back to
the parent. Find playbooks that use sub-playbooks with
outputs and explain the pattern.
```

```
Show me how to implement a polling pattern in a playbook
that waits for an async operation to complete. Find examples
and explain the GenericPolling approach.
```

---

## Discovery Prompts

### Exploring Available Content

```
Use get_pattern_index_stats to show me what content
is available in the index.
```

```
Search for all playbooks related to "CrowdStrike" and
list them with their pack names.
```

```
Find all integrations that support the "fetch-incidents"
capability.
```

### Learning Best Practices

```
Find the highest-rated enrichment playbooks and explain
what patterns they use that I should follow.
```

```
Search for CommonPlaybooks and CommonScripts to understand
the recommended patterns for reusable content.
```

---

## Combined Workflow Prompts

### End-to-End Development

```
I want to create a complete phishing response pack. Please:

1. Use find_similar_playbooks to find phishing playbooks
   and analyze their structure
2. Use find_similar_scripts to find email parsing scripts
3. Create a new pack called "AcmePhishingResponse" using init_pack
4. Create the main playbook following the patterns found
5. Run format_content and validate_content
6. Generate documentation with generate_docs

Show me each step and the final structure.
```

### Migration & Modernization

```
I have an old playbook that uses deprecated commands.

1. Read the playbook at Packs/Legacy/Playbooks/OldPlaybook.yml
2. Search for modern playbooks that do similar things
3. Identify which commands need to be updated
4. Create a new version following current best practices
5. Validate the new playbook
```

---

## Tips for Effective Prompts

1. **Be specific about the use case** - "phishing with email analysis" is better than just "phishing"

2. **Request full content when needed** - Add "include_content=true" or "show the full YAML" to get complete examples

3. **Combine search with action** - First search for patterns, then use SDK tools to create content

4. **Specify the pack context** - Mention which pack you're working in for relevant suggestions

5. **Ask for explanations** - Request that the LLM explain patterns it finds, not just show them

6. **Iterate on results** - If the first search doesn't find what you need, try different keywords or related terms
