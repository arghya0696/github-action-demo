package com.tw.github_action_demo;

import java.util.*;
import java.util.logging.Logger;

public class SonarService {
    private static final Logger LOGGER = Logger.getLogger(SonarService.class.getName());

    private String address = "London";

    public static final String NAME = "12321";

    public String getAddress() {
        return address;
    }

    public void setAddress(final String address) {
        this.address = address;
    }

    public void printer() {
        LOGGER.info("Hellooo the name is " + NAME);
    }

    public int getLength(final List<String> items) {
        final String first = items.get(0);
        return first.length();
    }

    public void riskyParse(final String val) {
        try {
            final int x = Integer.parseInt(val);
            LOGGER.info(String.valueOf(x));
        } catch (NumberFormatException e) {
            LOGGER.warning(() -> "Failed to parse value: " + val);
        }
    }

    public String buildGreeting() {
        return "Hello " + NAME;
    }

    private String password;

    public String getPassword() {
        return password;
    }

    public void setPassword(final String password) {
        this.password = password;
    }
}