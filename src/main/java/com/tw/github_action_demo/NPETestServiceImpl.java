package com.tw.github_action_demo;

import org.springframework.stereotype.Service;
import java.util.Optional;
import java.util.logging.Logger;


@Service
public class NPETestServiceImpl {

    public void testNPE() {
        final Integer p = 42;

        final int compareTo = Optional.ofNullable(p)
                .map(value -> value.compareTo(10))
                .orElseThrow(() -> new IllegalArgumentException("Value 'p' must not be null"));

        System.out.println(compareTo);
    }
}