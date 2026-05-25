package com.tw.github_action_demo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;


@Component
public class CastTestServiceImpl {

    public void testClassCast() {
        Object x = Integer.valueOf(0);
        System.out.println(x.toString());
    }
}