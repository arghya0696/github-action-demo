package com.tw.github_action_demo.controller;

import com.tw.github_action_demo.NPETestServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ErrorLogsController {

    @Autowired
    NPETestServiceImpl testService;

    @GetMapping("/logs")
    public void getLogs() {
        testService.printLogs();
    }
}