/**
 * 面试记录控制器（RecordController）
 * 
 * 功能说明：
 * - 提供面试记录的查询接口
 * - 支持查询历史面试记录列表、查看单条记录详情
 * - 供Flutter前端的"历史记录"页面展示
 * 
 * 接口说明：
 * - GET /api/record/list - 查询历史面试记录列表
 * - GET /api/record/{id} - 查询单条面试记录详情
 * - GET /api/record/{id}/status - 查询面试记录处理状态
 */
package com.ecommerce.backend_springai.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ecommerce.backend_springai.entity.InterviewRecord;
import com.ecommerce.backend_springai.service.InterviewRecordService;
import com.ecommerce.backend_springai.util.ResultUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/record")
public class RecordController {
    
    /**
     * 面试记录服务
     */
    private final InterviewRecordService recordService;
    
    /**
     * 构造函数注入依赖
     * 
     * @param recordService 面试记录服务
     */
    public RecordController(InterviewRecordService recordService) {
        this.recordService = recordService;
    }
    
    /**
     * 查询历史面试记录列表
     * 
     * 请求参数：
     * - page: 页码，默认1
     * - size: 每页数量，默认10
     * 
     * @param page 页码
     * @param size 每页数量
     * @return 分页查询结果，包含总记录数和记录列表
     */
    @GetMapping("/list")
    public ResultUtil<Map<String, Object>> listRecords(
            @RequestParam(value = "page", defaultValue = "1") Integer page,
            @RequestParam(value = "size", defaultValue = "10") Integer size) {
        
        log.info("查询面试记录列表: page={}, size={}", page, size);
        
        try {
            // 构建分页参数
            Page<InterviewRecord> pageParam = new Page<>(page, size);
            Page<InterviewRecord> result = recordService.page(pageParam);
            
            // 转换为摘要格式
            List<Map<String, Object>> records = result.getRecords().stream()
                    .map(this::convertToSummary)
                    .collect(Collectors.toList());
            
            Map<String, Object> data = new HashMap<>();
            data.put("total", result.getTotal());
            data.put("records", records);
            
            return ResultUtil.success(data);
            
        } catch (Exception e) {
            log.error("查询面试记录列表失败", e);
            return ResultUtil.fail(500, "查询失败: " + e.getMessage());
        }
    }
    
    /**
     * 查询单条面试记录详情
     * 
     * @param id 面试记录ID
     * @return 完整的面试记录信息
     */
    @GetMapping("/{id}")
    public ResultUtil<InterviewRecord> getRecord(@PathVariable Long id) {
        log.info("查询面试记录详情, id={}", id);
        
        try {
            InterviewRecord record = recordService.getById(id);
            
            if (record == null) {
                return ResultUtil.fail(404, "面试记录不存在");
            }
            
            return ResultUtil.success(record);
            
        } catch (Exception e) {
            log.error("查询面试记录详情失败, id={}", id, e);
            return ResultUtil.fail(500, "查询失败: " + e.getMessage());
        }
    }
    
    /**
     * 查询面试记录处理状态
     * 
     * @param id 面试记录ID
     * @return 处理状态信息
     */
    @GetMapping("/{id}/status")
    public ResultUtil<Map<String, Object>> getStatus(@PathVariable Long id) {
        log.info("查询面试记录状态: id={}", id);
        
        try {
            InterviewRecord record = recordService.getById(id);
            
            if (record == null) {
                return ResultUtil.fail(404, "面试记录不存在");
            }
            
            Map<String, Object> statusInfo = new HashMap<>();
            statusInfo.put("interviewId", record.getId());
            statusInfo.put("status", record.getStatus().name());
            statusInfo.put("statusDesc", getStatusDescription(record.getStatus()));
            
            return ResultUtil.success(statusInfo);
            
        } catch (Exception e) {
            log.error("查询面试记录状态失败, id={}", id, e);
            return ResultUtil.fail(500, "查询失败: " + e.getMessage());
        }
    }
    
    /**
     * 将InterviewRecord转换为摘要格式
     * 
     * @param record 完整的面试记录
     * @return 摘要信息Map
     */
    private Map<String, Object> convertToSummary(InterviewRecord record) {
        Map<String, Object> summary = new HashMap<>();
        summary.put("interviewId", record.getId());
        summary.put("audioFileId", record.getAudioFileId());
        summary.put("durationSeconds", record.getDurationSeconds());
        summary.put("status", record.getStatus().name());
        summary.put("createdAt", record.getCreatedAt());
        return summary;
    }
    
    /**
     * 获取状态描述文本
     * 
     * @param status 状态枚举
     * @return 状态描述
     */
    private String getStatusDescription(InterviewRecord.Status status) {
        switch (status) {
            case PROCESSING:
                return "AI分析中";
            case ASR_COMPLETED:
                return "语音识别完成";
            case DIALOGUE_PARSED:
                return "对话解析完成";
            case EVALUATION_COMPLETED:
                return "评估报告生成完成";
            case COMPLETED:
                return "处理完成，可查看报告";
            case FAILED:
                return "处理失败";
            default:
                return "未知状态";
        }
    }
}
