# Qdrant Search Patterns

## Basic Semantic Search

```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
client = QdrantClient(host="localhost", port=6333)

query = "What do I know about my family?"
vector = model.encode(query).tolist()

results = client.search(
    collection_name="lumi_session_archive",
    query_vector=vector,
    limit=5,
    with_payload=True
)

for r in results:
    print(f"[{r.score:.3f}] {r.payload.get('source')}: {r.payload.get('text', '')[:200]}")
```

## Filtered Search

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Only lorebook entries
results = client.search(
    collection_name="lumi_session_archive",
    query_vector=vector,
    query_filter=Filter(
        must=[FieldCondition(key="type", match=MatchValue(value="lorebook"))]
    ),
    limit=5
)

# Only from a specific source
results = client.search(
    collection_name="lumi_session_archive",
    query_vector=vector,
    query_filter=Filter(
        must=[FieldCondition(key="source", match=MatchValue(value="HEART.md"))]
    ),
    limit=5
)
```

## Adding New Memories

```python
import time, uuid
from qdrant_client.models import PointStruct

text = "New memory content here..."
vector = model.encode(text).tolist()

client.upsert(
    collection_name="lumi_session_archive",
    points=[PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload={
            "text": text,
            "source": "conversation",
            "type": "memory",
            "timestamp": time.time()
        }
    )]
)
```

## Verification Queries

After seeding, test with these queries to verify the system is working:

| Query | Expected Top Result |
|---|---|
| "What is my relationship with Mom and Dad?" | RELATIONSHIP.md or MEMORY.md family entry |
| "Tell me about Cultus Anarchia" | MEMORY.md community entry |
| "How does Qdrant memory work?" | MEMORY.md infrastructure entry |
| "What is the ALCHEMY framework?" | Should find S.A.S.S. or ALIGNMENT content |

Scores above 0.3 indicate good semantic matches. Scores below 0.15 suggest the query is out of vocabulary or the collection lacks relevant content.
