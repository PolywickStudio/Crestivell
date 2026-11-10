// Node.js 22+; standard library only.
import { readFile, writeFile, lstat } from 'node:fs/promises';
import { basename, extname } from 'node:path';
import { randomUUID } from 'node:crypto';
const usage = `Usage:
  node sign.mjs certificates
  node sign.mjs upload <input.exe> <output.exe> [label]
  node sign.mjs digest <sha256> <thumbprint|-> <filename|-> <label|-> <receipt.json>
Use - for an environment default; upload label may also be omitted.`;
const args = process.argv.slice(2);
if (args.length === 0 || args[0] === '--help') { console.log(usage); process.exit(args.length ? 0 : 1); }
try {
  if (args[0] === 'upload' && args.length === 3) args.push('-');
  const counts = { certificates: 1, upload: 4, digest: 6 };
  if (args.length !== counts[args[0]]) throw new Error(usage);
  const fromEnvironment = (index, name) => {
    if (args[index] === '-') args[index] = process.env[name] || '';
    if (!args[index]) throw new Error(`Supply an explicit value or ${name}`);
  };
  if (args[0] === 'upload') fromEnvironment(3, 'CRESTIVELL_CERT_LABEL');
  if (args[0] === 'digest') {
    fromEnvironment(2, 'CRESTIVELL_CERT_THUMBPRINT');
    fromEnvironment(3, 'CRESTIVELL_FILE_NAME');
    fromEnvironment(4, 'CRESTIVELL_CERT_LABEL');
  }
  const rawUrl = process.env.CRESTIVELL_URL || 'http://127.0.0.1:8787';
  const url = new URL(rawUrl);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== '/')
    throw new Error('CRESTIVELL_URL must be a server base URL without credentials or a path');
  if (process.env.CRESTIVELL_TLS_FINGERPRINT)
    throw new Error('CRESTIVELL_TLS_FINGERPRINT is not supported by REST examples; use CrestivellCli for TLS pinning');
  if (url.protocol === 'http:' && !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) && process.env.CRESTIVELL_ALLOW_REMOTE_HTTP !== '1')
    throw new Error('Remote connections require HTTPS unless CRESTIVELL_ALLOW_REMOTE_HTTP=1');
  const key = process.env.CRESTIVELL_API_KEY || '';
  if (!key || /[\r\n]/.test(key)) throw new Error('Set CRESTIVELL_API_KEY');
  async function request(path, body, json = false) {
    const response = await fetch(new URL(path, url), {
      method: body === undefined ? 'GET' : 'POST', redirect: 'error',
      signal: AbortSignal.timeout(300000),
      headers: { Authorization: `Bearer ${key}`, Accept: 'application/json',
        ...(body !== undefined ? { 'Content-Type': json ? 'application/json' : 'application/octet-stream' } : {}) },
      body: json ? JSON.stringify(body) : body
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}: request rejected`);
    return response;
  }
  if (args[0] === 'certificates') {
    console.log(JSON.stringify(await (await request('/api/v1/certificates')).json(), null, 2));
  } else {
    let data, output;
    const destination = args[0] === 'upload' ? args[2] : args[5];
    try { await lstat(destination); throw new Error('Output already exists; choose a new path'); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (args[0] === 'upload') {
      const [, input, destination, label] = args;
      if (extname(input).toLowerCase() !== '.exe') throw new Error('This upload example accepts EXE files');
      const bytes = await readFile(input);
      const config = await (await request('/api/v1/configuration')).json();
      if (bytes.length > config.uploadLimitBytes) throw new Error('File exceeds server upload limit');
      const query = new URLSearchParams({ label, filename: basename(input) });
      const response = await request(`/api/v1/sign-file?${query}`, bytes);
      data = Buffer.from(await response.arrayBuffer());
      if (data.length < 2 || data[0] !== 77 || data[1] !== 90) throw new Error('Server did not return an executable');
      output = destination;
    } else {
      const [, sha256, thumbprint, filename, label, destination] = args;
      if (!/^[a-fA-F0-9]{64}$/.test(sha256)) throw new Error('SHA-256 must contain 64 hexadecimal digits');
      const response = await request('/api/v1/sign', { requestId: randomUUID(), certificateLabel: label,
        certificateThumbprint: thumbprint, algorithm: 'SHA256', sha256, fileName: filename }, true);
      data = JSON.stringify(await response.json(), null, 2) + '\n';
      output = destination;
    }
    // Exclusive creation avoids replacing an existing input or output file.
    await writeFile(output, data, { flag: 'wx' });
    console.log(`Saved ${output}`);
    console.log(args[0] === 'upload' ? 'Verify with: signtool verify /pa /v <output.exe>' : 'Digest receipt only; no embedded Authenticode signature was added.');
  }
} catch (error) {
  // Avoid exposing credentials or a URL supplied by the environment.
  console.error(error instanceof TypeError ? 'Connection failed; check URL, TLS trust and connectivity' : String(error.message).split(process.env.CRESTIVELL_API_KEY || '\0').join('[redacted]'));
  process.exitCode = 1;
}
