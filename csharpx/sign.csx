// Run with dotnet-script; uses framework libraries only.
using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

var usage = "dotnet script sign.csx -- certificates | upload <input.exe> <output.exe> [label] | digest <sha256> <thumbprint|-> <filename|-> <label|-> <receipt.json> (- uses environment default)";
var arguments = Args.ToArray();
if (arguments.Length == 0 || arguments[0] == "--help") { Console.WriteLine(usage); Environment.Exit(arguments.Length == 0 ? 1 : 0); }
try {
    var command = arguments[0];
    if (command == "upload" && arguments.Length == 3) arguments = arguments.Concat(new[] { "-" }).ToArray();
    if (arguments.Length != (command == "certificates" ? 1 : command == "upload" ? 4 : command == "digest" ? 6 : -1)) throw new Exception(usage);
    void FromEnvironment(int index, string name) {
        if (arguments[index] == "-") arguments[index] = Environment.GetEnvironmentVariable(name) ?? "";
        if (string.IsNullOrEmpty(arguments[index])) throw new Exception("Supply an explicit value or " + name);
    }
    if (command == "upload") FromEnvironment(3, "CRESTIVELL_CERT_LABEL");
    if (command == "digest") {
        FromEnvironment(2, "CRESTIVELL_CERT_THUMBPRINT");
        FromEnvironment(3, "CRESTIVELL_FILE_NAME");
        FromEnvironment(4, "CRESTIVELL_CERT_LABEL");
    }
    var rawUrl = Environment.GetEnvironmentVariable("CRESTIVELL_URL");
    var url = new Uri(string.IsNullOrEmpty(rawUrl) ? "http://127.0.0.1:8787" : rawUrl);
    if ((url.Scheme != "http" && url.Scheme != "https") || url.UserInfo != "" || url.Query != "" || url.Fragment != "" || url.AbsolutePath != "/")
        throw new Exception("CRESTIVELL_URL must be a server base URL without credentials or a path");
    if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("CRESTIVELL_TLS_FINGERPRINT"))) throw new Exception("CRESTIVELL_TLS_FINGERPRINT is not supported by REST examples; use CrestivellCli for TLS pinning");
    if (url.Scheme == "http" && url.Host != "localhost" && url.Host != "127.0.0.1" && url.Host != "[::1]" && Environment.GetEnvironmentVariable("CRESTIVELL_ALLOW_REMOTE_HTTP") != "1") throw new Exception("Remote connections require HTTPS unless CRESTIVELL_ALLOW_REMOTE_HTTP=1");
    var key = Environment.GetEnvironmentVariable("CRESTIVELL_API_KEY") ?? "";
    if (key.Length == 0 || key.Contains("\r") || key.Contains("\n")) throw new Exception("Set CRESTIVELL_API_KEY");
    using (var handler = new HttpClientHandler { AllowAutoRedirect = false })
    using (var client = new HttpClient(handler) { BaseAddress = url, Timeout = TimeSpan.FromSeconds(300) }) {
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", key);
        async Task<byte[]> Request(string path, byte[] body = null, string contentType = "application/octet-stream") {
            using (var message = new HttpRequestMessage(body == null ? HttpMethod.Get : HttpMethod.Post, path)) {
                if (body != null) { message.Content = new ByteArrayContent(body); message.Content.Headers.ContentType = new MediaTypeHeaderValue(contentType); }
                using (var response = await client.SendAsync(message)) {
                    if (!response.IsSuccessStatusCode) throw new Exception("HTTP " + (int)response.StatusCode + ": request rejected");
                    return await response.Content.ReadAsByteArrayAsync();
                }
            }
        }
        if (command == "certificates") Console.WriteLine(Encoding.UTF8.GetString(await Request("/api/v1/certificates")));
        else {
            byte[] result;
            var output = command == "upload" ? arguments[2] : arguments[5];
            if (File.Exists(output)) throw new Exception("Output already exists; choose a new path");
            if (command == "upload") {
                if (!string.Equals(Path.GetExtension(arguments[1]), ".exe", StringComparison.OrdinalIgnoreCase)) throw new Exception("This upload example accepts EXE files");
                var bytes = File.ReadAllBytes(arguments[1]);
                using (var config = JsonDocument.Parse(await Request("/api/v1/configuration"))) {
                    if (bytes.LongLength > config.RootElement.GetProperty("uploadLimitBytes").GetInt64()) throw new Exception("File exceeds server upload limit");
                }
                result = await Request("/api/v1/sign-file?label=" + Uri.EscapeDataString(arguments[3]) + "&filename=" + Uri.EscapeDataString(Path.GetFileName(arguments[1])), bytes);
                if (result.Length < 2 || result[0] != 77 || result[1] != 90) throw new Exception("Server did not return an executable");
            } else {
                if (arguments[1].Length != 64 || !arguments[1].All(Uri.IsHexDigit)) throw new Exception("SHA-256 must contain 64 hexadecimal digits");
                var json = JsonSerializer.Serialize(new { requestId = Guid.NewGuid().ToString(), certificateLabel = arguments[4], certificateThumbprint = arguments[2], algorithm = "SHA256", sha256 = arguments[1], fileName = arguments[3] });
                result = await Request("/api/v1/sign", Encoding.UTF8.GetBytes(json), "application/json");
            }
            using (var stream = new FileStream(output, FileMode.CreateNew, FileAccess.Write)) { stream.Write(result, 0, result.Length); }
            Console.WriteLine("Saved " + output);
            Console.WriteLine(command == "upload" ? "Verify with: signtool verify /pa /v <output.exe>" : "Digest receipt only; no embedded Authenticode signature was added.");
        }
    }
} catch (Exception error) {
    var key = Environment.GetEnvironmentVariable("CRESTIVELL_API_KEY");
    var message = error is HttpRequestException || error is UriFormatException ? "Connection failed; check URL, TLS trust and connectivity" : error.Message;
    Console.Error.WriteLine(string.IsNullOrEmpty(key) ? message : message.Replace(key, "[redacted]"));
    Environment.Exit(1);
}
