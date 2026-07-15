/**
 * 面试记录服务类（InterviewRecordService）
 * 
 * 功能说明：
 * - 提供面试记录的CRUD操作
 * - 被AudioController调用，存储音频上传后的初始记录
 * - 被InterviewAgentGraph调用，更新流水线处理状态和结果
 * - 被RecordController调用，查询历史面试记录
 * 
 * 核心方法：
 * - createRecord(): 创建面试记录（音频上传时）
 * - updateStatus(): 更新处理状态
 * - updateTranscript(): 更新ASR转写文本
 * - updateDialogue(): 更新对话列表
 * - updateReport(): 更新复盘报告
 * - getById(): 查询单条记录
 * - listAll(): 查询记录列表
 */
package com.ecommerce.backend_springai.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ecommerce.backend_springai.entity.InterviewRecord;
import com.ecommerce.backend_springai.repository.InterviewRecordMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Slf4j
@Service
public class InterviewRecordService extends ServiceImpl<InterviewRecordMapper, InterviewRecord> {
    
    /**
     * 创建面试记录
     * 在音频上传成功后调用，初始化记录状态为PROCESSING
     * 
     * @param record 面试记录实体（已填充audioFileId, audioFilePath, durationSeconds等字段）
     * @return 保存后的记录（包含自增ID）
     */
    @Transactional
    public InterviewRecord createRecord(InterviewRecord record) {
        log.info("创建面试记录, audioFileId={}", record.getAudioFileId());
        
        // 设置初始状态
        record.setStatus(InterviewRecord.Status.PROCESSING);
        record.setCreatedAt(LocalDateTime.now());
        record.setUpdatedAt(LocalDateTime.now());
        
        // 保存到数据库
        save(record);
        log.info("面试记录创建成功, id={}", record.getId());
        
        return record;
    }
    
    /**
     * 更新流水线处理状态
     * 在Agent流水线每个节点执行完成后调用
     * 
     * @param id 面试记录ID
     * @param status 新状态
     */
    @Transactional
    public void updateStatus(Long id, InterviewRecord.Status status) {
        log.info("更新面试记录状态, id={}, status={}", id, status);
        
        InterviewRecord record = getById(id);
        if (record != null) {
            record.setStatus(status);
            record.setUpdatedAt(LocalDateTime.now());
            updateById(record);
        }
    }
    
    /**
     * 更新ASR转写文本
     * 在Whisper ASR节点执行完成后调用
     * 
     * @param id 面试记录ID
     * @param rawTranscript ASR识别的原始文本
     */
    @Transactional
    public void updateTranscript(Long id, String rawTranscript) {
        log.info("更新ASR转写文本, id={}, textLength={}", id, rawTranscript != null ? rawTranscript.length() : 0);
        
        InterviewRecord record = getById(id);
        if (record != null) {
            record.setRawTranscript(rawTranscript);
            record.setStatus(InterviewRecord.Status.ASR_COMPLETED);
            record.setUpdatedAt(LocalDateTime.now());
            updateById(record);
        }
    }
    
    /**
     * 更新对话列表
     * 在DialogueParseNode说话人分离完成后调用
     * 
     * @param id 面试记录ID
     * @param dialogueJson 对话列表JSON字符串
     */
    @Transactional
    public void updateDialogue(Long id, String dialogueJson) {
        log.info("更新对话列表, id={}", id);
        
        InterviewRecord record = getById(id);
        if (record != null) {
            record.setDialogueJson(dialogueJson);
            record.setStatus(InterviewRecord.Status.DIALOGUE_PARSED);
            record.setUpdatedAt(LocalDateTime.now());
            updateById(record);
        }
    }
    
    /**
     * 更新复盘报告
     * 在ReportGenNode报告生成完成后调用
     * 
     * @param id 面试记录ID
     * @param reportJson 复盘报告JSON字符串
     */
    @Transactional
    public void updateReport(Long id, String reportJson) {
        log.info("更新复盘报告, id={}", id);
        
        InterviewRecord record = getById(id);
        if (record != null) {
            record.setReportJson(reportJson);
            record.setStatus(InterviewRecord.Status.COMPLETED);
            record.setUpdatedAt(LocalDateTime.now());
            updateById(record);
        }
    }
    
    /**
     * 标记流水线执行失败
     * 在Agent流水线异常时调用
     * 
     * @param id 面试记录ID
     * @param errorMsg 错误信息（可选，用于调试）
     */
    @Transactional
    public void markFailed(Long id, String errorMsg) {
        log.error("面试记录处理失败, id={}, error={}", id, errorMsg);
        
        InterviewRecord record = getById(id);
        if (record != null) {
            record.setStatus(InterviewRecord.Status.FAILED);
            record.setUpdatedAt(LocalDateTime.now());
            updateById(record);
        }
    }
}
