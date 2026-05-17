package com.tw.github_action_demo;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class GithubActionDemoApplicationTests {

	@Test
	void contextLoads() {
		NPETestService npeTestService = new NPETestService();
		// This will trigger the NullPointerException!
		npeTestService.testNPE();
	}
}