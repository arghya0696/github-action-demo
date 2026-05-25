package com.tw.github_action_demo;

import org.springframework.stereotype.Component;

import java.util.logging.Logger;


@Component
public class CastTestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(CastTestServiceImpl.class.getName());

    public void testClassCast() {
        Object obj = Integer.valueOf(10); // obj is an Integer

        final String str = (obj instanceof Integer i) ? String.valueOf(i) : (String) obj;

        LOGGER.info(str);
    }
}