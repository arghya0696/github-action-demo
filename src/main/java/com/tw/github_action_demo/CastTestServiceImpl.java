package com.tw.github_action_demo;

import org.springframework.stereotype.Component;

import java.util.logging.Logger;


@Component
public class CastTestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(CastTestServiceImpl.class.getName());

    public void testClassCast() {
        final Object obj = Integer.valueOf(10); // obj is an Integer

        final String str = switch (obj) {
            case Integer i -> String.valueOf(i);
            case String s -> s;
            default -> obj.toString();
        };

        LOGGER.info(str);

    }
}