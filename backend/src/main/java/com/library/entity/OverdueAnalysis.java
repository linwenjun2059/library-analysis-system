package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 逾期分析表实体
 */
@Data
@TableName("overdue_analysis")
public class OverdueAnalysis implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 分析类型(复合主键之一)
     */
    private String analysisType;

    /**
     * 目标ID
     */
    private String targetId;

    /**
     * 目标名称
     */
    private String targetName;

    /**
     * 逾期次数
     */
    private Long overdueCount;

    /**
     * 总借阅次数
     */
    private Long totalBorrowCount;

    /**
     * 逾期率
     */
    private Double overdueRate;

    /**
     * 平均逾期天数
     */
    private Double avgOverdueDays;

    /**
     * 当前逾期数量
     */
    private Long currentOverdueCount;

    /**
     * 风险等级
     */
    private String riskLevel;
}
