package com.tw.github_action_demo;

import org.springframework.stereotype.Component;

import java.util.logging.Logger;


@Component
public class CastTestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(CastTestServiceImpl.class.getName());

    public void testClassCast() {
        Object obj = Integer.valueOf(10); // obj is an Integer

        // This will throw java.lang.ClassCastException
        // because an Integer is not a String
        String str = (String) obj;

        LOGGER.info(str);
    }
}