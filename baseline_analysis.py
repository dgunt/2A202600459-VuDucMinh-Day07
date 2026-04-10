"""
Baseline Analysis: So sánh 3 chiến lược chunking trên 2-3 tài liệu pháp lý
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import src
sys.path.insert(0, str(Path(__file__).parent))

from src.chunking import ChunkingStrategyComparator
import json

# Load 3 tài liệu: nhỏ, trung bình, lớn
docs = {
    "01_quy_dinh_chung.md": "data/education_policy/01_quy_dinh_chung.md",
    "08_coi_thi.md": "data/education_policy/08_coi_thi.md",
    "09_cham_thi.md": "data/education_policy/09_cham_thi.md",
}

print("=" * 80)
print("BASELINE ANALYSIS: Chunking Strategy Comparison")
print("=" * 80)

results = {}
comparator = ChunkingStrategyComparator()

for doc_name, doc_path in docs.items():
    full_path = Path(__file__).parent / doc_path
    
    if not full_path.exists():
        print(f"❌ Không tìm thấy: {full_path}")
        continue
    
    with open(full_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"\n📄 Document: {doc_name}")
    print(f"   Kích thước: {len(text):,} ký tự")
    print("-" * 80)
    
    # Chạy comparator
    comparison = comparator.compare(text, chunk_size=800)
    results[doc_name] = {
        "size": len(text),
        "results": comparison
    }
    
    # In bảng kết quả
    for strategy_name, stats in comparison.items():
        count = stats["count"]
        avg_len = stats["avg_length"]
        chunks = stats["chunks"]
        
        # Đánh giá "Preserves Context"
        preserves = "✅ Tốt" if avg_len >= 500 and count <= 50 else "⚠️ Trung bình" if avg_len >= 300 else "❌ Yếu"
        
        print(f"\n  {strategy_name}:")
        print(f"    Chunk Count: {count}")
        print(f"    Avg Length: {avg_len:.0f} ký tự")
        print(f"    Preserves Context?: {preserves}")
        
        # Xem 1-2 chunk đầu
        if chunks:
            print(f"    Sample chunk 1 (first 100 chars): {chunks[0][:100]}...")
            if len(chunks) > 1:
                print(f"    Sample chunk 2 (first 100 chars): {chunks[1][:100]}...")

print("\n" + "=" * 80)
print("SUMMARY TABLE")
print("=" * 80)

# In bảng tổng hợp
for doc_name, data in results.items():
    print(f"\n### {doc_name} (Kích thước: {data['size']:,} ký tự)")
    print("| Strategy | Chunk Count | Avg Length | Context Quality |")
    print("|----------|-------------|------------|-----------------|")
    
    for strategy_name, stats in data["results"].items():
        count = stats["count"]
        avg_len = f"{stats['avg_length']:.0f}"
        quality = "✅ Tốt" if float(avg_len) >= 500 else "⚠️ Trung" if float(avg_len) >= 300 else "❌ Yếu"
        print(f"| {strategy_name:20} | {count:11} | {avg_len:10} | {quality:15} |")

# Lưu JSON để tiện xử lý sau
output_file = Path(__file__).parent / "baseline_results.json"
with open(output_file, "w", encoding="utf-8") as f:
    # Convert Chunks list để JSON-serializable
    json_results = {}
    for doc_name, data in results.items():
        json_results[doc_name] = {
            "size": data["size"],
            "strategies": {}
        }
        for strategy_name, stats in data["results"].items():
            json_results[doc_name]["strategies"][strategy_name] = {
                "count": stats["count"],
                "avg_length": round(stats["avg_length"], 2),
                "sample_chunks": [c[:100] for c in stats["chunks"][:2]]  # Chỉ lấy 2 chunks đầu
            }
    json.dump(json_results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Kết quả đã lưu vào: {output_file}")
