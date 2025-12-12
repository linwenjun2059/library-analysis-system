package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 专业阅读特征表实体
 */
@Data
@TableName("major_reading_profile")
public class MajorReadingProfile implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 院系(复合主键之一)
     */
    private String dept;

    /**
     * 专业
     */
    private String occupation;

    /**
     * 学生数量
     */
    private Long studentCount;

    /**
     * 总借阅量
     */
    private Long totalBorrowCount;

    /**
     * 人均借阅量
     */
    private Double avgBorrowPerStudent;

    /**
     * 核心学科TOP5(JSON数组)
     */
    private String coreSubjects;

    /**
     * 跨学科借阅TOP3(JSON数组)
     */
    private String crossSubjects;

    /**
     * 阅读广度得分
     */
    private Double readingBreadthScore;

    /**
     * 热门书目TOP10(JSON数组)
     */
    private String popularBooks;
}
