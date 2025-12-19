# Credentials Configuration

The `demisto-sdk` requires credentials to interact with your XSIAM/XSOAR instance.

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `DEMISTO_BASE_URL` | Your XSIAM/XSOAR API URL |
| `DEMISTO_API_KEY` | API key with Instance Administrator role |
| `XSIAM_AUTH_ID` | Auth ID from the API key configuration |

> **Important:** Get the base URL from **Settings → Configurations → API Keys → Copy URL** (not the browser URL).

## Secure Storage Options

**Avoid storing credentials directly in `.env` files** as these can be accidentally committed to version control.

### 1Password CLI (Recommended)

Install and configure the [1Password CLI](https://developer.1password.com/docs/cli/):

```bash
# macOS
brew install --cask 1password-cli

# Sign in (opens browser/biometric)
op signin
```

Create an API credential item:

```bash
op item create \
  --category="API Credential" \
  --title="XSIAM API" \
  --vault="YourVault" \
  'url=https://your-instance.xdr.au.paloaltonetworks.com' \
  'credential=your-api-key' \
  'auth_id=your-auth-id'
```

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# XSIAM credentials from 1Password
export DEMISTO_BASE_URL=$(op read "op://YourVault/XSIAM API/url")
export DEMISTO_API_KEY=$(op read "op://YourVault/XSIAM API/credential")
export XSIAM_AUTH_ID=$(op read "op://YourVault/XSIAM API/auth_id")
```

### macOS Keychain

```bash
# Store credentials
security add-generic-password -a "$USER" -s "demisto-api-key" -w "your-api-key"
security add-generic-password -a "$USER" -s "demisto-url" -w "https://your-instance.xdr.au.paloaltonetworks.com"
security add-generic-password -a "$USER" -s "demisto-auth-id" -w "your-auth-id"
```

Add to `~/.zshrc`:

```bash
export DEMISTO_BASE_URL=$(security find-generic-password -a "$USER" -s "demisto-url" -w)
export DEMISTO_API_KEY=$(security find-generic-password -a "$USER" -s "demisto-api-key" -w)
export XSIAM_AUTH_ID=$(security find-generic-password -a "$USER" -s "demisto-auth-id" -w)
```

### Windows Credential Manager

```powershell
# Store credentials (PowerShell)
cmdkey /generic:demisto-api-key /user:demisto /pass:your-api-key
cmdkey /generic:demisto-url /user:demisto /pass:https://your-instance.xdr.au.paloaltonetworks.com
cmdkey /generic:demisto-auth-id /user:demisto /pass:your-auth-id
```

### AWS Secrets Manager

```bash
# Store secret
aws secretsmanager create-secret --name demisto-sdk/credentials \
  --secret-string '{"url":"https://your-instance.xdr.au.paloaltonetworks.com","api_key":"your-api-key","auth_id":"your-auth-id"}'

# Retrieve (add to shell profile)
export DEMISTO_CREDS=$(aws secretsmanager get-secret-value --secret-id demisto-sdk/credentials --query SecretString --output text)
export DEMISTO_BASE_URL=$(echo $DEMISTO_CREDS | jq -r '.url')
export DEMISTO_API_KEY=$(echo $DEMISTO_CREDS | jq -r '.api_key')
export XSIAM_AUTH_ID=$(echo $DEMISTO_CREDS | jq -r '.auth_id')
```

See [AWS Secrets Manager documentation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html).

### GitHub Actions

Use [encrypted secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets):

```yaml
env:
  DEMISTO_BASE_URL: ${{ secrets.DEMISTO_BASE_URL }}
  DEMISTO_API_KEY: ${{ secrets.DEMISTO_API_KEY }}
  XSIAM_AUTH_ID: ${{ secrets.XSIAM_AUTH_ID }}
```

### Environment File (Less Secure)

If you must use a `.env` file for local development:

1. **Never commit `.env` to version control** — ensure it's in `.gitignore`
2. Create with restricted permissions:

```bash
touch .env && chmod 600 .env
```

```bash
# .env (DO NOT COMMIT)
DEMISTO_BASE_URL=https://your-instance.xdr.au.paloaltonetworks.com
DEMISTO_API_KEY=your-api-key
XSIAM_AUTH_ID=your-auth-id
```

Load with:
```bash
source .env  # Or use direnv, dotenv, etc.
```

