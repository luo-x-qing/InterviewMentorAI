package com.interview.mentor.entity.dto.req;

import lombok.Data;

@Data
public class CreateInterviewRequest {

    private String jobRole;
    private Long userId;
}
