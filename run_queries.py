#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import io
from pathlib import Path

# Fix encoding for console output
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from main import load_education_policy_documents
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker

# Mock LLM just returns extracted context
def mock_llm(prompt):
    lines = prompt.split('\n')
    # Find the actual LLM might return something from context
    return "Based on the provided context, this is the answer."

# Load raw documents
raw_docs = load_education_policy_documents()
print(f"Loaded {len(raw_docs)} documents", file=sys.stderr)

# Chunk them
chunker = RecursiveChunker(chunk_size=800)
chunked_docs = []

for doc in raw_docs:
    chunks = chunker.chunk(doc.content)
    print(f"  {doc.id}: {len(chunks)} chunks", file=sys.stderr)
    for i, chunk in enumerate(chunks):
        chunked_doc = type(doc)(
            id=f"{doc.id}_chunk_{i}",
            content=chunk,
            metadata=doc.metadata
        )
        chunked_docs.append(chunked_doc)

print(f"Total chunks: {len(chunked_docs)}", file=sys.stderr)

# Create store and add
store = EmbeddingStore()
store.add_documents(chunked_docs)
print(f"Store collection size: {store.get_collection_size()}", file=sys.stderr)

# Create agent
agent = KnowledgeBaseAgent(store, mock_llm)

# Test queries
queries = [
    ("Thí sinh được phép mang những vật dụng gì vào phòng thi?", None),
    ("Việc sử dụng điện thoại và internet tại Điểm thi được quy định thế nào?", {"category": "quy_dinh_chung"}),
    ("Điểm liệt trong xét công nhận tốt nghiệp THPT là bao nhiêu điểm?", None),
    ("Mỗi bài thi tự luận được chấm bao nhiêu vòng và do ai thực hiện?", None),
    ("Thời hạn nhận đơn phúc khảo bài thi là bao nhiêu ngày kể từ ngày công bố điểm?", None),
]

print("\n=== RUNNING QUERIES ===", file=sys.stderr)
relevant_count = 0

for i, (query, metadata_filter) in enumerate(queries, 1):
    print(f"\nQuery {i}: {query[:60]}...")
    
    # Search
    if metadata_filter:
        results = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
    else:
        results = store.search(query, top_k=3)
    
    if results:
        top = results[0]
        score = top.get('score', 0)
        content = top['content'][:80].replace('\n', ' ')
        print(f"  Top-1 Score: {score:.3f}")
        print(f"  Content: {content}...")
        relevant = score > 0.3  # Simple relevance heuristic
        relevant_count += relevant
        print(f"  Relevant: {'✅' if relevant else '❌'}")
    else:
        print(f"  No results")
    
    # Agent answer
    try:
        answer = agent.answer(query, top_k=3)
        print(f"  Agent: {answer[:80]}...")
    except Exception as e:
        print(f"  Agent error: {str(e)[:80]}")

print(f"\n=== RESULTS SUMMARY ===")
print(f"Queries with relevant top-3: {relevant_count} / 5")

