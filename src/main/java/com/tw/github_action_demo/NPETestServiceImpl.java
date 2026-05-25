package com.tw.github_action_demo;

import java.util.logging.Logger;


public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Integer p = null;
        LOGGER.info(String.valueOf(p.compareTo(10)));
    }
}