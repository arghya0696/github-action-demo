package com.tw.github_action_demo;

import java.util.Optional;
import java.util.logging.Logger;
import org.springframework.stereotype.Service;


@Service
public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Optional<Integer> p = Optional.ofNullable(null);
        p.ifPresent(value -> System.out.println(value.compareTo(10)));
    }
}