package com.tw.github_action_demo;

import java.util.*;
import java.util.logging.Logger;

public class OrderService {

    private static final Logger logger = Logger.getLogger(OrderService.class.getName());

    public int getOrderCount(Map<String, List<String>> orders, String customer) {
        return orders.get(customer).size();
    }

    public int parseOrderId(String raw) {
        try {
            return Integer.parseInt(raw);
        } catch (NumberFormatException e) {
            // Return -1 to indicate invalid input when raw cannot be parsed as an integer
        }
        return -1;
    }

    public boolean isSameCustomer(String a, String b) {
        return a.equals(b);
    }

    public void printOrder(String orderId) {
        logger.info("Processing order: " + orderId);
    }

    public String buildSummary(String orderId) {
        return "Order: " + orderId;
    }
}