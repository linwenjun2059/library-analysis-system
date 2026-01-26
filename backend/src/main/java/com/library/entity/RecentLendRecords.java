package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 近期借阅记录实体
 */
@Data
@TableName("recent_lend_records")
public class RecentLendRecords implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 借阅记录ID
     */
    @TableId
    private String lendId;

    /**
     * 用户ID
     */
    private String userid;

    /**
     * 图书ID
     */
    private String bookId;

    /**
     * 借阅日期
     */
    @JsonFormat(pattern = "yyyy-MM-dd", timezone = "GMT+8")
    private Date lendDate;

    /**
     * 借阅时间
     */
    private String lendTime;

    /**
     * 归还日期
     */
    @JsonFormat(pattern = "yyyy-MM-dd", timezone = "GMT+8")
    private Date retDate;

    /**
     * 归还时间
     */
    private String retTime;

    /**
     * 续借次数
     */
    private Integer renewTimes;

    /**
     * 借阅天数
     */
    private Integer borrowDays;

    /**
     * 是否逾期(0:否, 1:是)
     */
    private Integer isOverdue;

    /**
     * 创建时间(数据库中可能不存在，标记为非数据库字段)
     */
    @TableField(exist = false)
    private Date createTime;

    // ========== 关联的图书信息字段 ==========
    /**
     * 书名
     */
    @TableField(exist = false)
    private String title;

    /**
     * 作者
     */
    @TableField(exist = false)
    private String author;

    /**
     * 出版社
     */
    @TableField(exist = false)
    private String publisher;

    /**
     * 主题分类
     */
    @TableField(exist = false)
    private String subject;

    /**
     * 馆藏位置
     */
    @TableField(exist = false)
    private String locationName;
}
