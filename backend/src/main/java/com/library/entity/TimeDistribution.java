package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 时间分布表实体
 */
@Data
@TableName("time_distribution")
public class TimeDistribution implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 时间类型(复合主键之一)
     */
    private String timeType;

    /**
     * 时间值
     */
    private Integer timeValue;

    /**
     * 借阅次数
     */
    private Long borrowCount;

    /**
     * 归还次数
     */
    private Long returnCount;

    /**
     * 活跃用户数
     */
    private Long activeUserCount;

    /**
     * 占比
     */
    private Double percentage;
}
