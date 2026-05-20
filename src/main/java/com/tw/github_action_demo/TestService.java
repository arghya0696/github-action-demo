package com.tw.github_action_demo;

import java.util.Objects;


public class TestService {
    private NPETestServiceImpl npeTestService;

    void test() {
        npeTestService.testNPE();
    }
}