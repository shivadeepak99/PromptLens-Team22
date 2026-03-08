"""Simple ingestion script to load JSON datasets into MongoDB.

Usage:
    python ingest_to_mongodb.py <path-to-json> [--uri mongodb://localhost:27017] [--db promptlens] [--collection raw]

The script streams the input file line-by-line to avoid loading large JSON files into memory,
parses each line as a JSON object and inserts batches into MongoDB using bulk operations.
"""

import argparse
import json
import sys
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest a JSON log file into MongoDB")
    parser.add_argument("input", help="Path to the newline-delimited JSON file")
    parser.add_argument("--uri", default="mongodb://localhost:27017", help="MongoDB connection URI")
    parser.add_argument("--db", default="promptlens", help="Database name")
    parser.add_argument("--collection", default="raw", help="Collection name")
    parser.add_argument("--batch", type=int, default=1000, help="Bulk insert batch size")
    return parser.parse_args()


def main():
    args = parse_args()
    client = MongoClient(args.uri)
    db = client[args.db]
    coll = db[args.collection]

    print(f"Ingesting {args.input} to {args.uri}/{args.db}.{args.collection}")
    batch = []
    count = 0
    with open(args.input, "r", encoding="utf-8") as f:
        # determine whether file is a JSON array or newline-delimited
        first = f.read(1)
        f.seek(0)
        if first == "[":
            # load entire array; use json.load so we don't convert line-by-line incorrectly
            try:
                docs = json.load(f)
            except json.JSONDecodeError:
                docs = []
            for doc in tqdm(docs, desc="iterating array"):
                if not isinstance(doc, dict):
                    continue
                batch.append(doc)
                if len(batch) >= args.batch:
                    try:
                        coll.insert_many(batch, ordered=False)
                    except BulkWriteError as bwe:
                        print("Bulk write error", bwe.details, file=sys.stderr)
                    count += len(batch)
                    batch = []
        else:
            for line in tqdm(f, desc="reading lines"):
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    # skip invalid lines
                    continue
                batch.append(doc)
                if len(batch) >= args.batch:
                    try:
                        coll.insert_many(batch, ordered=False)
                    except BulkWriteError as bwe:
                        # ignore duplicates or write errors
                        print("Bulk write error", bwe.details, file=sys.stderr)
                    count += len(batch)
                    batch = []
    # insert remaining
    if batch:
        try:
            coll.insert_many(batch, ordered=False)
            count += len(batch)
        except BulkWriteError as bwe:
            print("Bulk write error", bwe.details, file=sys.stderr)
    print(f"Inserted ~{count} documents")


if __name__ == "__main__":
    main()

