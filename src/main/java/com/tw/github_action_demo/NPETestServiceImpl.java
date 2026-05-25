package com.tw.github_action_demo;

import org.springframework.stereotype.Service;
import java.util.Optional;
import java.util.logging.Level;
import java.util.logging.Logger;


@Service
public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Integer p = 42;

        final int compareTo = Optional.ofNullable(p)
                .map(value -> value.compareTo(10))
                .orElseThrow(() -> new IllegalArgumentException("Value 'p' must not be null"));

        LOGGER.log(Level.INFO, String.valueOf(compareTo));
    }
}