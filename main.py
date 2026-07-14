"""
main.py

Simple CLI entry point for manually testing AURA Shield against a single
prompt, without needing the Streamlit dashboard running.
"""
import argparse
import json
import logging
from app.storage.database import init_db
from app.models import IncomingRequest
from app.pipeline import process_request


def main():
    logging.basicConfig(level=logging.INFO)
    init_db()

    parser = argparse.ArgumentParser(description="Run a single prompt through AURA Shield")
    parser.add_argument("prompt", help="The user prompt to test")
    parser.add_argument("--source", default=None, help="Optional untrusted source content (document/tool output)")
    args = parser.parse_args()

    request = IncomingRequest(user_prompt=args.prompt, source_content=args.source)
    result = process_request(request)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
