package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 出版社分析表实体
 */
@Data
@TableName("publisher_analysis")
public class PublisherAnalysis implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 出版社名称
     */
    @TableId
    private String publisher;

    /**
     * 图书数量
     */
    private Long bookCount;

    /**
     * 总借阅次数
     */
    private Long totalLendCount;

    /**
     * 总借阅用户数
     */
    private Long totalUserCount;

    /**
     * 平均借阅次数
     */
    private Double avgLendCount;

    /**
     * 排名
     */
    private Integer rankNo;
}
