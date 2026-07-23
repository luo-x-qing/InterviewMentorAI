package com.interview.mentor.entity.dto.resp;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

/**
 * Python AI 后端分析结果 —— 映射 {@code POST /api/v1/analysis/analyze} 的 AnalysisResponse。
 *
 * <p>Python 侧字段为 snake_case，用 {@link JsonProperty} 显式映射，避免命名策略耦合。
 */
@Data
public class AnalysisResult {

    /** COMPLETED / FAILED（中间态不会出现在最终响应） */
    private String status;

    @JsonProperty("interview_id")
    private Long interviewId;

    /** Markdown 复盘报告全文 */
    private String report;

    /** 逐题评估 */
    private List<EvaluationItem> evaluations;

    /** 失败时的错误信息 */
    private String error;

    public boolean isCompleted() {
        return "COMPLETED".equalsIgnoreCase(status);
    }

    @Data
    public static class EvaluationItem {
        private String question;
        private String answer;
        /** 0-100 */
        private Integer score;
        /** PROFICIENT 熟练 / WEAK 薄弱 */
        private String level;
        private String strengths;
        private String weaknesses;
        /** 仅薄弱项有值 */
        private String correction;
        @JsonProperty("knowledge_points")
        private String knowledgePoints;
    }
}
