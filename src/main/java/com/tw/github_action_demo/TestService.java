package com.tw.github_action_demo;

import java.util.Objects;
import org.springframework.stereotype.Service;

@Service
public class TestService {
    private final NPETestServiceImpl npeTestService;
    public TestService(final NPETestServiceImpl npeTestService) {
        this.npeTestService = Objects.requireNonNull(npeTestService, "npeTestService must not be null");
    }
    void test() {
        npeTestService.testNPE();
    }
}