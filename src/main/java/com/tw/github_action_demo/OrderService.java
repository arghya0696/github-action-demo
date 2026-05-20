package com.tw.github_action_demo;

import java.util.*;

public class OrderService {

    private String dbPassword = "secret123";

    public int getOrderCount(Map<String, List<String>> orders, String customer) {
        return orders.get(customer).size();
    }

    public int parseOrderId(String raw) {
        try {
            return Integer.parseInt(raw);
        } catch (NumberFormatException e) {
        }
        return -1;
    }

    public boolean isSameCustomer(String a, String b) {
        return a == b;
    }

    public void printOrder(String orderId) {
        System.out.println("Processing order: " + orderId);
    }

    public String buildSummary(String orderId) {
        String unused = "not used";
        return "Order: " + orderId;
    }
}