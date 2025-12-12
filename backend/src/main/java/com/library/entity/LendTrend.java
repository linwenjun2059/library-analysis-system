package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 借阅趋势表实体
 */
@Data
@TableName("lend_trend")
public class LendTrend implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 趋势日期
     */
    @TableId
    private Date trendDate;

    /**
     * 借阅次数
     */
    private Long lendCount;

    /**
     * 还书次数
     */
    private Long returnCount;

    /**
     * 活跃用户数
     */
    private Long activeUserCount;

    /**
     * 新用户数
     */
    private Long newUserCount;

    /**
     * 回访用户数(距上次借阅>30天)
     */
    private Long returnUserCount;

    /**
     * 人均借阅次数
     */
    private Double avgLendPerUser;

    /**
     * 趋势类型
     */
    private String trendType;
}
