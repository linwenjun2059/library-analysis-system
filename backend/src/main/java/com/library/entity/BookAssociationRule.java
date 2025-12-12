package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 图书关联规则实体(FPGrowth算法挖掘结果)
 */
@Data
@TableName("book_association_rules")
public class BookAssociationRule implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 前项图书ID(逗号分隔)
     */
    @TableId
    private String antecedentBooks;

    /**
     * 后项图书ID(逗号分隔)
     */
    private String consequentBooks;

    /**
     * 前项图书标题
     */
    private String antecedentTitle;

    /**
     * 后项图书标题
     */
    private String consequentTitle;

    /**
     * 前项图书主题
     */
    private String antecedentSubject;

    /**
     * 后项图书主题
     */
    private String consequentSubject;

    /**
     * 置信度(0-1)
     */
    private Double confidence;

    /**
     * 提升度(>1表示正相关)
     */
    private Double lift;

    /**
     * 支持度
     */
    private Double support;

    /**
     * 规则描述(如：借阅《三体》的读者80%会借《流浪地球》)
     */
    private String ruleDescription;

    /**
     * 关联类型(同主题关联/跨主题关联)
     */
    private String associationType;
}
