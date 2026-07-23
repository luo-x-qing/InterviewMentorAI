package com.interview.mentor.entity.dto.resp;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 验证 Python AnalysisResponse 的 snake_case JSON 能正确反序列化进 AnalysisResult。
 * 字段名映射错配曾是集成失败的根因，故显式守护。
 */
class AnalysisResultDeserializationTest {

    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    @DisplayName("Python 响应 JSON 正确映射到 AnalysisResult")
    void deserializesPythonResponse() throws Exception {
        String json = """
                {
                  "status": "COMPLETED",
                  "interview_id": 42,
                  "report": "# 报告全文",
                  "evaluations": [
                    {
                      "question": "什么是多态",
                      "answer": "……",
                      "score": 85,
                      "level": "PROFICIENT",
                      "strengths": "概念清晰",
                      "weaknesses": "",
                      "correction": "",
                      "knowledge_points": "OOP"
                    }
                  ],
                  "error": null
                }
                """;

        AnalysisResult result = mapper.readValue(json, AnalysisResult.class);

        assertTrue(result.isCompleted());
        assertEquals(42L, result.getInterviewId());
        assertEquals("# 报告全文", result.getReport());
        assertEquals(1, result.getEvaluations().size());

        AnalysisResult.EvaluationItem item = result.getEvaluations().get(0);
        assertEquals(85, item.getScore());
        assertEquals("PROFICIENT", item.getLevel());
        assertEquals("OOP", item.getKnowledgePoints(), "knowledge_points 应映射到 knowledgePoints");
    }

    @Test
    @DisplayName("FAILED 状态下 isCompleted 为 false")
    void failedStatus_isNotCompleted() throws Exception {
        String json = """
                {"status": "FAILED", "interview_id": 1, "error": "ASR 失败"}
                """;

        AnalysisResult result = mapper.readValue(json, AnalysisResult.class);

        assertFalse(result.isCompleted());
        assertEquals("ASR 失败", result.getError());
    }
}
