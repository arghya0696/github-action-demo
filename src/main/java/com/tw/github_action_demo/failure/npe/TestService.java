package com.tw.github_action_demo.failure.npe;

import org.springframework.stereotype.Service;

@Service
public class TestService {

    private final TestServiceImpl npeTestService;

    public TestService(final TestServiceImpl npeTestService) {
        this.npeTestService = java.util.Objects.requireNonNull(npeTestService);
    }

    public void test() {
        npeTestService.compareObjects();
    }
}