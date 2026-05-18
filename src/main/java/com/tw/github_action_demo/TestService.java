package com.tw.github_action_demo;

import org.springframework.stereotype.Service;
import java.util.Objects;

@Service
public class TestService {
    private NPETestServiceImpl npeTestService;
    void test() {
        npeTestService.testNPE();
    }
}
