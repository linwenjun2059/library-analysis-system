package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 图书推荐基础表实体
 */
@Data
@TableName("book_recommend_base")
public class BookRecommendBase implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 推荐类型(复合主键之一)
     */
    private String recommendType;

    /**
     * 范围
     */
    private String scope;

    /**
     * 图书ID
     */
    private String bookId;

    /**
     * 书名
     */
    private String title;

    /**
     * 作者
     */
    private String author;

    /**
     * 主题
     */
    private String subject;

    /**
     * 借阅次数
     */
    private Long borrowCount;

    /**
     * 排名
     */
    private Integer rankNo;

    /**
     * 更新日期
     */
    private Date updateDate;
}
