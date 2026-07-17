package com.interview.mentor.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.InterviewRecord;
import com.interview.mentor.entity.dto.req.CreateInterviewRequest;
import org.springframework.web.multipart.MultipartFile;

public interface InterviewService {

    /**
     * 创建面试记录
     */
    InterviewRecord createInterview(CreateInterviewRequest request, Long currentUserId);

    /**
     * 上传音频并触发 AI 分析
     */
    InterviewRecord uploadAudio(Long interviewId, MultipartFile audioFile);

    /**
     * 查询面试记录详情
     */
    InterviewRecord getInterview(Long interviewId);

    /**
     * 分页查询面试列表（HR查看本租户所有）
     */
    IPage<InterviewRecord> listInterviews(Page<InterviewRecord> page, Long tenantId);

    /**
     * 分页查询候选人自己的面试列表
     */
    IPage<InterviewRecord> listMyInterviews(Page<InterviewRecord> page, Long userId);
}
