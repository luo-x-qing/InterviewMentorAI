/**
 * 统一响应工具类（ResultUtil）
 * 
 * 功能说明：
 * - 封装后端所有接口的统一响应格式
 * - 标准结构：{ code: 状态码, msg: 提示信息, data: 业务数据 }
 * - 提供success/fail静态工厂方法，简化Controller返回值构建
 * - 被所有Controller使用，保持前后端响应格式一致
 */
package com.ecommerce.backend_springai.util;

import lombok.Data;

@Data
public class ResultUtil<T> {
    /** 状态码：200成功，其他为失败 */
    private Integer code;
    /** 提示信息 */
    private String msg;
    /** 业务数据（泛型） */
    private T data;

    /**
     * 构建成功响应（带数据）
     * 
     * @param data 业务返回数据
     * @param <T> 数据类型
     * @return 包装后的成功响应对象
     */
    public static <T> ResultUtil<T> success(T data) {
        ResultUtil<T> r = new ResultUtil<>();
        r.setCode(200);
        r.setMsg("success");
        r.setData(data);
        return r;
    }

    /**
     * 构建成功响应（无数据）
     * 
     * @param <T> 数据类型
     * @return 包装后的成功响应对象（data为null）
     */
    public static <T> ResultUtil<T> success() {
        return success(null);
    }

    /**
     * 构建失败响应
     * 
     * @param code 错误状态码
     * @param msg 错误提示信息
     * @param <T> 数据类型
     * @return 包装后的失败响应对象
     */
    public static <T> ResultUtil<T> fail(Integer code, String msg) {
        ResultUtil<T> r = new ResultUtil<>();
        r.setCode(code);
        r.setMsg(msg);
        return r;
    }
}
