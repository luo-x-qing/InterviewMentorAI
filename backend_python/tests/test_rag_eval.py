#rag效果评估脚本
from app.services.rag_service import rag_service
from app.services.agent_pipeline import agent_pipeline
from app.models.schemas import AnalysisRequest

# 测试用面试问题（标准答案存在知识库中）
test_questions = [
    "Java HashMap底层原理",
    "Python列表和元组区别",
    "SpringBoot自动配置机制"
]

def test_retrieval_metrics():
    """0005 检索质量评估：统计命中、精确率"""
    total_hit = 0
    total_query = len(test_questions)
    for q in test_questions:
        res = rag_service.retrieve_by_question(q)
        if len(res.docs) > 0:
            total_hit += 1
            print(f"问题：{q} 匹配到{len(res.docs)}条文档")
            for d in res.docs:
                print(f"  相似度：{d.score:.2f} 来源：{d.source}")
    recall = total_hit / total_query
    print(f"\n检索召回率：{recall:.2f}")

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
    chunks_fixed = rag_service.split_chunks(sample_text, "fixed")
    print(f"固定长度分块：{len(chunks_fixed)} 个块")
    
    # 按段落分块
    chunks_paragraph = rag_service.split_chunks(sample_text, "paragraph")
    print(f"按段落分块：{len(chunks_paragraph)} 个块")
    
    # 语义分块
    chunks_semantic = rag_service.split_chunks(sample_text, "semantic")
    print(f"语义分块：{len(chunks_semantic)} 个块")

def test_end_to_end_rag():
    """0005 端到端评估：对比有无RAG的评估结果差异"""
    test_req = AnalysisRequest(interview_id=999, audio_file_path="./data/audio/test_interview.wav")
    print("\n===== 开启RAG增强评估 端到端测试 =====")
    resp = agent_pipeline.run(test_req)
    print(f"分析状态：{resp.status} 报告长度：{len(resp.report)}")

if __name__ == "__main__":
    test_retrieval_metrics()
    test_hybrid_retrieval()
    test_vector_only_retrieval()
    test_chunking_methods()
    test_end_to_end_rag()