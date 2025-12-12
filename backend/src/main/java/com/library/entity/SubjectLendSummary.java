package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 主题分类汇总表实体
 */
@Data
@TableName("subject_lend_summary")
public class SubjectLendSummary implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主题分类
     */
    @TableId
    private String subject;

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
     * 平均借阅天数
     */
    private Double avgBorrowDays;

    /**
     * 逾期率
     */
    private Double overdueRate;

    /**
     * 最受欢迎的院系
     */
    private String popularDept;

    /**
     * 创建时间(数据库中不存在，标记为非数据库字段)
     */
    @TableField(exist = false)
    private Date createTime;
}
