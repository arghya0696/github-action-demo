package com.tw.github_action_demo.controller;

import com.tw.github_action_demo.failure.npe.TestServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.nio.file.Files;
import java.nio.file.Path;

@RestController
public class ErrorLogsController {

    @Autowired
    TestServiceImpl testService;

    @Value("${logging.file.name:/tmp/app.log}")
    private String logFilePath;

    @GetMapping("/logs")
    public String getLogs() {
        testService.printLogs();
        try {
            Path path = Path.of(logFilePath);
            if (Files.exists(path)) {
                return Files.readString(path);
            }
            return "Log file not found at: " + logFilePath;
        } catch (Exception e) {
            return "Error reading log file: " + e.getMessage();
        }
    }
}