package com.tw.github_action_demo;

import org.springframework.stereotype.Service;

@Service
public class TestService {

    private NPETestServiceImpl npeTestService;

    void test() {
        npeTestService.testNPE();
    }
}
