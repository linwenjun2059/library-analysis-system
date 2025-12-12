package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 图书维度表实体
 */
@Data
@TableName("book_dimension")
public class BookDimension implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 图书ID
     */
    @TableId
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
     * 出版社
     */
    private String publisher;

    /**
     * ISBN
     */
    private String isbn;

    /**
     * 出版年份
     */
    private Integer pubYear;

    /**
     * 主题分类
     */
    private String subject;

    /**
     * 索书号
     */
    private String callNo;

    /**
     * 馆藏位置
     */
    private String locationName;

    /**
     * 文献类型
     */
    private String docTypeName;

    /**
     * 创建时间(数据库中不存在，标记为非数据库字段)
     */
    @TableField(exist = false)
    private Date createTime;
}
