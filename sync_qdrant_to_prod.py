#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Qdrant data from local to production
"""
from qdrant_client import QdrantClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local Qdrant (если запущен)
LOCAL_HOST = "localhost"
LOCAL_PORT = 6333

# Production Qdrant
PROD_HOST = "5.35.88.251"
PROD_PORT = 6333

print("=" * 80)
print("SYNC QDRANT: LOCAL → PRODUCTION")
print("=" * 80)

try:
    # Connect to local Qdrant
    print(f"\n1. Connecting to LOCAL Qdrant ({LOCAL_HOST}:{LOCAL_PORT})...")
    local_client = QdrantClient(host=LOCAL_HOST, port=LOCAL_PORT, timeout=5)

    # Get collections
    collections = local_client.get_collections()
    print(f"   ✅ Found {len(collections.collections)} collection(s)")

    for coll in collections.collections:
        print(f"     - {coll.name}: {coll.points_count} points")

    # Connect to production Qdrant
    print(f"\n2. Connecting to PRODUCTION Qdrant ({PROD_HOST}:{PROD_PORT})...")
    prod_client = QdrantClient(host=PROD_HOST, port=PROD_PORT, timeout=10)
    print("   ✅ Connected")

    # Sync each collection
    for coll in collections.collections:
        coll_name = coll.name
        print(f"\n3. Syncing collection '{coll_name}'...")

        # Get collection info
        coll_info = local_client.get_collection(coll_name)

        # Create collection on production
        print(f"   Creating collection on production...")
        prod_client.recreate_collection(
            collection_name=coll_name,
            vectors_config=coll_info.config.params.vectors
        )
        print("   ✅ Collection created")

        # Get all points from local
        print(f"   Fetching points from local...")
        points = []
        offset = None

        while True:
            result = local_client.scroll(
                collection_name=coll_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )

            points.extend(result[0])
            offset = result[1]

            if offset is None:
                break

        print(f"   ✅ Fetched {len(points)} points")

        # Upload points to production
        if points:
            print(f"   Uploading to production...")
            prod_client.upsert(
                collection_name=coll_name,
                points=points
            )
            print(f"   ✅ Uploaded {len(points)} points")

    print("\n" + "=" * 80)
    print("✅ SYNC COMPLETE!")
    print("=" * 80)

    # Verify
    print("\nVerification:")
    prod_collections = prod_client.get_collections()
    for coll in prod_collections.collections:
        print(f"  - {coll.name}: {coll.points_count} points")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

    print("\n" + "=" * 80)
    print("FALLBACK: Use snapshot transfer instead")
    print("=" * 80)
    print("\nSteps:")
    print("1. Create snapshot on local Qdrant:")
    print("   curl -X POST http://localhost:6333/collections/knowledge_sections/snapshots")
    print("")
    print("2. Download snapshot:")
    print("   curl http://localhost:6333/collections/knowledge_sections/snapshots/SNAPSHOT_NAME")
    print("        -o knowledge_sections.snapshot")
    print("")
    print("3. Upload to production:")
    print("   scp knowledge_sections.snapshot root@5.35.88.251:/tmp/")
    print("")
    print("4. Restore on production:")
    print("   curl -X PUT http://5.35.88.251:6333/collections/knowledge_sections/snapshots/recover")
    print("        -H 'Content-Type: multipart/form-data'")
    print("        -F 'snapshot=@/tmp/knowledge_sections.snapshot'")
