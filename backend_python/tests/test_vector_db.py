import math
import pytest
import numpy as np


def _fake_embedding(dim=1024):
    return [float(i % 100) / 100.0 for i in range(dim)]


class TestTokenizer:
    def test_chinese(self, vector_db):
        tokens = vector_db._tokenize("Java HashMap底层原理")
        assert "java" in tokens
        assert "hashmap" in tokens
        assert "底层" in tokens
        assert "原理" in tokens

    def test_mixed_text(self, vector_db):
        tokens = vector_db._tokenize("我今天去ABC公司参加算法面试")
        assert "我" in tokens
        assert "今天" in tokens
        assert "abc" in tokens
        assert "公司" in tokens
        assert "算法" in tokens
        assert "面试" in tokens

    def test_english_only(self, vector_db):
        tokens = vector_db._tokenize("Hello World Test")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens

    def test_numbers(self, vector_db):
        tokens = vector_db._tokenize("Java8新特性")
        assert "java8" in tokens or "java" in tokens

    def test_empty_string(self, vector_db):
        tokens = vector_db._tokenize("")
        assert tokens == []

    def test_whitespace_only(self, vector_db):
        tokens = vector_db._tokenize("   ")
        assert tokens == []


class TestBuildIdfIndex:
    def test_empty_db(self, vector_db):
        vector_db._build_idf_index()
        assert vector_db._idf_cache == {}
        assert vector_db._idf_dirty is False

    def test_single_doc(self, vector_db):
        vector_db.conn.execute(
            "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
            ("t", "Java HashMap原理", "src"),
        )
        vector_db.conn.commit()
        vector_db._build_idf_index()
        assert len(vector_db._idf_cache) > 0
        assert all(v > 0 for v in vector_db._idf_cache.values())

    def test_multiple_docs_idf_variance(self, vector_db):
        vector_db.conn.executemany(
            "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
            [
                ("t1", "Java HashMap底层原理", "src"),
                ("t2", "Python列表和元组区别", "src"),
                ("t3", "Java SpringBoot自动配置", "src"),
            ],
        )
        vector_db.conn.commit()
        vector_db._build_idf_index()

        N = 3
        expected_java_idf = math.log((N - 2 + 0.5) / (2 + 0.5) + 1.0)
        expected_python_idf = math.log((N - 1 + 0.5) / (1 + 0.5) + 1.0)
        actual_java = vector_db._idf_cache.get("java", 0)
        actual_python = vector_db._idf_cache.get("python", 0)
        assert abs(actual_java - expected_java_idf) < 1e-6
        assert abs(actual_python - expected_python_idf) < 1e-6
        assert actual_python > actual_java

    def test_lazy_rebuild_on_search(self, vector_db):
        vector_db.conn.execute(
            "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
            ("t", "Java原理", "src"),
        )
        vector_db.conn.commit()
        vector_db._idf_dirty = True
        vector_db._idf_cache = {}
        vector_db._ensure_idf_ready()
        assert len(vector_db._idf_cache) > 0


class TestBm25Score:
    def test_exact_match(self, vector_db):
        vector_db.conn.execute(
            "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
            ("t", "Java HashMap底层原理", "src"),
        )
        vector_db.conn.commit()
        vector_db._build_idf_index()
        query = ["java", "hashmap"]
        doc = ["java", "hashmap", "底层", "原理"]
        score = vector_db._bm25_score(query, doc, avg_dl=4.0)
        assert score > 0

    def test_no_match(self, vector_db):
        vector_db.conn.execute(
            "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
            ("t", "Java HashMap底层原理", "src"),
        )
        vector_db.conn.commit()
        vector_db._build_idf_index()
        query = ["python"]
        doc = ["java", "hashmap", "底层", "原理"]
        score = vector_db._bm25_score(query, doc, avg_dl=4.0)
        assert score == 0.0

    def test_idf_impacts_score(self, vector_db):
        vector_db.conn.executemany(
            "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
            [
                ("t1", "Java常用", "src"),
                ("t2", "Java基础", "src"),
                ("t3", "Java高级 红黑树", "src"),
            ],
        )
        vector_db.conn.commit()
        vector_db._build_idf_index()
        query_rare = ["红黑树"]
        query_common = ["java"]
        doc = ["java", "红黑树"]
        score_rare = vector_db._bm25_score(query_rare, doc, avg_dl=2.0)
        score_common = vector_db._bm25_score(query_common, doc, avg_dl=2.0)
        assert score_rare > score_common


