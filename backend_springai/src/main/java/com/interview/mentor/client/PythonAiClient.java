package com.interview.mentor.client;

import com.interview.mentor.entity.dto.resp.AnalysisResult;

/**
 * Python AI 后端的调用接缝（seam）。
 *
 * <p>把与 Python 后端的 HTTP 细节（URL、DTO、超时、序列化、错误处理）封装在实现之后，
 * 让业务代码依赖接口而非 RestClient。两个适配器坐实这个接缝：生产用
 * {@link HttpPythonAiClient}（真实 HTTP），测试用内存 Fake（不起 8000 端口即可验证编排与回写）。
 */
public interface PythonAiClient {

    /**
     * 触发一次面试分析。同步阻塞直到 Python 跑完 ASR→评估→报告生成。
     *
     * @param interviewId   面试记录ID（Python 侧按此标识）
     * @param audioFilePath Python 可访问的音频文件路径（共享文件系统约束）
     * @return 分析结果（report + 逐题 evaluations）
     * @throws PythonAiException 调用失败或 Python 返回 FAILED 时抛出
     */
    AnalysisResult analyze(Long interviewId, String audioFilePath);
}
