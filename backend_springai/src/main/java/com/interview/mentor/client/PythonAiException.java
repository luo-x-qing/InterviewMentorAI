package com.interview.mentor.client;

/**
 * 调用 Python AI 后端失败时抛出（HTTP 错误、超时、或 Python 返回 FAILED 状态）。
 */
public class PythonAiException extends RuntimeException {

    public PythonAiException(String message) {
        super(message);
    }

    public PythonAiException(String message, Throwable cause) {
        super(message, cause);
    }
}
