package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 推荐效果统计表实体
 */
@Data
@TableName("recommendation_stats")
public class RecommendationStats implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 统计类型(主键)
     */
    @TableId
    private String statType;

    /**
     * 统计名称
     */
    private String statName;

    /**
     * 统计值
     */
    private String statValue;
}
