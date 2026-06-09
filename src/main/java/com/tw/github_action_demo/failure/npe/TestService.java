package com.tw.github_action_demo.failure.npe;

import org.springframework.stereotype.Service;

@Service
public class TestService {

    private final TestServiceImpl testService;

    public TestService(final TestServiceImpl npeTestService) {
        this.testService = java.util.Objects.requireNonNull(npeTestService);
    }

    public void test() {
        testService.compareObjects();
    }
}