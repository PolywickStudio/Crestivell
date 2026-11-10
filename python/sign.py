"""Signing-scope examples: upload an EXE, sign a SHA-256 digest, or list certificates."""
import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from crestivell_api import CrestivellAPI


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("certificates")
    upload = commands.add_parser("upload", help="Download a signed copy of a PE EXE")
    upload.add_argument("--file", type=Path, required=True)
    upload.add_argument("--output", type=Path, required=True)
    upload.add_argument("--label", default=os.environ.get("CRESTIVELL_CERT_LABEL"))
    digest = commands.add_parser("digest", help="Sign a digest; does not modify or sign an executable")
    digest.add_argument("--sha256", required=True)
    digest.add_argument("--label", default=os.environ.get("CRESTIVELL_CERT_LABEL"))
    digest.add_argument("--thumbprint", default=os.environ.get("CRESTIVELL_CERT_THUMBPRINT"))
    digest.add_argument("--filename", default=os.environ.get("CRESTIVELL_FILE_NAME"))
    digest.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    api = CrestivellAPI()
    if args.command == "certificates":
        print(json.dumps(api.request("/api/v1/certificates"), indent=2))
        return
    if not args.label:
        raise ValueError("Supply --label or CRESTIVELL_CERT_LABEL")
    if args.command == "digest" and (not args.thumbprint or not args.filename):
        raise ValueError("Supply --thumbprint and --filename, or CRESTIVELL_CERT_THUMBPRINT and CRESTIVELL_FILE_NAME")
    if args.output.exists():
        raise ValueError("Output already exists; choose a new path")
    if args.command == "upload":
        if args.file.suffix.lower() != ".exe":
            raise ValueError("Upload signing supports PE EXE files")
        data = args.file.read_bytes()
        configuration = api.request("/api/v1/configuration")
        if len(data) > configuration["uploadLimitBytes"]:
            raise ValueError("File exceeds the server upload limit")
        result = api.request("/api/v1/sign-file", "POST", raw=data,
                             query={"label": args.label, "filename": args.file.name})
        if not isinstance(result, bytes) or not result.startswith(b"MZ"):
            raise RuntimeError("Server did not return an executable")
    else:
        if len(args.sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in args.sha256):
            raise ValueError("SHA-256 must contain 64 hexadecimal digits")
        result = api.request("/api/v1/sign", "POST", payload={
            "requestId": str(uuid.uuid4()), "certificateLabel": args.label,
            "certificateThumbprint": args.thumbprint, "algorithm": "SHA256",
            "sha256": args.sha256, "fileName": args.filename})
        result = (json.dumps(result, indent=2) + "\n").encode("utf-8")
    with args.output.open("xb") as output:
        output.write(result)
    print(f"Saved {args.output}")
    if args.command == "upload":
        print("Verify the downloaded EXE with: signtool verify /pa /v <output-file>")
    else:
        print("Digest receipt only: no embedded Authenticode signature was added to a file.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
