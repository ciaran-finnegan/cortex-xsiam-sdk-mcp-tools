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
- **Avoid storing credentials directly in `.env` files.** Use a secrets manager (1Password, Keychain/Credential Manager, AWS Secrets Manager, GitHub Secrets) and inject via environment variables at runtime.
- If you must use `.env` locally, ensure it is ignored by git, permissioned tightly, and treated as disposable.

## Recommended storage options

### 1Password CLI (recommended)

See [1Password CLI documentation](https://developer.1password.com/docs/cli/).

```bash
# macOS
brew install --cask 1password-cli

# Sign in (opens browser/biometric)
op signin
```

Create an item:

```bash
op item create \
  --category="API Credential" \
  --title="XSIAM API" \
  --vault="YourVault" \
  'url=https://your-tenant.xdr.au.paloaltonetworks.com' \
  'credential=YOUR_API_KEY' \
  'auth_id=YOUR_AUTH_ID'
```

Reference it from your shell profile:

```bash
export DEMISTO_BASE_URL="$(op read "op://YourVault/XSIAM API/url")"
export DEMISTO_API_KEY="$(op read "op://YourVault/XSIAM API/credential")"
export XSIAM_AUTH_ID="$(op read "op://YourVault/XSIAM API/auth_id")"
```

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

### AWS Secrets Manager

See [AWS Secrets Manager documentation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html).

```bash
aws secretsmanager create-secret --name demisto-sdk/credentials \
  --secret-string '{"url":"https://your-tenant.xdr.au.paloaltonetworks.com","api_key":"YOUR_API_KEY","auth_id":"YOUR_AUTH_ID"}'
```

```bash
export DEMISTO_CREDS="$(aws secretsmanager get-secret-value --secret-id demisto-sdk/credentials --query SecretString --output text)"
export DEMISTO_BASE_URL="$(echo "$DEMISTO_CREDS" | jq -r '.url')"
export DEMISTO_API_KEY="$(echo "$DEMISTO_CREDS" | jq -r '.api_key')"
export XSIAM_AUTH_ID="$(echo "$DEMISTO_CREDS" | jq -r '.auth_id')"
```

### GitHub Actions secrets

See [GitHub Actions encrypted secrets documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets).

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