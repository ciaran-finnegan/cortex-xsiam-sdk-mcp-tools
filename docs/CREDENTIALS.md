# Credentials Configuration

The `demisto-sdk` requires credentials to interact with your XSIAM/XSOAR instance.

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `DEMISTO_BASE_URL` | Your XSIAM/XSOAR API URL |
| `DEMISTO_API_KEY` | API key with Instance Administrator role |
| `XSIAM_AUTH_ID` | Auth ID from the API key configuration |

> **Important:** Get the base URL from **Settings → Configurations → API Keys → Copy URL** (not the browser URL).

## Security guidance

- **Do not commit secrets** (API keys, tokens, client secrets) to git.
- **Avoid storing credentials directly in `.env` files.** Prefer an OS credential store or an encrypted secrets store and inject via environment variables at runtime.
- If you must use `.env` locally, ensure it is ignored by git, permissioned tightly, and treated as disposable.

## Storage options (examples)

### macOS Keychain

```bash
security add-generic-password -a "$USER" -s "demisto-url" -w "https://your-tenant.xdr.au.paloaltonetworks.com"
security add-generic-password -a "$USER" -s "demisto-api-key" -w "YOUR_API_KEY"
security add-generic-password -a "$USER" -s "demisto-auth-id" -w "YOUR_AUTH_ID"
```

```bash
export DEMISTO_BASE_URL="$(security find-generic-password -a "$USER" -s "demisto-url" -w)"
export DEMISTO_API_KEY="$(security find-generic-password -a "$USER" -s "demisto-api-key" -w)"
export XSIAM_AUTH_ID="$(security find-generic-password -a "$USER" -s "demisto-auth-id" -w)"
```

### Windows Credential Manager

```powershell
cmdkey /generic:demisto-url /user:demisto /pass:https://your-tenant.xdr.au.paloaltonetworks.com
cmdkey /generic:demisto-api-key /user:demisto /pass:YOUR_API_KEY
cmdkey /generic:demisto-auth-id /user:demisto /pass:YOUR_AUTH_ID
```

### Linux Secret Service (libsecret / GNOME Keyring)

```bash
secret-tool store --label="demisto-url" service demisto-url account "$USER" <<< "https://your-tenant.xdr.au.paloaltonetworks.com"
secret-tool store --label="demisto-api-key" service demisto-api-key account "$USER" <<< "YOUR_API_KEY"
secret-tool store --label="demisto-auth-id" service demisto-auth-id account "$USER" <<< "YOUR_AUTH_ID"
```

```bash
export DEMISTO_BASE_URL="$(secret-tool lookup service demisto-url account "$USER")"
export DEMISTO_API_KEY="$(secret-tool lookup service demisto-api-key account "$USER")"
export XSIAM_AUTH_ID="$(secret-tool lookup service demisto-auth-id account "$USER")"
```

### CI encrypted secrets (example)

Most CI systems provide an encrypted secret store. For GitHub Actions, see [encrypted secrets documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets).

```yaml
env:
  DEMISTO_BASE_URL: ${{ secrets.DEMISTO_BASE_URL }}
  DEMISTO_API_KEY: ${{ secrets.DEMISTO_API_KEY }}
  XSIAM_AUTH_ID: ${{ secrets.XSIAM_AUTH_ID }}
```

## Local development `.env` (not recommended)

If you must use a `.env` file locally:

- Keep it **out of git** (this repo’s `.gitignore` already ignores `.env`)
- Restrict permissions: `chmod 600 .env`
- Prefer `.env.example` in git with **placeholders only**

```bash
touch .env && chmod 600 .env
```

```bash
# .env (DO NOT COMMIT)
DEMISTO_BASE_URL=https://your-tenant.xdr.au.paloaltonetworks.com
DEMISTO_API_KEY=YOUR_API_KEY
XSIAM_AUTH_ID=YOUR_AUTH_ID
```

```bash
source .env
```

## Security Considerations for Remote Operations

### Production-Impacting Tools

The following tools can modify your XSIAM/XSOAR tenant and should be used with caution:

| Tool | Risk Level | What It Does |
|------|------------|--------------|
| `upload_content` | **HIGH** | Deploys content to your tenant - can overwrite existing content |
| `run_command` | **HIGH** | Executes commands directly on your tenant |
| `run_playbook` | **HIGH** | Triggers playbook automation |
| `download_content` | LOW | Downloads content from tenant (read-only) |
| `list_files` | LOW | Lists available content (read-only) |

### Recommendations

1. **Use separate credentials for development and production**
   - Create a dedicated API key for development with limited scope
   - Never use production credentials during content development

2. **Test in staging first**
   - Deploy and test content in a non-production environment
   - Validate behavior before production deployment

3. **Review before upload**
   - Always review generated or modified content before uploading
   - Use `validate_content` and `lint_content` before deployment

4. **Enable audit logging**
   - Configure audit logging in your XSIAM tenant
   - Monitor for unexpected API activity

5. **Principle of least privilege**
   - Request only the API permissions you need
   - Avoid using Instance Administrator keys for routine operations

### SSL Verification

SSL certificate verification is enabled by default for all remote operations. This protects your credentials from man-in-the-middle attacks.

**Do not disable SSL verification (`insecure` flag) unless:**
- You are using a self-signed certificate in a controlled environment
- You understand and accept the security risks
- You have set `acknowledge_insecure_risk: true` explicitly

If you need to use self-signed certificates, consider:
1. Adding the CA certificate to your system trust store
2. Setting `REQUESTS_CA_BUNDLE` to point to your certificate
3. Using a proper certificate from a trusted CA
