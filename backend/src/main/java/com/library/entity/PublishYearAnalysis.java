package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 出版年份分析表实体
 */
@Data
@TableName("publish_year_analysis")
public class PublishYearAnalysis implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 出版年份
     */
    @TableId
    private Integer pubYear;

    /**
     * 图书数量
     */
    private Long bookCount;

    /**
     * 总借阅次数
     */
    private Long totalLendCount;

    /**
     * 平均借阅次数
     */
    private Double avgLendCount;
}
