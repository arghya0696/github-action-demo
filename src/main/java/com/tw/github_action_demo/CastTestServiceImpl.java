package com.tw.github_action_demo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;


@Component
public class CastTestServiceImpl {

    private static final Logger logger = LoggerFactory.getLogger(CastTestServiceImpl.class);

    public void testClassCast() {
        final Object x = Integer.valueOf(0);
        logger.info(String.valueOf(x));
    }
}