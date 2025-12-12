package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 用户排名表实体
 */
@Data
@TableName("user_ranking")
public class UserRanking implements Serializable {

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
     * 专业
     */
    private String occupation;

    /**
     * 用户类型
     */
    private String userType;

    /**
     * 总借阅量
     */
    private Long totalBorrowCount;

    /**
     * 院系内排名
     */
    private Integer deptRank;

    /**
     * 专业内排名
     */
    private Integer occupationRank;

    /**
     * 院系总用户数
     */
    private Integer deptTotalUsers;

    /**
     * 专业总用户数
     */
    private Integer occupationTotalUsers;

    /**
     * 院系百分位
     */
    private Double percentileDept;

    /**
     * 专业百分位
     */
    private Double percentileOccupation;
}
