package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 每日统计表实体
 */
@Data
@TableName("daily_stats")
public class DailyStats implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 统计日期
     */
    @TableId
    private Date statDate;

    /**
     * 借阅次数
     */
    private Integer lendCount;

    /**
     * 归还次数
     */
    private Integer returnCount;

    /**
     * 新增用户数
     */
    private Integer newUserCount;

    /**
     * 活跃用户数
     */
    private Integer activeUserCount;

    /**
     * 逾期次数
     */
    private Integer overdueCount;

    /**
     * 平均借阅天数
     */
    private Double avgBorrowDays;

    /**
     * 创建时间
     */
    @TableField(exist = false)
    private Date createTime;
}
