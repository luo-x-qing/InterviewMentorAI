/**
 * 统一响应工具类（ResultUtil）
 * 
 * 功能说明：
 * - 封装所有接口的统一响应格式
 * - 标准结构：{ code: 状态码, msg: 提示信息, data: 业务数据 }
 * - 提供success/fail静态方法，方便Controller返回值构造
 * - 供所有Controller使用，保证接口返回格式一致
 */
package com.ecommerce.backend_springai.util;

import lombok.Data;

@Data
public class ResultUtil<T> {
    /** 状态码：200成功，其他为失败 */
    private Integer code;
    /** 提示信息 */
    private String msg;
    /** 业务数据，可以为null */
    private T data;

    /**
     * 返回成功响应（带数据）
     * 
     * @param data 返回的业务数据
     * @param <T> 数据类型
     * @return 成功的响应对象
     */
    public static <T> ResultUtil<T> success(T data) {
        ResultUtil<T> r = new ResultUtil<>();
        r.setCode(200);
        r.setMsg("success");
        r.setData(data);
        return r;
    }

    /**
     * 返回成功响应（无数据）
     * 
     * @param <T> 数据类型
     * @return 成功的响应对象，data为null
     */
    public static <T> ResultUtil<T> success() {
        return success(null);
    }

    /**
     * 返回失败响应
     * 
     * @param code 错误码
     * @param msg 错误描述
     * @param <T> 数据类型
     * @return 失败的响应对象
     */
    public static <T> ResultUtil<T> fail(Integer code, String msg) {
        ResultUtil<T> r = new ResultUtil<>();
        r.setCode(code);
        r.setMsg(msg);
        return r;
    }
}
