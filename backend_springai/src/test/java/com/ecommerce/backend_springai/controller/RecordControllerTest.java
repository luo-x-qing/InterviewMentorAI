package com.ecommerce.backend_springai.controller;

import com.ecommerce.backend_springai.entity.InterviewRecord;
import com.ecommerce.backend_springai.service.InterviewRecordService;
import com.ecommerce.backend_springai.util.ResultUtil;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.bean.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(RecordController.class)
class RecordControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private InterviewRecordService recordService;

    @Test
    void listRecords_Success() throws Exception {
        // 准备测试数据
        InterviewRecord record = InterviewRecord.builder()
                .id(1L)
                .audioFileId("test-uuid-123")
                .status(InterviewRecord.Status.COMPLETED)
                .createdAt(LocalDateTime.now())
                .build();

        List<InterviewRecord> records = Arrays.asList(record);
        
        // 模拟服务层调用
        when(recordService.page(any())).thenReturn(
            new com.baomidou.mybatisplus.extension.plugins.pagination.Page<InterviewRecord>(1, 10)
                .setRecords(records)
                .setTotal(1)
        );

        // 执行测试
        mockMvc.perform(get("/api/record/list")
                .param("page", "1")
                .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.total").value(1));
    }

    @Test
    void getRecord_NotFound() throws Exception {
        // 模拟服务层返回null
        when(recordService.getById(eq(999L))).thenReturn(null);

        // 执行测试
        mockMvc.perform(get("/api/record/999"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(404));
    }

    @Test
    void getRecord_Success() throws Exception {
        // 准备测试数据
        InterviewRecord record = InterviewRecord.builder()
                .id(1L)
                .audioFileId("test-uuid-123")
                .status(InterviewRecord.Status.COMPLETED)
                .createdAt(LocalDateTime.now())
                .build();

        // 模拟服务层调用
        when(recordService.getById(eq(1L))).thenReturn(record);

        // 执行测试
        mockMvc.perform(get("/api/record/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.audioFileId").value("test-uuid-123"));
    }

    @Test
    void getStatus_Success() throws Exception {
        // 准备测试数据
        InterviewRecord record = InterviewRecord.builder()
                .id(1L)
                .status(InterviewRecord.Status.PROCESSING)
                .build();

        // 模拟服务层调用
        when(recordService.getById(eq(1L))).thenReturn(record);

        // 执行测试
        mockMvc.perform(get("/api/record/1/status"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.status").value("PROCESSING"));
    }
}
