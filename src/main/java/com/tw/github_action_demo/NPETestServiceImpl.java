package com.tw.github_action_demo;

public class NPETestServiceImpl {

    public void testNPE() {
        Integer p = null;
        System.out.println(p.compareTo(10));
    }
}
