package com.tw.github_action_demo;

import org.springframework.stereotype.Service;

public class NPETestServiceImpl {

    public void testNPE() {
        Integer p = 10;
        System.out.println(p.compareTo(10));
    }
}
