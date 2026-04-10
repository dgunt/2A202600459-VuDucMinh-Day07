# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Đức Minh
**Nhóm:** 67-E403
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**

High cosine similarity nghĩa là hai câu có ý nghĩa hoặc ngữ cảnh gần giống nhau trong không gian embedding.

**Ví dụ HIGH similarity:**
- **Sentence A:** Tớ thích học AI
- **Sentence B:** Học AI là niềm vui của tớ 
- **Tại sao:** Cả hai câu đều nói về việc thích học AI, chỉ khác cách diễn đạt.

**Ví dụ LOW similarity:**
- **Sentence A:** Tớ thích học AI 
- **Sentence B:** Tớ đi học bằng xe bus
- **Tại sao:** Một câu nói về sở thích, một câu nói về phương tiện di chuyển, gần như không liên quan đến nhau về ngữ nghĩa.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**

Cosine similarity tập trung vào hướng của vector, tức là mức độ giống nhau về ngữ nghĩa, thay vì độ lớn của vector.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

```
Bước nhảy giữa 2 chunk liên tiếp:
  step = chunk_size - overlap = 500 - 50 = 450

Công thức số chunk:
  chunks = ceil((document_length - chunk_size) / step) + 1

Thay số vào:
  chunks = ceil((10000 - 500) / 450) + 1
         = ceil(9500 / 450) + 1
         = ceil(21.11) + 1
         = 22 + 1 = 23
```

**Đáp án: 23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

```
Khi overlap tăng lên 100:
  step mới = 500 - 100 = 400
  
Số chunk mới:
  chunks = ceil((10000 - 500) / 400) + 1
         = ceil(9500 / 400) + 1
         = ceil(23.75) + 1
         = 24 + 1 = 25
```

Overlap lớn hơn làm số chunk tăng từ 23 lên 25 vì mỗi chunk dịch ít hơn, nên cần nhiều chunk hơn để phủ hết tài liệu. Người ta muốn overlap nhiều hơn để giữ ngữ cảnh liên tục giữa các đoạn, tránh mất ý ở phần biên của chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Quy chế thi tốt nghiệp THPT (Thông tư 15/2020/TT-BGDĐT)

**Tại sao nhóm chọn domain này?**

Quy chế thi là loại tài liệu pháp lý chuyên sâu có cấu trúc chương, điều rõ ràng và chứa nhiều quy định phức tạp. Việc chọn domain này giúp kiểm thử tốt khả năng chia nhỏ văn bản (chunking) sao cho không bị mất ngữ cảnh pháp lý và kiểm chứng việc tìm kiếm (retrieval) trả về đúng điều khoản quy định.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | `01_quy_dinh_chung.md` | TT 15/2020 | 4,406 | `{"category": "quy_dinh_chung", "phase": "general"}` |
| 2 | `02_ban_chi_dao_hoi_dong.md` | TT 15/2020 | 10,291 | `{"category": "to_chuc_thi", "phase": "preparation"}` |
| 3 | `03_diem_thi_phong_thi.md` | TT 15/2020 | 6,404 | `{"category": "to_chuc_thi", "phase": "preparation"}` |
| 4 | `04_doi_tuong_dieu_kien.md` | TT 15/2020 | 8,646 | `{"category": "dang_ky_thi", "phase": "registration"}` |
| 5 | `05_trach_nhiem_thi_sinh.md` | TT 15/2020 | 8,409 | `{"category": "thi_sinh", "phase": "registration"}` |
| 6 | `06_cong_tac_de_thi.md` | TT 15/2020 | 12,889 | `{"category": "de_thi", "phase": "preparation"}` |
| 7 | `07_in_sao_van_chuyen_de.md`| TT 15/2020 | 6,409 | `{"category": "de_thi", "phase": "preparation"}` |
| 8 | `08_coi_thi.md` | TT 15/2020 | 15,182 | `{"category": "coi_thi", "phase": "exam"}` |
| 9 | `09_cham_thi.md` | TT 15/2020 | 29,970 | `{"category": "cham_thi", "phase": "grading"}` |
| 10 | `10_phuc_khao_tot_nghiep.md`| TT 15/2020 | 52,945 | `{"category": "phuc_khao", "phase": "appeals"}` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `category` | `string` | `"quy_dinh_chung"`, `"coi_thi"` | Giúp khoanh vùng nhanh các nội dung có chung chủ đề, dễ dàng lọc kết quả tìm kiếm theo nội dung chuyên môn thay vì từ khóa (ví dụ truy vấn về coi thi chỉ quét tài liệu nhóm coi_thi). |
| `phase` | `string` | `"preparation"`, `"grading"` | Cho phép hệ thống lọc kết quả theo quá trình liên quan trong kỳ thi, giúp thu hẹp phạm vi context nếu câu hỏi nhắm vào một giai đoạn cụ thể (chuẩn bị thi, lúc thi, chấm bài). |
| `source` | `string` | `"Thông tư 15/2020/TT-BGDDT"` | Hỗ trợ cung cấp câu trích dẫn tham chiếu ở cuối câu trả lời, tăng độ tin cậy. Dữ liệu này được map dưới dạng shared key - áp dụng chung cho mọi docs từ YAML schema. |

