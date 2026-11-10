# PowerShell examples

Requires PowerShell 7 or later (`pwsh.exe`), without extra modules.
Set `CRESTIVELL_URL` and `CRESTIVELL_API_KEY`; see the parent README.
Omit `-Label`, `-Thumbprint` or `-FileName` to use `CRESTIVELL_CERT_LABEL`, `CRESTIVELL_CERT_THUMBPRINT` or `CRESTIVELL_FILE_NAME`, respectively. Explicit parameters take precedence. The latter two apply to digest signing. See the parent README for remote-HTTP and TLS-pin behavior; `.env` files are not automatically loaded.
Run these commands in PowerShell 7:

```powershell
./sign.ps1 certificates
./sign.ps1 upload -File 'application.exe' -Output 'signed-application.exe' -Label 'release'
./sign.ps1 digest -Sha256 '<64 hex digits>' -Thumbprint '<certificate fingerprint>' -FileName 'application.exe' -Label 'release' -Output 'receipt.json'
./sign.ps1 -Help
```

Follow your organization's script execution policy. Upload accepts EXE only. Verify the signed output with SignTool. Digest signing returns a receipt without modifying an executable. Errors return exit status 1.
