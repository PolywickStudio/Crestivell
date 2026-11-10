"""Admin-scope examples: inspect records and explicitly change server settings."""
import argparse
import json
import sys
from crestivell_api import CrestivellAPI


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="Read administration data")
    listing.add_argument("resource", choices=["users", "keys", "certificates", "settings", "logs", "licenses"])
    maintenance = commands.add_parser("maintenance", help="Pause or resume signing")
    maintenance.add_argument("state", choices=["on", "off"])
    swagger = commands.add_parser("swagger", help="Enable or disable public API documentation")
    swagger.add_argument("state", choices=["on", "off"])
    args = parser.parse_args()
    api = CrestivellAPI("CRESTIVELL_ADMIN_API_KEY")
    if args.command == "list":
        result = api.request("/admin/api/" + args.resource)
    else:
        setting = "maintenanceMode" if args.command == "maintenance" else "swaggerEnabled"
        # This endpoint uses string values, not JSON boolean values.
        result = api.request("/admin/api/settings", "PUT",
                             payload={setting: "true" if args.state == "on" else "false"})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
