"""Vector database setup script.

Initializes vector database (Pinecone or Weaviate) for the application.

Usage:
    python scripts/setup_vector_db.py --provider pinecone
    python scripts/setup_vector_db.py --provider weaviate
"""

import argparse
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_pinecone():
    """Set up Pinecone vector database."""
    from pinecone import Pinecone, ServerlessSpec

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("ERROR: PINECONE_API_KEY environment variable not set")
        sys.exit(1)

    pc = Pinecone(api_key=api_key)

    index_name = os.getenv("PINECONE_INDEX_NAME", "wafaa-knowledge")
    environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

    # Check if index exists
    existing_indexes = [index.name for index in pc.list_indexes()]

    if index_name in existing_indexes:
        print(f"Index '{index_name}' already exists")
        return

    # Create index
    print(f"Creating Pinecone index: {index_name}")
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI ada-002 dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=environment,
        ),
    )

    print(f"✓ Pinecone index '{index_name}' created successfully")


def setup_weaviate():
    """Set up Weaviate vector database."""
    import weaviate

    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    host = weaviate_url.replace("http://", "").split(":")[0]
    port = int(weaviate_url.split(":")[-1])

    client = weaviate.connect_to_local(host=host, port=port)

    # Create Knowledge class schema
    try:
        client.collections.create(
            name="Knowledge",
            properties=[
                {
                    "name": "text",
                    "dataType": ["text"],
                    "description": "The text content of the knowledge chunk",
                },
                {
                    "name": "client_id",
                    "dataType": ["text"],
                    "description": "The client/tenant ID",
                },
                {
                    "name": "document_type",
                    "dataType": ["text"],
                    "description": "Type of document (menu, faq, etc.)",
                },
                {
                    "name": "chunk_index",
                    "dataType": ["int"],
                    "description": "Index of the chunk within the document",
                },
            ],
            vectorizer_config=None,  # We provide our own vectors
        )
        print("✓ Weaviate 'Knowledge' collection created successfully")

    except Exception as e:
        if "already exists" in str(e).lower():
            print("'Knowledge' collection already exists")
        else:
            print(f"ERROR: {e}")
            sys.exit(1)

    client.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Set up vector database")
    parser.add_argument(
        "--provider",
        type=str,
        required=True,
        choices=["pinecone", "weaviate"],
        help="Vector database provider",
    )

    args = parser.parse_args()

    print(f"Setting up {args.provider}...")

    if args.provider == "pinecone":
        setup_pinecone()
    elif args.provider == "weaviate":
        setup_weaviate()

    print("Setup complete!")


if __name__ == "__main__":
    main()
