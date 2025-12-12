package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 用户逾期风险预测实体
 */
@Data
@TableName("overdue_risk_prediction")
public class OverdueRiskPrediction {
    
    @TableId
    private String userid;
    
    private String dept;
    
    private String userType;
    
    private Long borrowCount;
    
    private Double historicalOverdueRate;
    
    private Double avgBorrowDays;
    
    private Double overdueProbability;
    
    private String riskLevel;
    
    private String warningMessage;
    
    private String predictionDate;
}
