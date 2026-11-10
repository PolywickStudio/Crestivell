# Windows batch examples

Requires CMD and CrestivellCli.exe. All wrappers share `..\find-cli.cmd`. It checks an explicit `CRESTIVELL_CLI` override, then `..\..\CrestivellCli.exe` relative to this CMD directory, PATH, and standard Program Files installation locations. Paths are independent of the current working directory. A missing CLI returns exit code 2. Set `CRESTIVELL_CLI` to an executable path to override it (without surrounding quotes in the value). For MSI installations select the Client component to install the CLI.

Set connection settings in CMD or through your build system's secret store:

```bat
set "CRESTIVELL_URL=http://127.0.0.1:8787"
set "CRESTIVELL_API_KEY=<sign-scoped key>"
sign-file.cmd "application.exe" "signed-application.exe" "release"
sign-digest.cmd "<64 hex digits>" "application.exe" "release"
crestivell.cmd config --pretty
crestivell.cmd health
```

Use `call` when invoking these wrappers from another batch file, then check `errorlevel`. CLI exit codes are preserved. Use trusted HTTPS for remote servers. CMD applies its normal quoting and environment-expansion rules. Paths with spaces are supported.

The final label argument is optional: omit it to use `CRESTIVELL_CERT_LABEL`. Digest signing also inherits `CRESTIVELL_CERT_THUMBPRINT`; its filename remains an explicit argument. To override the thumbprint, use `crestivell.cmd sign --digest ... --name ... --thumbprint ...`. Connection, remote-HTTP and TLS-pin settings are handled by the CLI. Run `crestivell.cmd env --pretty` to inspect effective settings with the API key redacted. See the parent README for the full variable list; `.env` files are not automatically loaded.

Upload accepts the formats supported by the installed CLI/server. Verify signed outputs with SignTool. Digest signing writes a receipt to stdout without embedding a signature in a file. See the parent README for shared guidance.
