package com.interview.mentor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.interview.mentor.entity.InterviewSession;
import com.interview.mentor.exception.BusinessException;
import com.interview.mentor.mapper.InterviewSessionMapper;
import com.interview.mentor.service.InterviewSessionService;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Random;

@Service
public class InterviewSessionServiceImpl implements InterviewSessionService {

    private final InterviewSessionMapper sessionMapper;

    public InterviewSessionServiceImpl(InterviewSessionMapper sessionMapper) {
        this.sessionMapper = sessionMapper;
    }

    @Override
    public InterviewSession createSession(String title, Long tenantId, Long hrUserId,
                                           String candidateName, String candidatePhone) {
        InterviewSession session = new InterviewSession();
        session.setTenantId(tenantId);
        session.setTitle(title);
        session.setCreatedBy(hrUserId);
        session.setInviteCode(generateInviteCode());
        session.setCandidateName(candidateName);
        session.setCandidatePhone(candidatePhone);
        session.setStatus("PENDING");
        session.setExpireAt(LocalDateTime.now().plusHours(24)); // 24小时过期
        session.setCreatedAt(LocalDateTime.now());

        sessionMapper.insert(session);
        return session;
    }

    @Override
    public InterviewSession getSessionByCode(String inviteCode) {
        InterviewSession session = sessionMapper.selectByInviteCode(inviteCode);
        if (session == null) {
            throw new BusinessException(404, "邀请码无效");
        }

        // 检查是否过期
        if (session.getExpireAt() != null && session.getExpireAt().isBefore(LocalDateTime.now())) {
            throw new BusinessException(410, "邀请码已过期");
        }

        // 检查状态
        if ("COMPLETED".equals(session.getStatus())) {
            throw new BusinessException(400, "该面试已完成");
        }

        return session;
    }

    @Override
    public void bindInterview(Long sessionId, Long interviewId) {
        InterviewSession session = sessionMapper.selectById(sessionId);
        if (session == null) {
            throw new BusinessException(404, "面试会话不存在");
        }

        session.setInterviewId(interviewId);
        session.setStatus("COMPLETED");
        sessionMapper.updateById(session);
    }

    @Override
    public IPage<InterviewSession> listSessions(Page<InterviewSession> page,
                                                 Long tenantId, Long hrUserId) {
        return sessionMapper.selectPage(page,
                new LambdaQueryWrapper<InterviewSession>()
                        .eq(InterviewSession::getTenantId, tenantId)
                        .eq(InterviewSession::getCreatedBy, hrUserId)
                        .orderByDesc(InterviewSession::getCreatedAt));
    }

    @Override
    public boolean isCodeValid(String inviteCode) {
        InterviewSession session = sessionMapper.selectByInviteCode(inviteCode);
        if (session == null) return false;
        if ("COMPLETED".equals(session.getStatus())) return false;
        if (session.getExpireAt() != null && session.getExpireAt().isBefore(LocalDateTime.now())) return false;
        return true;
    }

    /**
     * 生成6位大写字母邀请码
     */
    private String generateInviteCode() {
        String chars = "ABCDEFGHJKLMNPQRSTUVWXYZ";
        Random random = new Random();
        StringBuilder code = new StringBuilder();
        for (int i = 0; i < 6; i++) {
            code.append(chars.charAt(random.nextInt(chars.length())));
        }
        // 确保唯一性
        if (sessionMapper.selectByInviteCode(code.toString()) != null) {
            return generateInviteCode(); // 递归重试
        }
        return code.toString();
    }
}
