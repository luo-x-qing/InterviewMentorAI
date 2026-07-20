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
