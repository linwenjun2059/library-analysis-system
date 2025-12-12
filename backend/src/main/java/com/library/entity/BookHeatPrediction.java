package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

/**
 * 图书热度预测实体
 */
@Data
@TableName("book_heat_prediction")
public class BookHeatPrediction {
    
    @TableId
    private String bookId;
    
    private String title;
    
    private String subject;
    
    private String author;
    
    private Long totalLendCount;
    
    private Long recentLendCount;
    
    private Long uniqueUserCount;
    
    private Double heatScore;
    
    private String heatLevel;
    
    private String trend;
    
    private String recommendation;
    
    private String predictionDate;
}
