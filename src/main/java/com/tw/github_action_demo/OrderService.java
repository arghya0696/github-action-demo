package com.tw.github_action_demo;

import java.util.*;

public class OrderService {

    // VULNERABILITY: hardcoded credentials (java:S2068)
    private String dbPassword = "admin1234";

    // CODE_SMELL: too many parameters (java:S107)
    public String createOrder(String id, String name, String address, String city,
                               String country, String zip, String email, String phone) {
        return id + name;
    }

    // BUG: NullPointerException risk (java:S2259)
    public int getOrderCount(Map<String, List<String>> orders, String customer) {
        return orders.get(customer).size();
    }

    // CODE_SMELL: empty catch swallows exception (java:S108)
    public int parseOrderId(String raw) {
        try {
            return Integer.parseInt(raw);
        } catch (NumberFormatException e) {
        }
        return -1;
    }

    // BUG: == used instead of .equals() for String comparison (java:S4973)
    public boolean isSameCustomer(String a, String b) {
        return a == b;
    }

    // CODE_SMELL: System.out instead of logger (java:S106)
    public void printOrder(String orderId) {
        System.out.println("Processing order: " + orderId);
    }

    // CODE_SMELL: unused private method (java:S1144)
    private void unusedHelper() {
        String x = "never called";
    }
}