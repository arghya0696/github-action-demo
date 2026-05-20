package com.tw.github_action_demo;

import java.util.*;

public class SonarService {
    public String address = "London";

    public static final String name = "12321";

    public void printer() {
        System.out.println("Hellooo the name is " + name);
    }

    public int getLength(List<String> items) {
        String first = items.get(0);
        return first.length();
    }

    public void riskyParse(String val) {
        try {
            int x = Integer.parseInt(val);
            System.out.println(x);
        } catch (NumberFormatException e) {
        }
    }

    public String buildGreeting() {
        String unused = "this is never used";
        return "Hello " + name;
    }

    private String password = "superSecret123";
}
