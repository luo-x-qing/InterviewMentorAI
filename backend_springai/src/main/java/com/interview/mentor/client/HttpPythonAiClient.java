package com.interview.mentor.client;

import com.interview.mentor.entity.dto.resp.AnalysisResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.Map;

/**
 * {@link PythonAiClient} 的生产适配器：通过 HTTP 调用 Python AI 后端。
 *
 * <p>封装了此前散落在 InterviewServiceImpl 里的所有 HTTP 细节：
 * baseUrl / 超时 / 请求体字段 / 反序列化 / 错误处理。RestClient 只构造一次复用。
 */
@Component
public class HttpPythonAiClient implements PythonAiClient {

    private static final Logger log = LoggerFactory.getLogger(HttpPythonAiClient.class);

    /** 注意：分析接口带 /api/v1 前缀（Python 侧前缀不统一） */
    private static final String ANALYZE_PATH = "/api/v1/analysis/analyze";

    private final RestClient restClient;

    public HttpPythonAiClient(
            @Value("${python.ai.backend.url:http://localhost:8000}") String backendUrl,
            @Value("${python.ai.backend.connect-timeout:10000}") int connectTimeout,
            @Value("${python.ai.backend.read-timeout:120000}") int readTimeout) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(connectTimeout);
        factory.setReadTimeout(readTimeout);
        this.restClient = RestClient.builder()
                .baseUrl(backendUrl)
                .requestFactory(factory)
                .build();
    }

    @Override
    public AnalysisResult analyze(Long interviewId, String audioFilePath) {
        // 请求体字段与 Python AnalysisRequest 对齐：interview_id + audio_file_path
        Map<String, Object> requestBody = Map.of(
                "interview_id", interviewId,
                "audio_file_path", audioFilePath);

        AnalysisResult result;
        try {
            result = restClient.post()
                    .uri(ANALYZE_PATH)
                    .body(requestBody)
                    .retrieve()
                    .body(AnalysisResult.class);
        } catch (RestClientException e) {
            // 覆盖 HTTP 500（Python pipeline 异常）与超时/连接错误
            throw new PythonAiException(
                    "调用 Python 分析接口失败, interviewId=" + interviewId, e);
        }

        if (result == null) {
            throw new PythonAiException("Python 分析返回空响应, interviewId=" + interviewId);
        }
        if (!result.isCompleted()) {
            throw new PythonAiException(
                    "Python 分析未完成, interviewId=" + interviewId + ", status=" + result.getStatus()
                            + ", error=" + result.getError());
        }

        log.info("Python 分析完成, interviewId={}, 评估条数={}",
                interviewId, result.getEvaluations() == null ? 0 : result.getEvaluations().size());
        return result;
    }
}
