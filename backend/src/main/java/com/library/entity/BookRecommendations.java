package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 图书推荐表实体
 */
@Data
@TableName("book_recommendations")
public class BookRecommendations implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 用户ID(复合主键之一)
     */
    private String userid;

    /**
     * 图书ID
     */
    private String bookId;

    /**
     * 图书标题
     */
    private String title;

    /**
     * 作者
     */
    private String author;

    /**
     * 主题分类
     */
    private String subject;

    /**
     * 推荐得分(0-10分)
     */
    private Double score;

    /**
     * 推荐来源组合(cf,content,popularity)
     */
    private String recSources;

    /**
     * 推荐理由
     */
    private String reason;

    /**
     * 推荐排名(1-20)
     */
    private Integer rankNo;

    /**
     * 多样性得分(0-1,越高越多样)
     */
    private Double diversityScore;

    /**
     * 协同过滤得分(0-10)
     */
    private Double cfScore;

    /**
     * 内容推荐得分(0-10)
     */
    private Double contentScore;

    /**
     * 热门推荐得分(0-10)
     */
    private Double popularityScore;
}
