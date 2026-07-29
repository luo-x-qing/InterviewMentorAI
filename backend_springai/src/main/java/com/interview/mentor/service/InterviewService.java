package com.interview.mentor.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.InterviewRecord;
import com.interview.mentor.entity.dto.req.CreateInterviewRequest;
import org.springframework.web.multipart.MultipartFile;

public interface InterviewService {

    InterviewRecord createInterview(CreateInterviewRequest request, Long currentUserId);

    InterviewRecord uploadAudio(Long interviewId, MultipartFile audioFile);

    InterviewRecord getInterview(Long interviewId);

    IPage<InterviewRecord> listInterviews(Page<InterviewRecord> page);

    IPage<InterviewRecord> listMyInterviews(Page<InterviewRecord> page, Long userId);
}
