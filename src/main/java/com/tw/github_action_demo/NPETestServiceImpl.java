package com.tw.github_action_demo;

import java.util.logging.Logger;


public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Integer p = null;

        int compareTo = p.compareTo(10);

        System.out.println(compareTo);
    }
}