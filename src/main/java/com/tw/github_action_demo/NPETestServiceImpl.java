package com.tw.github_action_demo;

import java.util.Optional;

public class NPETestServiceImpl {

    public void testNPE() {
        final Integer p = null;
        System.out.println(p.compareTo(10));
    }
}