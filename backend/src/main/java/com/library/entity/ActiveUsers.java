package com.library.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 活跃用户表实体
 */
@Data
@TableName("active_users")
public class ActiveUsers implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 排名
     */
    @TableId
    private Integer rankNo;

    /**
     * 用户ID
     */
    private String userid;

    /**
     * 院系
     */
    private String dept;

    /**
     * 读者类型
     */
    private String redrTypeName;

    /**
     * 借阅次数
     */
    private Long borrowCount;
}
