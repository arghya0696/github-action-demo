package com.tw.github_action_demo;

import java.util.logging.Logger;
import org.springframework.stereotype.Service;


@Service
public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Integer p = null;
        LOGGER.info(String.valueOf(java.util.Optional.ofNullable(p).map(v -> v.compareTo(10)).orElse(null)));
    }
}