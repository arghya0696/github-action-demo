package com.tw.github_action_demo;

import java.util.logging.Logger;
import org.springframework.stereotype.Service;


@Service
public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Integer p = null;
        if (LOGGER.isLoggable(java.util.logging.Level.INFO)) {
            final String value = String.valueOf(java.util.Optional.ofNullable(p).map(v -> v.compareTo(10)).orElse(null));
            LOGGER.info(value);
        }
    }
}