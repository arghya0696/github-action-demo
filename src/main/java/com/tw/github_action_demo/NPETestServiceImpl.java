package com.tw.github_action_demo;

import org.springframework.stereotype.Service;
import java.util.Optional;
import java.util.logging.Logger;

@Service
public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Integer p = null;
        Optional.ofNullable(p).ifPresent(value -> LOGGER.info(String.valueOf(value.compareTo(10))));
    }
}