package com.tw.github_action_demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class GithubActionDemoApplicationTests {

	@Autowired
	TestService testService;

	@Autowired
	CastTestServiceImpl castTestServiceImpl;

	@Test
	void testNPE() {

		testService.test();
	}

	@Test
	void testClassCast() {

		castTestServiceImpl.testClassCast();
	}

}
