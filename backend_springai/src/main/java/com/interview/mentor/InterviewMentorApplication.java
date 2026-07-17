package com.interview.mentor;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@MapperScan("com.interview.mentor.mapper")
@EnableAsync
@EnableScheduling
public class InterviewMentorApplication {

    public static void main(String[] args) {
        SpringApplication.run(InterviewMentorApplication.class, args);
    }
}
