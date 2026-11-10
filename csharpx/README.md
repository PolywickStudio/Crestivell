# C# scripting examples

This folder intentionally uses the requested name `csharpx`; the scripts use the `.csx` extension.
Requires a separately installed .NET SDK and the `dotnet-script` tool. No script NuGet packages are needed.
Set `CRESTIVELL_URL` and `CRESTIVELL_API_KEY`; see the parent README.
Omit the upload label or use `-` in a label, thumbprint or digest filename position to use `CRESTIVELL_CERT_LABEL`, `CRESTIVELL_CERT_THUMBPRINT` or `CRESTIVELL_FILE_NAME`. Explicit values take precedence. For example: `dotnet script sign.csx -- digest '<64 hex digits>' - - - 'receipt.json'`. See the parent README for remote-HTTP and TLS-pin behavior; `.env` files are not automatically loaded.

```powershell
dotnet script sign.csx -- certificates
dotnet script sign.csx -- upload 'application.exe' 'signed-application.exe' 'release'
dotnet script sign.csx -- digest '<64 hex digits>' '<certificate fingerprint>' 'application.exe' 'release' 'receipt.json'
dotnet script sign.csx -- --help
```

Upload accepts EXE only. Verify the signed output with SignTool. Digest signing returns a receipt without modifying an executable. Errors return exit status 1.
