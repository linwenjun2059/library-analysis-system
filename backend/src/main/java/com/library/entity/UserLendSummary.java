package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 用户借阅汇总表实体
 */
@Data
@TableName("user_lend_summary")
public class UserLendSummary implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 用户ID
     */
    @TableId
    private String userid;

    /**
     * 总借阅次数
     */
    private Long totalLendCount;

    /**
     * 总借阅天数
     */
    private Long totalBorrowDays;

    /**
     * 平均借阅天数
     */
    private Double avgBorrowDays;

    /**
     * 逾期次数
     */
    private Long overdueCount;

    /**
     * 逾期率
     */
    private Double overdueRate;

    /**
     * 续借次数
     */
    private Long renewCount;

    /**
     * 最喜欢的主题
     */
    private String favoriteSubject;

    /**
     * 最喜欢的位置
     */
    private String favoriteLocation;

    /**
     * 首次借阅日期
     */
    private Date firstLendDate;

    /**
     * 最后借阅日期
     */
    private Date lastLendDate;

    /**
     * 活跃天数
     */
    private Integer activeDays;

    /**
     * 创建时间(数据库中不存在，标记为非数据库字段)
     */
    @TableField(exist = false)
    private Date createTime;
}
