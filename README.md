# Crestivell examples

| Folder | Requirements | Examples |
| --- | --- | --- |
| python | Python 3.10+; standard library | Certificates, EXE upload signing, digest signing, administration |
| cmd | Windows CMD and CrestivellCli.exe | CLI wrapper, upload signing, digest signing |
| powershell | PowerShell 7+ (pwsh); standard library | Certificates, EXE upload signing, digest signing |
| csharpx | .NET SDK and dotnet-script | C# scripts (.csx): certificates, EXE upload signing, digest signing |
| js | Node.js 22+; standard library | Certificates, EXE upload signing, digest signing |

The MSI installs this layout under `%ProgramFiles%\PolywickStudio\Crestivell\examples`, when the checked-by-default **Crestivell Client Examples** option is selected. Uncheck it to omit all examples. Language runtimes and dotnet-script are not bundled. CMD examples additionally require the Client component (CrestivellCli.exe), or a separately supplied CLI executable.

Set `CRESTIVELL_URL` (default `http://127.0.0.1:8787`) and `CRESTIVELL_API_KEY` through the terminal or your build system's secret store. Use a sign-scoped key with access to the selected certificate. Python administration uses `CRESTIVELL_ADMIN_API_KEY` separately. Never commit actual credentials.

The REST examples require trusted HTTPS for remote connections by default, retain TLS verification, reject redirects, and do not retry signing failures. Upload examples preserve the input and create a new output file; they currently accept EXE only. The CLI supports additional upload formats. Verify downloaded artifacts with `signtool verify /pa /v` before publishing. A digest receipt does not embed an Authenticode signature, and a whole-file hash is not an Authenticode digest.

## Environment settings

All examples read the environment of the process that launches them. They do not automatically load `.env` files. Saving a file in the client Environment wizard does not activate it for these scripts; **Apply connection** affects only the GUI session. Set variables in your terminal or build-agent configuration before launching an example. `CRESTIVELL_SERVER_*` settings configure the server, not these clients.

| Variable | Behavior |
| --- | --- |
| `CRESTIVELL_URL` | Server base URL; unset or empty uses `http://127.0.0.1:8787`. |
| `CRESTIVELL_API_KEY` | Signing credential. |
| `CRESTIVELL_CERT_LABEL` | Default signing label; an explicit argument takes precedence. |
| `CRESTIVELL_CERT_THUMBPRINT` | Default digest certificate thumbprint; an explicit argument takes precedence. |
| `CRESTIVELL_FILE_NAME` | Default digest filename in REST examples. CMD/CLI digest commands still require a filename argument. Uploads use the actual input filename. |
| `CRESTIVELL_ALLOW_REMOTE_HTTP` | Only the exact value `1` permits remote HTTP, which transmits credentials without TLS. Prefer HTTPS. |
| `CRESTIVELL_TLS_FINGERPRINT` | Supported through CMD/CLI. REST examples stop before sending requests when this is set; use the CLI for pinned TLS, or clear it to use normal certificate validation. |
| `CRESTIVELL_ADMIN_API_KEY` | Python `admin.py` credential, separate from the signing key. |
| `CRESTIVELL_CLI` | Optional CLI executable override for CMD wrappers. |

Python and PowerShell use environment defaults when their corresponding options are omitted. JavaScript and C# allow the upload label to be omitted; use `-` in a label, thumbprint or digest filename position to select its environment default. CMD signing wrappers allow the label argument to be omitted and retain the CLI's environment defaults. The CLI may select the sole eligible certificate for uploads when no label is configured.

Choose an output location you can write to, such as your build workspace. Do not write signed files into Program Files. Run commands from the relevant language folder; see each README for usage.

`find-cli.cmd` resolves the CLI using `CRESTIVELL_CLI`, then `..\CrestivellCli.exe` relative to this examples folder, PATH, and standard installation locations.

## Testing the examples

Run `python tests/example-environment-tests.py` from this repository. The tests use local mock servers and synthetic credentials; they do not contact a signing server or produce genuinely signed files. Python is required. JavaScript, PowerShell and C# checks run when their runtimes are available; unavailable runtimes are reported as skipped. For CMD checks on Windows, set `CRESTIVELL_CLI` to the installed CLI executable or put it on PATH.
