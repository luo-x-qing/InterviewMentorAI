#RAG 检索问答验证脚本（离线，直连本地向量库）
# 用法：
#   python scripts/rag_query.py "Java HashMap底层原理"       # 单次原始检索
#   python scripts/rag_query.py answer "问题"                 # agentic 完整答案（langgraph 工作流）
#   python scripts/rag_query.py                               # 交互式（输入 exit 退出，answer 模式）
# 输出每个命中块：分数 / 来源 / 题号 / 内容全文（标注是否含图片 OCR 文本）
import sys
import os
import asyncio

# 将backend_python目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.rag_service import RagService
from app.services.agentic_rag_service import AgenticRagService


async def query(svc: RagService, q: str, top_k: int = 3) -> None:
    """执行一次混合检索 + 重排，打印命中结果"""
    res = await svc.retrieve_by_question(q, use_hybrid=True, use_rerank=True)
    print(f"\n问题: {q}")
    m = res.metrics
    if m and m.hit_count > 0:
        print(f"命中 {m.hit_count} 条 | 分数 {m.score_min:.3f} ~ {m.score_max:.3f} | 来源 {list(m.sources.items())}")
    else:
        print("命中 0 条")
    for i, d in enumerate(res.docs):
        has_ocr = "图片内容" in d.content
        print(f"\n  ── 候选 #{i + 1}  相似度 {d.score:.3f}  {('含图片OCR' if has_ocr else '纯文本')} ──")
        print(f"     来源: {d.source}")
        print(f"     标题: {d.title}")
        print(f"     内容: {d.content.replace(chr(10), ' ')[:400]}")


async def answer_query(q: str) -> None:
    """agentic 完整答案：检索→扩展（同题全部块拼接）→评估（过滤无关）→合成"""
    svc = AgenticRagService()
    result = await svc.answer(q)
    print(f"\n问题: {q}")
    print(f"状态: {result.status} | 检索轮数: {result.iterations}")
    if result.log:
        print("工作流日志: " + " | ".join(result.log))
    if not result.candidates:
        print("未找到候选答案")
        return
    for i, c in enumerate(result.candidates):
        tag = "相关" if c.related else "无关"
        print(f"\n  ── 候选 #{i + 1}  相似度 {c.score:.3f}  [{tag}] ──")
        print(f"     来源: {c.source}")
        print(f"     标题: 题{c.question_no} {c.title}")
        print(f"     完整答案: {c.full_answer[:800]}")
    svc.close()


async def main():
    svc = RagService(top_k=3, threshold=0.25)
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        if args[0].lower() in ("answer", "ans"):
            for q in args[1:]:
                await answer_query(q)
        else:
            for q in args:
                await query(svc, q)
        svc.vector_db.close()
        return
    print("===== RAG 检索问答验证（输入问题回车，exit 退出）=====")
    print("提示: 输入「answer 问题」走 agentic 完整答案；直接输入问题走原始检索")
    print(f"数据库: {settings.sqlite_db_path}")
    print(f"题库目录: {settings.rag_doc_root}")
    try:
        while True:
            q = input("\n问题> ").strip()
            if not q:
                continue
            if q.lower() in ("exit", "quit", "退出"):
                break
            if q.lower().startswith("answer "):
                await answer_query(q[len("answer "):].strip())
            else:
                await query(svc, q)
    except (KeyboardInterrupt, EOFError):
        pass
    svc.vector_db.close()
    print("\n已退出")


if __name__ == "__main__":
    asyncio.run(main())
