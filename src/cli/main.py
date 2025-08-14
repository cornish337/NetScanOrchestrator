"""Command line interface for NetScanOrchestrator."""
import argparse

from ..ip_handler import read_ips_from_file
from ..db import repository as db_repo


def ingest_command(file_path: str) -> None:
    """Ingest targets from a file into the in-memory repository."""
    ips = read_ips_from_file(file_path)
    if not ips:
        print("No IPs to ingest.")
        return
    count = db_repo.add_targets(ips)
    print(f"Ingested {count} target(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="NetScanOrchestrator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest targets from a file")
    ingest_parser.add_argument("file", help="Path to file containing IPs or hostnames")

    args = parser.parse_args()

    if args.command == "ingest":
        ingest_command(args.file)


if __name__ == "__main__":
    main()
