package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 热门图书表实体
 */
@Data
@TableName("hot_books")
public class HotBooks implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 排名
     */
    @TableId
    private Integer rankNo;

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
}
