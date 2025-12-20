# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Use GitHub's private vulnerability reporting feature, or
3. Email the maintainers directly (see repository contacts)

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Resolution Timeline**: Depends on severity
  - Critical: 7 days
  - High: 30 days
  - Medium: 90 days
  - Low: Best effort

## Security Model

This MCP server operates with the following security considerations:

### Trust Boundaries

1. **MCP Client**: Trusted to enforce access control and user authentication
2. **demisto-sdk**: Trusted external binary, validated before execution
3. **Content Repository**: Semi-trusted, path traversal protections applied
4. **XSIAM/XSOAR API**: External service, credentials must be secured

### Security Features

- **Path Traversal Protection**: All file access validates paths stay within content_root
- **Binary Validation**: Only approved SDK binary names can be executed
- **Input Validation**: All tool arguments validated before subprocess execution
- **Symlink Protection**: Symlinks blocked by default during indexing
- **SSL Verification**: Enabled by default, explicit acknowledgment required to disable

### Production-Impacting Tools

The following tools can modify your XSIAM/XSOAR tenant:

| Tool | Risk | Description |
|------|------|-------------|
| `upload_content` | HIGH | Deploys content to your tenant |
| `run_command` | HIGH | Executes arbitrary commands on tenant |
| `run_playbook` | HIGH | Triggers automation workflows |

**Recommendations:**
- Use separate API credentials for development and production
- Test content in staging environments before production
- Review all content before deployment
- Enable audit logging in your XSIAM tenant

## Best Practices

### Credential Security

1. **Never commit credentials** to version control
2. **Use credential helpers** (macOS Keychain, Windows Credential Manager)
3. **Use short-lived API keys** when possible
4. **Rotate credentials** regularly
5. **Use least-privilege** API permissions

See [docs/CREDENTIALS.md](docs/CREDENTIALS.md) for secure credential configuration.

### Network Security

1. **SSL verification is enabled by default** - Do not disable in production
2. **Use VPN or private network** when connecting to tenant
3. **Monitor API key usage** in XSIAM settings

### Runtime Security

1. **Never run this tool with elevated privileges** unless absolutely necessary
2. **Review uploaded content** before deploying to production tenants
3. **Keep dependencies updated** - Check for security advisories regularly

## Known Limitations

1. **No built-in authentication**: The MCP server relies on the MCP client for access control
2. **Subprocess execution**: Commands are executed with the same privileges as the MCP server
3. **Local storage**: ChromaDB stores pattern data locally without encryption

## Changelog

### v0.2.0
- Added path traversal protection
- Added binary execution validation
- Added input validation for all tool handlers
- Added symlink protection for indexing
- Added SSL verification acknowledgment requirement
- Relative paths stored in pattern database
