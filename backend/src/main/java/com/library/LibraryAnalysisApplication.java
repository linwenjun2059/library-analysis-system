package com.library;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 图书馆借阅分析系统启动类
 */
@SpringBootApplication
@MapperScan("com.library.mapper")
public class LibraryAnalysisApplication {

    public static void main(String[] args) {
        SpringApplication.run(LibraryAnalysisApplication.class, args);
        System.out.println("\n========================================");
        System.out.println("图书馆借阅分析系统启动成功！");
        System.out.println("接口文档地址: http://localhost:8080/api/swagger-ui/index.html");
        System.out.println("Druid监控地址: http://localhost:8080/api/druid/index.html");
        System.out.println("========================================\n");
    }
}
