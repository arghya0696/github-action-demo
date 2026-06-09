package com.tw.github_action_demo;

import com.tw.github_action_demo.failure.npe.TestService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class GithubActionDemoApplicationTests {

    @Autowired
    TestService testService;

    @Test
    void testNPE() {
        testService.test();
    }
}