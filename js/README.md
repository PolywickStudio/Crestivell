# JavaScript examples

Requires Node.js 22 or later. No npm packages are required.
Set `CRESTIVELL_URL` and `CRESTIVELL_API_KEY`; see the parent README.
Omit the upload label or use `-` in a label, thumbprint or digest filename position to use `CRESTIVELL_CERT_LABEL`, `CRESTIVELL_CERT_THUMBPRINT` or `CRESTIVELL_FILE_NAME`. Explicit values take precedence. For example: `node sign.mjs digest '<64 hex digits>' - - - 'receipt.json'`. See the parent README for remote-HTTP and TLS-pin behavior; `.env` files are not automatically loaded.

```powershell
node sign.mjs certificates
node sign.mjs upload 'application.exe' 'signed-application.exe' 'release'
node sign.mjs digest '<64 hex digits>' '<certificate fingerprint>' 'application.exe' 'release' 'receipt.json'
node sign.mjs --help
```

Upload accepts EXE only. Verify the signed output with SignTool. Digest signing returns a receipt without modifying an executable. Errors return exit status 1.
