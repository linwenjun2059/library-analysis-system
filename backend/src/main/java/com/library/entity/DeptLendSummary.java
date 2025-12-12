package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 院系借阅汇总表实体
 */
@Data
@TableName("dept_lend_summary")
public class DeptLendSummary implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 院系名称
     */
    @TableId
    private String dept;

    /**
     * 总借阅次数
     */
    private Long totalLendCount;

    /**
     * 借阅用户数
     */
    private Long uniqueUserCount;

    /**
     * 借阅图书数
     */
    private Long uniqueBookCount;

    /**
     * 人均借阅次数
     */
    private Double avgLendPerUser;

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
     * 最喜欢的主题
     */
    private String favoriteSubject;

    /**
     * 最喜欢主题的借阅次数
     */
    private Long subjectMaxCount;

    /**
     * 最喜欢的位置
     */
    private String favoriteLocation;

    /**
     * 创建时间(数据库中不存在，标记为非数据库字段)
     */
    @TableField(exist = false)
    private Date createTime;
}
