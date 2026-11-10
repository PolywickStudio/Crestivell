# Python API examples

Python 3.10 or later; no third-party packages needed. Run these commands from this directory. Examples use the current Crestivell server API and do not automatically retry signing or PIN failures.

## Connection and scopes

Set the server URL and credentials in your terminal or build-agent secret configuration. Use HTTPS with a trusted certificate for remote servers. These examples verify TLS and do not follow redirects. See the parent README for all environment settings, the explicit remote-HTTP opt-in, and the TLS-pinning limitation. No `.env` file is automatically loaded.

```powershell
$env:CRESTIVELL_URL = 'http://127.0.0.1:8787'
# Supply actual secrets through your secret manager; these are placeholders.
$env:CRESTIVELL_API_KEY = '<sign-scoped key>'
$env:CRESTIVELL_ADMIN_API_KEY = '<admin-scoped key>'
```

`sign` permits signing and public-certificate download. `admin` permits server management, but does not permit signing. `sign,admin` permits both; set the applicable environment variable for each example. Keys must be enabled and unexpired. Certificate scope and any bound user's role, enabled status and stored certificate assignments also apply. Maintenance mode and licensing may prevent signing.

## Signing

Discover permitted labels:

```powershell
python sign.py certificates
```

This Python upload example currently accepts EXEs only. The server REST route and
CrestivellCli upload-sign also accept DLL, MSI, MSIX, AppX, CAT and CAB in the
updated server build. See the server API documentation for the supported signing formats.

Upload a Windows PE EXE and save the signed copy without changing the input:

```powershell
python sign.py upload --file application.exe --output signed-application.exe --label release
signtool verify /pa /v signed-application.exe
```

Replace `release` with an enabled real certificate label. The server needs SignTool, CrestivellDigest.dll, a reachable callback URL, and an active licence. Output must not already exist. The returned artifact must be verified before publishing it.

Omit `--label` to use `CRESTIVELL_CERT_LABEL`. For digest signing, omit `--thumbprint` and `--filename` to use `CRESTIVELL_CERT_THUMBPRINT` and `CRESTIVELL_FILE_NAME`. Explicit options override environment defaults.

Sign a supplied SHA-256 digest:

```powershell
python sign.py digest --sha256 '<64 hexadecimal digits>' --thumbprint '<certificate fingerprint>' --filename application.exe --label release --output receipt.json
```

This returns a signature/receipt; it **does not embed an Authenticode signature** in an executable. A normal whole-file SHA-256 hash is not an Authenticode digest. Use upload signing or the desktop SignTool workflow for a signed Windows executable. The fingerprint must match the server's certificate.

## Administration

Read-only examples:

```powershell
python admin.py list users
python admin.py list keys
python admin.py list certificates
python admin.py list settings
python admin.py list logs
```

Explicit settings changes:

```powershell
python admin.py maintenance on   # Pause new and queued signing; administration stays available.
python admin.py maintenance off  # Resume signing, subject to licensing and permissions.
python admin.py swagger on       # Make Swagger documentation publicly visible.
python admin.py swagger off      # Disable Swagger documentation (default).
```

Settings updates send only the changed field. An admin key bound to a user requires an enabled Administrator account. These examples do not log in with browser sessions or manage authenticator setup.

Errors are printed to stderr with a nonzero exit status, including server error details. The examples do not print API credentials. Treat administration output and receipt files as potentially sensitive records.
