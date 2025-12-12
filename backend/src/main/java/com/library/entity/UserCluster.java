package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 用户聚类分群实体(K-means算法结果)
 */
@Data
@TableName("user_clusters")
public class UserCluster implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 用户ID
     */
    @TableId
    private String userid;

    /**
     * 院系
     */
    private String dept;

    /**
     * 用户类型
     */
    private String userType;

    /**
     * 专业
     */
    private String occupation;

    /**
     * 聚类编号
     */
    private Integer cluster;

    /**
     * 聚类名称(如：科研学习型、文学类爱好者)
     */
    private String clusterName;

    /**
     * 聚类特征描述
     */
    private String clusterCharacteristics;

    /**
     * 借阅量
     */
    private Long borrowCount;

    /**
     * 活跃天数
     */
    private Integer activeDays;

    /**
     * 逾期率
     */
    private Double overdueRate;

    /**
     * 平均借阅天数
     */
    private Double avgBorrowDays;

    /**
     * 阅读广度(涉及主题数)
     */
    private Integer readingBreadth;
}
