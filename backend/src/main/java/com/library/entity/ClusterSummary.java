package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 聚类统计摘要实体
 */
@Data
@TableName("cluster_summary")
public class ClusterSummary implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 聚类编号
     */
    @TableId
    private Integer cluster;

    /**
     * 聚类名称
     */
    private String clusterName;

    /**
     * 聚类特征描述
     */
    private String clusterCharacteristics;

    /**
     * 用户数量
     */
    private Long userCount;

    /**
     * 平均借阅量
     */
    private Double avgBorrowCount;

    /**
     * 平均活跃天数
     */
    private Double avgActiveDays;

    /**
     * 平均逾期率
     */
    private Double avgOverdueRate;

    /**
     * 平均借阅天数
     */
    private Double avgBorrowDays;

    /**
     * 平均阅读广度
     */
    private Double avgReadingBreadth;
}
