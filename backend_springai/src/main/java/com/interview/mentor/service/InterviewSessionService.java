package com.interview.mentor.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.InterviewSession;

public interface InterviewSessionService {

    /**
     * HR创建面试会话（生成邀请码）
     */
    InterviewSession createSession(String title, Long tenantId, Long hrUserId,
                                    String candidateName, String candidatePhone);

    /**
     * 候选人通过邀请码查看面试会话
     */
    InterviewSession getSessionByCode(String inviteCode);

    /**
     * 候选人提交录音后，绑定面试记录
     */
    void bindInterview(Long sessionId, Long interviewId);

    /**
     * HR查看自己创建的会话列表
     */
    IPage<InterviewSession> listSessions(Page<InterviewSession> page,
                                          Long tenantId, Long hrUserId);

    /**
     * 检查邀请码是否有效
     */
    boolean isCodeValid(String inviteCode);
}
