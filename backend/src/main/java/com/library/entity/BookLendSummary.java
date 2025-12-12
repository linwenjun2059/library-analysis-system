package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 图书借阅汇总表实体
 */
@Data
@TableName("book_lend_summary")
public class BookLendSummary implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 图书ID
     */
    @TableId
    private String bookId;

    /**
     * 总借阅次数
     */
    private Long totalLendCount;

    /**
     * 借阅用户数
     */
    private Long uniqueUserCount;

    /**
     * 平均借阅天数
     */
    private Double avgBorrowDays;

    /**
     * 总借阅天数
     */
    private Long totalBorrowDays;

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
     * 首次借阅日期
     */
    private Date firstLendDate;

    /**
     * 最后借阅日期
     */
    private Date lastLendDate;

    /**
     * 借阅频率
     */
    private Double lendFrequency;

    /**
     * 创建时间(数据库中不存在，标记为非数据库字段)
     */
    @TableField(exist = false)
    private Date createTime;
}
