package com.tw.github_action_demo;

import java.util.Optional;
import java.util.logging.Logger;

public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Integer p = null;
        Optional.ofNullable(p)
                .ifPresent(value -> LOGGER.info(String.valueOf(value.compareTo(10))));
    }
}