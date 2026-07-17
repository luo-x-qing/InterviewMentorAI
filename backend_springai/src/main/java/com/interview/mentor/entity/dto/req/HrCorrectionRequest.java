package com.interview.mentor.entity.dto.req;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class HrCorrectionRequest {

    @NotNull(message = "评分不能为空")
    @DecimalMin(value = "0", message = "评分不能小于0")
    @DecimalMax(value = "100", message = "评分不能大于100")
    private BigDecimal score;

    private String level;

    private String remark;
}
