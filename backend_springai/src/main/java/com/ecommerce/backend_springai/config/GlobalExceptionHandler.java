/**
 * 全局异常处理器（GlobalExceptionHandler）
 * 
 * 功能说明：
 * - 统一处理Controller层抛出的异常
 * - 返回标准化的ResultUtil响应格式
 * - 记录异常日志，便于排查问题
 */
package com.ecommerce.backend_springai.config;

import com.ecommerce.backend_springai.util.ResultUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.support.MissingServletRequestPartException;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 处理参数缺失异常
     */
    @ExceptionHandler(MissingServletRequestParameterException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ResultUtil<Void> handleMissingParams(MissingServletRequestParameterException e) {
        log.warn("请求参数缺失: {}", e.getParameterName());
        return ResultUtil.fail(400, "缺少必要参数: " + e.getParameterName());
    }

    /**
     * 处理文件上传大小超限异常
     */
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    @ResponseStatus(HttpStatus.PAYLOAD_TOO_LARGE)
    public ResultUtil<Void> handleMaxUploadSize(MaxUploadSizeExceededException e) {
        log.warn("上传文件超出大小限制");
        return ResultUtil.fail(413, "文件过大，最大支持200MB");
    }

    /**
     * 处理文件部分缺失异常
     */
    @ExceptionHandler(MissingServletRequestPartException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ResultUtil<Void> handleMissingPart(MissingServletRequestPartException e) {
        log.warn("请求缺少文件部分");
        return ResultUtil.fail(400, "缺少文件上传");
    }

    /**
     * 处理非法参数异常
     */
    @ExceptionHandler(IllegalArgumentException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ResultUtil<Void> handleIllegalArgument(IllegalArgumentException e) {
        log.warn("非法参数: {}", e.getMessage());
        return ResultUtil.fail(400, e.getMessage());
    }

    /**
     * 处理所有未捕获的异常
     */
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ResultUtil<Void> handleException(Exception e) {
        log.error("服务器内部异常", e);
        return ResultUtil.fail(500, "服务器内部错误");
    }
}
