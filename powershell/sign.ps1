# PowerShell 7+; standard library only. Run Get-Help ./sign.ps1 for parameters.
[CmdletBinding()]
param(
    [ValidateSet('certificates','upload','digest')][string]$Command = 'certificates',
    [string]$File, [string]$Output, [string]$Label = $env:CRESTIVELL_CERT_LABEL,
    [string]$Sha256, [string]$Thumbprint = $env:CRESTIVELL_CERT_THUMBPRINT, [string]$FileName = $env:CRESTIVELL_FILE_NAME,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($Help) { Write-Output 'sign.ps1 certificates | upload -File <exe> -Output <exe> -Label <label> | digest -Sha256 <hex> -Thumbprint <fingerprint> -FileName <name> -Label <label> -Output <receipt.json>'; exit 0 }
$client = $null
try {
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 or later is required (pwsh.exe).' }
    $base = if ($env:CRESTIVELL_URL) { $env:CRESTIVELL_URL } else { 'http://127.0.0.1:8787' }
    $uri = [uri]$base
    if (-not $uri.IsAbsoluteUri -or $uri.Scheme -notin @('http','https') -or $uri.UserInfo -or $uri.Query -or $uri.Fragment -or $uri.AbsolutePath -ne '/') { throw 'CRESTIVELL_URL must be a server base URL without credentials or a path' }
    if ($env:CRESTIVELL_TLS_FINGERPRINT) { throw 'CRESTIVELL_TLS_FINGERPRINT is not supported by REST examples; use CrestivellCli for TLS pinning' }
    if ($uri.Scheme -eq 'http' -and $uri.Host -notin @('localhost','127.0.0.1','[::1]','::1') -and $env:CRESTIVELL_ALLOW_REMOTE_HTTP -ne '1') { throw 'Remote connections require HTTPS unless CRESTIVELL_ALLOW_REMOTE_HTTP=1' }
    if (-not $env:CRESTIVELL_API_KEY -or $env:CRESTIVELL_API_KEY -match '[\r\n]') { throw 'Set CRESTIVELL_API_KEY' }
    $handler = [System.Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $client = [System.Net.Http.HttpClient]::new($handler)
    $client.BaseAddress = $uri
    $client.Timeout = [TimeSpan]::FromSeconds(300)
    $client.DefaultRequestHeaders.Authorization = [System.Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer', $env:CRESTIVELL_API_KEY)
    function Invoke-Api([string]$Path, [byte[]]$Body, [string]$ContentType = 'application/octet-stream') {
        $message = [System.Net.Http.HttpRequestMessage]::new($(if ($null -eq $Body) { 'GET' } else { 'POST' }), $Path)
        try {
            if ($null -ne $Body) {
                $message.Content = [System.Net.Http.ByteArrayContent]::new($Body)
                $message.Content.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::new($ContentType)
            }
            $response = $client.SendAsync($message).GetAwaiter().GetResult()
            try {
                if (-not $response.IsSuccessStatusCode) { throw "HTTP $([int]$response.StatusCode): request rejected" }
                return ,$response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
            } finally { $response.Dispose() }
        } finally { $message.Dispose() }
    }
    if ($Command -eq 'certificates') {
        [Text.Encoding]::UTF8.GetString((Invoke-Api '/api/v1/certificates' $null))
    } else {
        if (-not $Output -or -not $Label) { throw 'Output and Label are required' }
        if ([IO.File]::Exists($Output)) { throw 'Output already exists; choose a new path' }
        if ($Command -eq 'upload') {
            if (-not $File -or [IO.Path]::GetExtension($File) -ine '.exe') { throw 'This upload example accepts EXE files' }
            $body = [IO.File]::ReadAllBytes($ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($File))
            $config = [Text.Encoding]::UTF8.GetString((Invoke-Api '/api/v1/configuration' $null)) | ConvertFrom-Json
            if ($body.Length -gt $config.uploadLimitBytes) { throw 'File exceeds server upload limit' }
            $path = '/api/v1/sign-file?label=' + [uri]::EscapeDataString($Label) + '&filename=' + [uri]::EscapeDataString([IO.Path]::GetFileName($File))
            $result = Invoke-Api $path $body
            if ($result.Length -lt 2 -or $result[0] -ne 77 -or $result[1] -ne 90) { throw 'Server did not return an executable' }
        } else {
            if ($Sha256 -notmatch '^[a-fA-F0-9]{64}$' -or -not $Thumbprint -or -not $FileName) { throw 'Supply a 64-digit SHA256, Thumbprint and FileName' }
            $body = @{ requestId = [guid]::NewGuid().ToString(); certificateLabel = $Label; certificateThumbprint = $Thumbprint; algorithm = 'SHA256'; sha256 = $Sha256; fileName = $FileName } | ConvertTo-Json -Compress
            $result = Invoke-Api '/api/v1/sign' ([Text.Encoding]::UTF8.GetBytes($body)) 'application/json'
        }
        $destination = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output)
        $stream = [IO.File]::Open($destination, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
        try { $stream.Write($result, 0, $result.Length) } finally { $stream.Dispose() }
        Write-Output "Saved $Output"
        if ($Command -eq 'upload') { Write-Output 'Verify with: signtool verify /pa /v <output.exe>' }
        else { Write-Output 'Digest receipt only; no embedded Authenticode signature was added.' }
    }
} catch {
    $message = $_.Exception.Message
    if ($env:CRESTIVELL_API_KEY) { $message = $message.Replace($env:CRESTIVELL_API_KEY, '[redacted]') }
    [Console]::Error.WriteLine($message)
    exit 1
} finally { if ($client) { $client.Dispose() } }
