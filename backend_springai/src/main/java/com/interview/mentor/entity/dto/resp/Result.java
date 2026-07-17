package com.interview.mentor.entity.dto.resp;

import lombok.Data;

@Data
public class Result<T> {

    private int code;
    private String message;
    private T data;

    private Result() {}

    public static <T> Result<T> success(T data) {
        Result<T> result = new Result<>();
        result.code = 200;
        result.message = "success";
        result.data = data;
        return result;
    }

    public static <T> Result<T> success() {
        return success(null);
    }

    public static <T> Result<T> error(int code, String message) {
        Result<T> result = new Result<>();
        result.code = code;
        result.message = message;
        return result;
    }

    public static <T> Result<T> error(String message) {
        return error(500, message);
    }
}
