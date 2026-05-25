package com.tw.github_action_demo;

import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.logging.Logger;

@Service
public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Optional<Integer> p = Optional.ofNullable(10);

        int compareTo = p.map(value -> value.compareTo(10))
                .orElseThrow(() -> new IllegalArgumentException("Value must not be null for comparison"));

        System.out.println(compareTo);
    }
}