package com.library.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.library.entity.RecentLendRecords;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 近期借阅记录Mapper
 */
@Mapper
public interface RecentLendRecordsMapper extends BaseMapper<RecentLendRecords> {

    /**
     * 分页查询用户借阅记录（关联图书信息）
     */
    @Select("SELECT r.*, b.title, b.author, b.publisher, b.subject, b.location_name " +
            "FROM recent_lend_records r " +
            "LEFT JOIN book_dimension b ON r.book_id = b.book_id " +
            "WHERE r.userid = #{userid} " +
            "ORDER BY r.lend_date DESC")
    Page<RecentLendRecords> selectUserRecordsWithBookInfo(Page<RecentLendRecords> page, @Param("userid") String userid);

    /**
     * 分页查询所有借阅记录（关联图书信息，带筛选条件）
     */
    @Select("<script>" +
            "SELECT r.*, b.title, b.author, b.publisher, b.subject, b.location_name " +
            "FROM recent_lend_records r " +
            "LEFT JOIN book_dimension b ON r.book_id = b.book_id " +
            "WHERE 1=1 " +
            "<if test='keyword != null and keyword != \"\"'>" +
            "  AND (r.userid LIKE CONCAT('%', #{keyword}, '%') " +
            "       OR r.book_id LIKE CONCAT('%', #{keyword}, '%') " +
            "       OR b.title LIKE CONCAT('%', #{keyword}, '%')) " +
            "</if>" +
            "<if test='startDate != null and startDate != \"\"'>" +
            "  AND r.lend_date &gt;= #{startDate} " +
            "</if>" +
            "<if test='endDate != null and endDate != \"\"'>" +
            "  AND r.lend_date &lt;= #{endDate} " +
            "</if>" +
            "<if test='returnStatus == \"returned\"'>" +
            "  AND r.ret_date IS NOT NULL " +
            "</if>" +
            "<if test='returnStatus == \"not_returned\"'>" +
            "  AND r.ret_date IS NULL " +
            "</if>" +
            "<if test='overdueStatus == \"overdue\"'>" +
            "  AND r.is_overdue = 1 " +
            "</if>" +
            "<if test='overdueStatus == \"normal\"'>" +
            "  AND r.is_overdue = 0 " +
            "</if>" +
            "ORDER BY r.lend_date DESC" +
            "</script>")
    Page<RecentLendRecords> selectAllRecordsWithBookInfo(
            Page<RecentLendRecords> page,
            @Param("keyword") String keyword,
            @Param("startDate") String startDate,
            @Param("endDate") String endDate,
            @Param("returnStatus") String returnStatus,
            @Param("overdueStatus") String overdueStatus
    );
}
