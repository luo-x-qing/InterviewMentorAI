#rag效果评估脚本（T4.3 检索可观测：命中率 / 得分分布 / 来源分布，对比 P0 空库基线 0%）
import sys
import os
import json

# 将backend_python目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.vector_db import VectorDB
from app.services.llm_client import LlmClient
from app.services.prompt_service import PromptService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RagService
from app.services.rag_mcp import RagMCP
from app.services.agent_pipeline import AgentPipeline
from app.models.schemas import AnalysisRequest

# 构造实例
vector_db = VectorDB()
llm_client = LlmClient()
chunking_service = ChunkingService()
embedding_service = EmbeddingService(llm_client=llm_client)
prompt_service = PromptService(llm_client=llm_client)
rag_service = RagService(
    vector_db=vector_db,
    embedding_service=embedding_service,
)
rag_mcp = RagMCP(rag_service=rag_service, prompt_service=prompt_service)
agent_pipeline = AgentPipeline(prompt_service=prompt_service, rag_mcp=rag_mcp)

# 测试用面试问题（标准答案存在知识库中）
test_questions = [
    "Java HashMap底层原理",
    "Python列表和元组区别",
    "SpringBoot自动配置机制"
]

P0_BASELINE_HIT_RATE = 0.0  # P0 基线：空库检索召回率 0%
BASELINE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_eval_baseline.json")


def _load_baseline() -> float:
    """读取历史基线（初始为 P0 空库基线 0.0）"""
    try:
        with open(BASELINE_FILE, "r", encoding="utf-8") as f:
            return float(json.load(f).get("hit_rate", P0_BASELINE_HIT_RATE))
    except Exception:
        return P0_BASELINE_HIT_RATE


def test_retrieval_metrics() -> float:
    """T4.3 检索可观测：命中率对比 P0 基线 + 得分/来源分布"""
    print("===== 检索质量评估（重排默认开启）=====")
    total_hit = 0
    total_query = len(test_questions)
    for q in test_questions:
        res = rag_service.retrieve_by_question(q)
        m = res.metrics
        if m and m.hit_count > 0:
            total_hit += 1
        print(f"问题：{q}")
        if m and m.hit_count > 0:
            print(f"  命中数：{m.hit_count}  得分范围：{m.score_min:.2f}~{m.score_max:.2f}  均分：{m.score_mean:.2f}")
            print(f"  来源分布：{m.sources}")
        else:
            print("  命中数：0（未命中）")
        for d in res.docs:
            print(f"    [{d.score:.2f}] {d.source} · {d.title[:40]}")
    recall = total_hit / total_query
    baseline = _load_baseline()
    print(f"\n检索召回率：{recall:.2f}  （基线：{baseline:.2f}，提升 {recall - baseline:.2f}）")
    return recall

def test_hybrid_retrieval():
    """测试混合检索"""
    print("\n===== 测试混合检索 =====")
    for q in test_questions:
        res = rag_service.retrieve_by_question(q, use_hybrid=True)
        print(f"问题：{q} 匹配到{len(res.docs)}条文档")
        for d in res.docs:
            print(f"  分数：{d.score:.2f} 来源：{d.source}")

def test_vector_only_retrieval():
    """测试纯向量检索"""
    print("\n===== 测试纯向量检索 =====")
    for q in test_questions:
        res = rag_service.retrieve_by_question(q, use_hybrid=False)
        print(f"问题：{q} 匹配到{len(res.docs)}条文档")
        for d in res.docs:
            print(f"  分数：{d.score:.2f} 来源：{d.source}")

def test_chunking_methods():
    """测试不同分块方法"""
    print("\n===== 测试分块方法 =====")
    sample_text = """这是一个测试文档。它包含多个句子。
    
第一段内容。这里有一些重要的信息。
    
第二段内容。这里有一些额外的细节。"""
    
    # 固定长度分块
    chunks_fixed = chunking_service.split(sample_text, "fixed")
    print(f"固定长度分块：{len(chunks_fixed)} 个块")
    
    # 按段落分块
    chunks_paragraph = chunking_service.split(sample_text, "paragraph")
    print(f"按段落分块：{len(chunks_paragraph)} 个块")
    
    # 语义分块
    chunks_semantic = chunking_service.split(sample_text, "semantic")
    print(f"语义分块：{len(chunks_semantic)} 个块")

def test_end_to_end_rag():
    """0005 端到端评估：对比有无RAG的评估结果差异"""
    test_req = AnalysisRequest(interview_id=999, audio_file_path="./data/audio/test_interview.wav")
    print("\n===== 开启RAG增强评估 端到端测试 =====")
    resp = agent_pipeline.run(test_req)
    print(f"分析状态：{resp.status} 报告长度：{len(resp.report)}")

if __name__ == "__main__":
    recall = test_retrieval_metrics()
    baseline = _load_baseline()
    if recall >= baseline:
        print(f"门禁通过：召回率 {recall:.2f} >= 基线 {baseline:.2f}")
    else:
        print(f"门禁失败：召回率 {recall:.2f} < 基线 {baseline:.2f}，检索质量回退！")
        sys.exit(1)
    test_hybrid_retrieval()
    test_vector_only_retrieval()
    test_chunking_methods()
    test_end_to_end_rag()
