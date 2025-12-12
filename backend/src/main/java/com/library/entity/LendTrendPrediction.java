package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 借阅趋势预测实体
 */
@Data
@TableName("lend_trend_prediction")
public class LendTrendPrediction {
    
    @TableId
    private String lendMonth;
    
    private Integer year;
    
    private Integer month;
    
    private Long lendCount;
    
    private Long activeUsers;
    
    private Long uniqueBooks;
    
    private Long predictedCount;
    
    private String dataType;
    
    private String trend;
    
    private String predictionDate;
}
