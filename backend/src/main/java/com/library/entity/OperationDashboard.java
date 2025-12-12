package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 运营看板表实体
 */
@Data
@TableName("operation_dashboard")
public class OperationDashboard implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 指标名称(主键)
     */
    @TableId
    private String metricName;

    /**
     * 指标值
     */
    private String metricValue;

    /**
     * 环比昨日
     */
    private Double compareYesterday;

    /**
     * 环比上周
     */
    private Double compareLastWeek;

    /**
     * 环比上月
     */
    private Double compareLastMonth;

    /**
     * 趋势：上升/下降/持平
     */
    private String trend;

    /**
     * 分类
     */
    private String category;
}
