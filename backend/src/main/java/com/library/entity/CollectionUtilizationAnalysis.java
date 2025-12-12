package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 馆藏利用分析表实体
 */
@Data
@TableName("collection_utilization_analysis")
public class CollectionUtilizationAnalysis implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 维度类型(复合主键之一)
     */
    private String dimensionType;

    /**
     * 维度值
     */
    private String dimensionValue;

    /**
     * 馆藏图书总数
     */
    private Long totalBooks;

    /**
     * 被借图书数
     */
    private Long borrowedBooks;

    /**
     * 总借阅次数
     */
    private Long totalLendCount;

    /**
     * 平均借阅次数
     */
    private Double avgBorrowTimes;

    /**
     * 平均借阅天数
     */
    private Double avgBorrowDays;

    /**
     * 周转率(本/年)
     */
    private Double turnoverRate;

    /**
     * 高需求图书数(借阅>5次)
     */
    private Long highDemandBooks;

    /**
     * 中等需求图书数(1-5次)
     */
    private Long mediumDemandBooks;

    /**
     * 低需求图书数(0次)
     */
    private Long lowDemandBooks;

    /**
     * 独立读者数
     */
    private Long uniqueReaders;

    /**
     * 读者/图书比
     */
    private Double readerPerBookRatio;
}
