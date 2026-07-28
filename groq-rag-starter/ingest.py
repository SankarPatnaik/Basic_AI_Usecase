import argparse

from app.vector_store import ingest_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into ChromaDB.")
    parser.add_argument("--data", default="data", help="Folder containing documents")
    parser.add_argument("--reset", action="store_true", help="Delete old vectors first")
    args = parser.parse_args()

    count = ingest_folder(args.data, reset=args.reset)
    print(f"Success: stored {count} chunks in ChromaDB.")


if __name__ == "__main__":
    main()
