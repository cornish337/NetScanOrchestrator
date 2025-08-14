import argparse
from db.session import Base, engine


def migrate(_args: argparse.Namespace) -> None:
    """Run database migrations by creating all tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="netscan")
    subparsers = parser.add_subparsers(dest="command")

    migrate_parser = subparsers.add_parser("migrate", help="Initialize the database schema")
    migrate_parser.set_defaults(func=migrate)

    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