---
## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu (nhỏ, trung bình, lớn):

**Tài liệu 1: `01_quy_dinh_chung.md` (4,406 ký tự)**
| Strategy | Chunk Count | Avg Length | Preserves Context? |
|----------|-------------|------------|-------------------|
| FixedSizeChunker (`fixed_size`) | 6 | 776 | ✅ Tốt |
| SentenceChunker (`by_sentences`) | 11 | 398 | ⚠️ Trung bình (chunks quá nhỏ) |
| RecursiveChunker (`recursive`) | 7 | 628 | ✅ Tốt |

**Tài liệu 2: `08_coi_thi.md` (15,182 ký tự)**
| Strategy | Chunk Count | Avg Length | Preserves Context? |
|----------|-------------|------------|-------------------|
| FixedSizeChunker (`fixed_size`) | 21 | 771 | ✅ Tốt, nhưng có thể cắt giữa Điều |
| SentenceChunker (`by_sentences`) | 12 | 1,262 | ✅ Tốt |
| RecursiveChunker (`recursive`) | 23 | 658 | ✅ Tốt, tôn trọng cấu trúc paragraph |

**Tài liệu 3: `09_cham_thi.md` (29,970 ký tự)**
| Strategy | Chunk Count | Avg Length | Preserves Context? |
|----------|-------------|------------|-------------------|
| FixedSizeChunker (`fixed_size`) | 40 | 798 | ✅ Tốt, nhưng kích thước cố định |
| SentenceChunker (`by_sentences`) | 44 | 679 | ✅ Tốt, nhưng phụ thuộc cấu trúc câu |
| RecursiveChunker (`recursive`) | 47 | 636 | ✅ Tốt nhất, giữ ngữ cảnh pháp lý |

### Strategy Của Tôi

**Loại:** RecursiveChunker (với tối ưu cho domain pháp lý)

**Mô tả cách hoạt động:**

RecursiveChunker chia văn bản theo múc độ ưu tiên của separators: trước tiên tôn trọng paragraph boundaries (`\n\n`), sau đó line breaks (`\n`), rồi câu (`. `), từ (` `), và cuối cùng ký tự. Khi một khúc văn bản vượt quá `chunk_size`, nó đệ quy qua separator tiếp theo. Điều này bảo toàn cấu trúc logic của tài liệu thay vì cắt ngang randomly như FixedSizeChunker.

**Tại sao tôi chọn strategy này cho domain nhóm?**

Tài liệu pháp lý (Thông tư 15/2020) có cấu trúc markdown rõ ràng: các "Điều" được tách thành paragraphs (`\n\n`), các mục nhỏ được tách thành lines (`\n`). RecursiveChunker sẽ "hiểu" cấu trúc này tự động, giữ mỗi Điều hoặc nhóm Điều liên quan trong cùng chunk. So sánh Baseline cho thấy RecursiveChunker có `Avg Length = 636-658 ký tự`, phân bố hợp lý và consistent. Quan trọng nhất: mỗi chunk sẽ tương ứng với 1-2 Điều hoặc mục phụ, làm tăng **retrieval quality** khi hệ thống truy vấn "Thí sinh được mang gì vào phòng thi?" → sẽ lấy chunk liên quan đó hoặc gần nhất.

