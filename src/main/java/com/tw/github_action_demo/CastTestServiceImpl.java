package com.tw.github_action_demo;

import org.springframework.stereotype.Component;


@Component
public class CastTestServiceImpl {

    public void testClassCast() {
        final Object x = Integer.valueOf(0);
        System.out.println(String.valueOf(x));
    }
}