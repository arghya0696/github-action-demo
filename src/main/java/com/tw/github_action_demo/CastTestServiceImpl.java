package com.tw.github_action_demo;

import org.springframework.stereotype.Component;


@Component
public class CastTestServiceImpl {

    public void testClassCast() {
        Object x = new Integer(0);
        System.out.println((String)x);
    }
}