**Code snippet:**
```python
from src.chunking import RecursiveChunker

# Khởi tạo chunker
chunker = RecursiveChunker(chunk_size=800)

# Đọc tài liệu pháp lý
with open("data/education_policy/08_coi_thi.md", "r", encoding="utf-8") as f:
    text = f.read()

# Chia chunk tôn trọng cấu trúc markdown
chunks = chunker.chunk(text)

print(f"Documents: {len(chunks)} chunks")
for i, chunk in enumerate(chunks[:3]):
    print(f"Chunk {i}: {len(chunk)} chars, starts: {chunk[:80]}...")
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| 09_cham_thi (29,970 ký) | FixedSizeChunker (baseline) | 40 | 798 | ⚠️ Có thể cắt Điều |
| | **RecursiveChunker (của tôi)** | 47 | 636 | ✅ Tốt, tôn trọng cấu trúc |

**Kết luận:** `RecursiveChunker(chunk_size=800)` là best choice cho domain pháp lý vì:

- Tôn trọng cấu trúc markdown tự động (paragraph boundaries `\n\n`, line breaks `\n`)
- Mỗi chunk tương ứng 1-2 Điều khoản → dễ retrieval
- Consistent avg length (636-658 ký tự) trên 3 tài liệu khác nhau

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi(Vũ Đức Minh) | RecursiveChunker (chunk_size=800) | 8.5 | Tôn trọng cấu trúc markdown, giữ ngữ cảnh pháp lý, avg length consistent 636 ký tự | Chunk count cao (47 vs 40), có thể chậm hơn với tài liệu rất lớn |
| Nguyễn Thị Ngọc | SentenceChunker | 9/10 | Preserve context tốt, ít chunks | Chunk dài hơn, cost embedding cao |
| Nguyễn Việt Quang | LegalArticleChunker (`legal_article`) | 7.5 / 10 | Giữ trọn vẹn ngữ cảnh theo từng Điều luật, phù hợp khi câu hỏi cần đầy đủ các Khoản và Điểm liên quan trong cùng một Điều. | Chunk quá dài, số lượng chunk ít nên embedding bị loãng; đã thể hiện rõ ở query về chấm thi khi hệ thống retrieve nhầm tài liệu. |
| Nguyễn Trọng Tiến | CustomChunker (legal-aware hybrid) | 8 | Overlap theo khoản, không cắt giữa điều luật | Nhiều chunk hơn RecursiveChunker 

**Strategy nào tốt nhất cho domain này? Tại sao?**

SentenceChunker của Nguyễn Thị Ngọc đạt điểm cao nhất (9/10) vì nó cân bằng tốt giữa việc giữ ngữ cảnh pháp lý (preserve context) và hiệu quả tính toán (ít chunks = cost embedding thấp hơn). Mặc dù RecursiveChunker của tôi cũng tôn trọng cấu trúc, nhưng số chunks cao hơn (47 vs 12 của SentenceChunker) dẫn đến chi phí embedding lớn và tốc độ retrieval chậm hơn. CustomChunker của Nguyễn Trọng Tiến cũng là lựa chọn hợp lý nhưng phức tạp hơn mà chưa đạt hiệu suất vượt trội so với SentenceChunker.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:

Sử dụng regex pattern `(?<=[.!?])(?:\s+|\n+)` để detect câu (tách sau dấu `.`, `!`, `?` và khoảng trắng/newline). Strip whitespace từ mỗi câu, sau đó nhóm vào chunks theo `max_sentences_per_chunk`. Xử lý edge case: text rỗng/chỉ khoảng trắng trả về `[]`, từng câu cũng được strip để tránh dư khoảng trắng.

**`RecursiveChunker.chunk` / `_split`** — approach:

Thuật toán đệ quy chia văn bản theo separators ưu tiên: `["\n\n", "\n", ". ", " ", ""]`. `_split()` nhận separator hiện tại, tách text theo nó, rồi duyệt các phần. Nếu phần đã gộp lại <= chunk_size thì giữ buffer; nếu vượt quá thì đệ quy buffer theo separator tiếp theo. Base case: text <= chunk_size return [text]; hết separator list thì force chia theo character. Cách này đảm bảo tôn trọng cấu trúc markdown (paragraph trước, rồi line, rồi câu).

### EmbeddingStore

**`add_documents` + `search`** — approach:

Mỗi Document được chuyển thành record (id, content, embedding, metadata) rồi lưu vào ChromaDB (nếu có) hoặc in-memory list. Search tính embedding của query, rồi dùng dot product để score tất cả stored records. ChromaDB trả về distances (convert về similarity bằng `1 - distance`), in-memory dùng `_search_records()` để tính dot product trực tiếp. Kết quả sort descending theo score, trả top_k.

**`search_with_filter` + `delete_document`** — approach:

Filter **trước** similarity search để giảm không gian tìm kiếm. ChromaDB dùng `where` clause trong query, in-memory lọc self._store theo metadata trước khi gọi `_search_records()`. Delete document dùng doc_id trong metadata để xác định tất cả chunks thuộc document đó, rồi xóa từ ChromaDB collection hoặc loại khỏi self._store. Trả True/False để báo có xóa được chunks hay không.

### KnowledgeBaseAgent

**`answer`** — approach:

RAG pattern: trước tiên gọi `store.search(question, top_k)` để lấy top_k chunks liên quan. Gộp chunks dưới dạng context với label `[Chunk N]` để LLM phân biệt. Xây dựng prompt chứa 3 phần: system instruction (hướng dẫn dùng context), context (chunks), và question. Cuối cùng gọi `llm_fn(prompt)` để generate answer. Nếu không tìm chunk nào, context = "No relevant context found..." để LLM biết giới hạn kiến thức.

### Test Results

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

====================== 42 passed in 1.69s ======================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Thí sinh được phép mang bút viết và thước kẻ vào phòng thi | Các dụng cụ viết như bút chì, thước vẽ được phép sử dụng trong kỳ thi | High | 0.89 | ✅ |
| 2 | Mỗi bài thi tự luận được chấm hai vòng độc lập | Thí sinh phải nộp bài thi đúng giờ qui định | Low | 0.12 | ✅ |
| 3 | Điểm liệt là khi bài thi đạt từ 1.0 điểm trở xuống | Nếu một môn dưới 1.0 điểm thì không tốt nghiệp | High | 0.76 | ✅ |
| 4 | Phúc khảo bài thi phải nộp đơn trong vòng 10 ngày | Thí sinh có thời hạn 10 ngày kể từ ngày công bố điểm để nộp đơn phúc khảo | High | 0.92 | ✅ |
| 5 | Coi thi là công việc đảm bảo công bằng kỳ thi | Chấm thi phải có sự giám sát chặt chẽ từ hội đồng | Low | 0.34 | ⚠️ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**

Cặp 5 là bất ngờ nhất: dự đoán low similarity nhưng actual score 0.34 cao hơn kỳ vọng. Điều này cho thấy embeddings không chỉ focus vào topic chính ("coi thi" vs "chấm thi") mà còn nắm bắt các semantic connection sâu hơn như "đảm bảo" và "giám sát" - cả hai câu đều liên quan đến oversight và quality control trong kỳ thi. Embeddings biểu diễn ý nghĩa thông qua các mối liên hệ ngữ cảnh và intent, không chỉ từ khóa surface-level riêng lẻ.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Thí sinh được phép mang những vật dụng gì vào phòng thi? | Gồm: Bút viết, thước kẻ, bút chì, tẩy chì, êke, thước vẽ đồ thị, dụng cụ vẽ hình, máy tính cầm tay (không soạn thảo văn bản/thẻ nhớ), Atlat Địa lý (đối với môn Địa). |
| 2 | Việc sử dụng điện thoại và internet tại Điểm thi được quy định thế nào? (Metadata filter: `category="quy_dinh_chung"`) | Bố trí 01 điện thoại để ở phòng làm việc chung (chỉ dùng nghe gọi, bật loa ngoài, có ghi nhật ký). Máy tính chỉ được nối internet khi báo cáo nhanh. |
| 3 | Điểm liệt trong xét công nhận tốt nghiệp THPT là bao nhiêu điểm? | Thí sinh bị điểm liệt nếu có bài thi (hoặc môn thi thành phần) đạt từ 1,0 điểm trở xuống (tất cả phải trên 1,0 mới đạt). |
| 4 | Mỗi bài thi tự luận được chấm bao nhiêu vòng và do ai thực hiện? | Chấm hai vòng độc lập bởi hai Cán bộ chấm thi (CBChT) của hai Tổ Chấm thi khác nhau. |
| 5 | Thời hạn nhận đơn phúc khảo bài thi là bao nhiêu ngày kể từ ngày công bố điểm? | Trong thời hạn 10 ngày kể từ ngày công bố điểm thi. |


### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thí sinh được phép mang những vật dụng gì vào phòng thi? | Dụng cụ viết: bút viết, thước kẻ, bút chì, tẩy chì, êke, thước vẽ đồ thị, dụng cụ vẽ hình, máy tính cầm tay... | 0.87 | ✅ | Vật dụng được phép: bút viết, thước kẻ, bút chì, tẩy chì, êke, thước vẽ, máy tính cầm tay, Atlat... |
| 2 | Việc sử dụng điện thoại và internet tại Điểm thi được quy định thế nào? | Bố trí 01 điện thoại để ở phòng làm việc chung. Chỉ dùng nghe gọi, bật loa ngoài, có ghi nhật ký... | 0.82 | ✅ | Điệnhiệu thoại: 1 chiếc ở phòng chung, chỉ nghe gọi, bật loa. Internet: máy tính nối khi báo cáo nhanh... |
| 3 | Điểm liệt trong xét công nhận tốt nghiệp THPT là bao nhiêu điểm? | Điểm liệt: bài thi hoặc môn thi thành phần đạt từ 1,0 điểm trở xuống. Tất cả môn phải trên 1,0... | 0.79 | ✅ | Thí sinh bị điểm liệt nếu có bài thi đạt ≤ 1,0 điểm. Tất cả môn phải > 1,0 mới đạt tốt nghiệp... |
| 4 | Mỗi bài thi tự luận được chấm bao nhiêu vòng và do ai thực hiện? | Chấm hai vòng độc lập bởi hai Cán bộ chấm thi (CBChT) khác nhau. Độc lập không được biết điểm vòng 1... | 0.81 | ✅ | Bài tự luận chấm 2 vòng độc lập bởi 2 CBChT từ 2 Tổ Chấm thi khác nhau... |
| 5 | Thời hạn nhận đơn phúc khảo bài thi là bao nhiêu ngày kể từ ngày công bố điểm? | Thời hạn 10 ngày kể từ ngày công bố điểm thi. Đơn phúc khảo phải ghi rõ lý do và yêu cầu... | 0.85 | ✅ | Thí sinh có thời hạn 10 ngày kể từ ngày công bố điểm để nộp đơn phúc khảo bài thi... |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**

SentenceChunker của Nguyễn Thị Ngọc cho thấy rằng việc sử dụng domain knowledge (nhóm câu thay vì chia cứng) có thể đạt retrieval quality cao hơn mà chỉ dùng 12 chunks thay vì 47 của tôi. Điều này dạy tôi rằng việc hiểu cấu trúc ngôn ngữ tự nhiên quan trọng hơn cố gắng tôn trọng 100% cấu trúc markdown của tài liệu. Chi phí embedding thấp hơn cũng có lợi ích dài hạn cho scalability.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**

Nhóm khác sử dụng hierarchical chunking (tôi chưa thử) với multi-level metadata (document_level, section_level, chunk_level) giúp retrieval có context richer. Kỹ thuật này cho phép truy vấn có thể "zoom in/out" tùy theo abstract level cần thiết, thay vì luôn lấy chunk nhỏ nhất. Điều này mở ra khả năng hybrid retrieval kết hợp section context với chunk detail.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**

Tôi sẽ test hybrid approach: chunk_size=1000 (thay vì 800) với explicit sentence boundary detection để tránh cắt giữa câu quan trọng, và thêm hierarchical metadata để giữ link tới parent section. Ngoài ra, tôi sẽ thêm bước post-processing để merge tiny chunks (<200 chars) ngay sau khi chunking, giảm "noise" và tối ưu hóa embedding cost mà vẫn giữ retrieval quality.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 14 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **87 / 100** |
