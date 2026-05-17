package com.tw.github_action_demo;

public class NPETestService {

    public void testNPE() {
        Integer p = 11;
        System.out.println(p.compareTo(10));
    }
}

public String processData(String input) {
    return input.toUpperCase();  // input could be null!
}