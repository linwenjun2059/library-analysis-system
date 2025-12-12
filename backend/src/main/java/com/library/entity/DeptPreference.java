package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 院系偏好表实体
 */
@Data
@TableName("dept_preference")
public class DeptPreference implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 院系
     */
    @TableId
    private String dept;

    /**
     * 最喜欢的主题
     */
    private String favoriteSubject;

    /**
     * 主题借阅次数
     */
    private Long subjectLendCount;

    /**
     * 总借阅次数
     */
    private Long totalLendCount;

    /**
     * 偏好率
     */
    private Double preferenceRate;
}
