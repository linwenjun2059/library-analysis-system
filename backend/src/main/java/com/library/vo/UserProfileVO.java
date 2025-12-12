package com.library.vo;

import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 用户画像VO
 */
@Data
public class UserProfileVO implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 用户ID
     */
    private String userid;

    /**
     * 用户类型
     */
    private String userType;

    /**
     * 院系
     */
    private String dept;

    /**
     * 专业
     */
    private String occupation;

    /**
     * 性别
     */
    private String gender;

    /**
     * 年龄段
     */
    private String ageGroup;

    /**
     * 借阅等级
     */
    private String borrowLevel;

    /**
     * 总借阅量
     */
    private Long totalBorrowCount;

    /**
     * 阅读广度
     */
    private Integer readingBreadth;

    /**
     * 偏好主题TOP3
     */
    private Object favoriteSubjects;

    /**
     * 偏好位置TOP3
     */
    private Object favoriteLocations;

    /**
     * 平均借阅天数
     */
    private Double avgBorrowDays;

    /**
     * 逾期率
     */
    private Double overdueRate;

    /**
     * 最后借阅日期
     */
    private Date lastBorrowDate;

    /**
     * 用户标签
     */
    private Object userTags;
}