class TestInsertChunk:
    def test_insert_and_dirty_flag(self, vector_db):
        vector_db._build_idf_index()
        vector_db._idf_dirty = False
        doc_id = vector_db.insert_chunk(
            title="测试文档",
            content="Java HashMap底层原理",
            source="test",
            embedding=_fake_embedding(),
        )
        assert doc_id == 1
        assert vector_db._idf_dirty is True
        row = vector_db.conn.execute(
            "SELECT title, content, source FROM rag_docs WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        assert row[0] == "测试文档"
        assert row[1] == "Java HashMap底层原理"

    def test_multiple_inserts(self, vector_db):
        ids = []
        for title in ["t1", "t2", "t3"]:
            doc_id = vector_db.insert_chunk(
                title=title, content=f"内容{title}", source="test", embedding=_fake_embedding()
            )
            ids.append(doc_id)
        assert ids == [1, 2, 3]


class TestGetQuestionsForCoach:
    """教练出题候选池：聚合去重 + 无偏抽样（不得被 doc_id 靠前的旧题库垄断）"""

    def test_returns_questions_with_metadata(self, vector_db):
        emb = _fake_embedding()
        for i in range(3):
            vector_db.insert_chunk(
                f"题{i}", f"内容{i}", "src.md", emb, question_no=str(i), section="Java"
            )
        vector_db.insert_chunk("无题号", "内容", "other.md", emb)
        rows = vector_db.get_questions_for_coach(limit=10)
        assert len(rows) == 3
        assert {r["question_no"] for r in rows} == {"0", "1", "2"}
        assert all(r["source"] == "src.md" for r in rows)
        assert all({"question_no", "title", "content", "source", "section"} <= set(r) for r in rows)

    def test_later_imported_source_reaches_pool(self, vector_db):
        """回归：ORDER BY doc_id 会让后入库题库永远进不了候选池。

        构造 doc_id 靠前的 40 组题 + 后入库 20 组题；取 50 时旧实现只会取到
        前 40 组旧题；随机抽样下 50 > 40 必然覆盖新来源。
        """
        emb = _fake_embedding()
        for i in range(40):
            vector_db.insert_chunk(f"旧题{i}", f"旧内容{i}", "a.md", emb, question_no=f"a{i}")
        for i in range(20):
            vector_db.insert_chunk(f"新题{i}", f"新内容{i}", "b.md", emb, question_no=f"b{i}")
        rows = vector_db.get_questions_for_coach(limit=50)
        assert len(rows) == 50
        assert {r["source"] for r in rows} == {"a.md", "b.md"}


class TestSearchBm25:
    def test_basic_search(self, vector_db):
        vector_db.conn.executemany(
            "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
            [
                ("t1", "Java HashMap底层原理", "src"),
                ("t2", "Python列表和元组区别", "src"),
            ],
        )
        vector_db.conn.commit()
        results = vector_db.search_bm25(query="Java HashMap", top_k=5)
        assert len(results) >= 1
        assert results[0].title == "t1"

    def test_empty_db(self, vector_db):
        results = vector_db.search_bm25(query="Java", top_k=5)
        assert results == []

    def test_no_match(self, vector_db):
        vector_db.conn.execute(
            "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
            ("t1", "Java HashMap底层原理", "src"),
        )
        vector_db.conn.commit()
        results = vector_db.search_bm25(query="红黑树", top_k=5)
        assert results == []

    def test_top_k(self, vector_db):
        vector_db.conn.executemany(
            "INSERT INTO rag_docs(title, content, source) VALUES (?, ?, ?)",
            [
                ("t1", "Java HashMap底层原理", "src"),
                ("t2", "Java HashMap扩容机制", "src"),
                ("t3", "Python列表推导式", "src"),
            ],
        )
        vector_db.conn.commit()
        results = vector_db.search_bm25(query="Java HashMap", top_k=2)
        assert len(results) == 2


class TestSearchVector:
    def test_basic_search(self, vector_db):
        emb = _fake_embedding()
        vector_db.insert_chunk("t1", "Java HashMap底层原理", "src", emb)
        vector_db.insert_chunk("t2", "Python列表和元组区别", "src", emb)
        results = vector_db.search_vector(query_emb=emb, top_k=5, threshold=0.0)
        assert len(results) == 2

    def test_threshold_filter(self, vector_db):
        emb_zero = [0.0] * 1024
        emb_one = [1.0] * 1024
        vector_db.insert_chunk("t1", "Java", "src", emb_zero)
        vector_db.insert_chunk("t2", "Python", "src", emb_one)
        results = vector_db.search_vector(query_emb=emb_zero, top_k=5, threshold=0.99)
        assert len(results) == 1

    def test_empty_db(self, vector_db):
        results = vector_db.search_vector(query_emb=_fake_embedding(), top_k=5, threshold=0.0)
        assert results == []


class TestSearchHybrid:
    def test_basic_hybrid(self, vector_db):
        emb = _fake_embedding()
        vector_db.insert_chunk("t1", "Java HashMap底层原理", "src", emb)
        vector_db.insert_chunk("t2", "Python列表和元组区别", "src", emb)
        results = vector_db.search_hybrid(
            query="Java HashMap", query_emb=emb, top_k=5, threshold=0.0
        )
        assert len(results) >= 1

    def test_empty_db(self, vector_db):
        emb = _fake_embedding()
        results = vector_db.search_hybrid(
            query="Java", query_emb=emb, top_k=5, threshold=0.0
        )
        assert results == []

    def test_weight_impact(self, vector_db):
        emb_java = [0.5] * 1024
        emb_python = [0.0] * 1024
        vector_db.insert_chunk("t1", "Java HashMap底层原理", "src", emb_java)
        vector_db.insert_chunk("t2", "Python列表和元组区别", "src", emb_python)
        results_hybrid = vector_db.search_hybrid(
            query="Java HashMap", query_emb=emb_java, top_k=5, threshold=0.0,
        )
        results_vector = vector_db.search_hybrid(
            query="Java HashMap", query_emb=emb_java, top_k=5, threshold=0.0,
            vector_weight=1.0, bm25_weight=0.0,
        )
        assert len(results_hybrid) >= 1
        assert len(results_vector) >= 1

    def test_bm25_strong_hit_passes_high_threshold(self, vector_db):
        """T4.1 回归：BM25 强命中但向量弱时，仍应放行（阈值判定为任一路强命中）"""
        emb = _fake_embedding()
        vector_db.insert_chunk("题1", "HashMap底层原理是数组加链表", "src", emb)
        results = vector_db.search_hybrid(
            query="HashMap底层原理", query_emb=[0.0] * 1024, top_k=5, threshold=0.5
        )
        assert any(r.title == "题1" for r in results)

    def test_vector_strong_hit_passes_high_threshold(self, vector_db):
        """T4.1 回归：向量强命中但 BM25 弱（无重叠词）时，仍应放行"""
        emb = _fake_embedding()
        vector_db.insert_chunk("题1", "PyTorch张量运算", "src", emb)
        results = vector_db.search_hybrid(
            query="深度学习框架张量计算", query_emb=emb, top_k=5, threshold=0.9
        )
        assert any(r.title == "题1" for r in results)

    def test_all_weak_filtered_by_threshold(self, vector_db):
        """T4.1 回归：两路都弱于阈值时，整体滤除"""
        emb = _fake_embedding()
        vector_db.insert_chunk("题1", "HashMap底层原理", "src", emb)
        results = vector_db.search_hybrid(
            query="完全不相关的查询文本", query_emb=[0.0] * 1024, top_k=5, threshold=0.99
        )
        assert results == []


class TestStatsAndClear:
    """T5.1 统计/清空下沉到 VectorDB 后的行为"""

    def test_total_docs_vectors_and_grouping(self, vector_db):
        emb = _fake_embedding()
        vector_db.insert_chunk("题1", "Java基础", "a.md", emb)
        vector_db.insert_chunk("题2", "Python基础", "a.md", emb)
        vector_db.insert_chunk("题3", "MySQL索引", "b.md", emb)

        assert vector_db.total_docs() == 3
        assert vector_db.total_vectors() == 3
        grouping = dict(vector_db.source_grouping())
        assert grouping["a.md"] == 2
        assert grouping["b.md"] == 1

    def test_clear_all_empties_db(self, vector_db):
        emb = _fake_embedding()
        vector_db.insert_chunk("题1", "Java基础", "a.md", emb)
        vector_db.upsert_file_fingerprint("a.md", "fp-a")
        vector_db.insert_chunk("题2", "Python基础", "b.md", emb)
        vector_db.upsert_file_fingerprint("b.md", "fp-b")

        vector_db.clear_all()

        assert vector_db.total_docs() == 0
        assert vector_db.total_vectors() == 0
        assert vector_db.file_fingerprint("a.md") is None
        assert vector_db.file_fingerprint("b.md") is None
        assert vector_db.search_bm25("Java", top_k=5) == []


class TestQuestionMetadata:
    """T2.2 元数据落库：question_no / section"""

    def test_insert_chunk_with_question_metadata(self, vector_db):
        emb = _fake_embedding()
        vector_db.insert_chunk("题1", "内容", "源.md", emb, question_no="1", section="Python基础")
        row = vector_db.conn.execute(
            "SELECT title, source, question_no, section FROM rag_docs"
        ).fetchone()
        assert row[2] == "1"
        assert row[3] == "Python基础"

    def test_default_question_metadata_empty(self, vector_db):
        emb = _fake_embedding()
        vector_db.insert_chunk("题2", "内容", "源.md", emb)
        row = vector_db.conn.execute("SELECT question_no, section FROM rag_docs").fetchone()
        assert row[0] == ""
        assert row[1] == ""

    def test_search_returns_question_metadata(self, vector_db):
        emb = _fake_embedding()
        vector_db.insert_chunk(
            "题1", "HashMap底层原理是数组加链表", "源.md", emb, question_no="1", section="Java基础"
        )
        docs = vector_db.search_bm25("HashMap底层原理", top_k=1)
        assert docs and docs[0].question_no == "1"
        assert docs[0].section == "Java基础"
        docs2 = vector_db.search_vector(query_emb=emb, top_k=5, threshold=0.0)
        assert docs2 and docs2[0].question_no == "1"
        assert docs2[0].section == "Java基础"
