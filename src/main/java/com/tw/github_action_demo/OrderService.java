package com.tw.github_action_demo;

import java.util.*;
import java.util.logging.Logger;

public class OrderService {

    private static final Logger LOGGER = Logger.getLogger(OrderService.class.getName());

    private static final double DISCOUNT_FACTOR = 0.9;

    // S2259 BUG: NullPointerException if orders.get(customer) returns null
    public int getOrderCount(Map<String, List<String>> orders, String customer) {
        return Optional.ofNullable(orders.get(customer))
                .map(List::size)
                .orElse(0);
    }

    // S108 CODE_SMELL: empty catch block silently swallows exception
    // S2447 BUG: method can return null but return type is Integer (boxed)
    public Optional<Integer> parseOrderId(String raw) {
        try {
            return Optional.of(Integer.parseInt(raw));
        } catch (NumberFormatException e) {
            // Return empty Optional when the raw string is not a valid integer
        }
        return Optional.empty();
    }

    // S2259 BUG: NullPointerException if parameter 'a' is null
    public boolean isSameCustomer(String a, String b) {
        Objects.requireNonNull(a, "Customer 'a' must not be null");
        return a.equals(b);
    }

    // S106 CODE_SMELL: use logger instead of System.out.println
    public void printOrder(String orderId) {
        LOGGER.info(() -> "Processing order: " + orderId);
    }

    // S1643 CODE_SMELL: string concatenation inside a loop, use StringBuilder
    public String buildSummary(List<String> orderIds) {
        final StringBuilder result = new StringBuilder();
        for (final String id : orderIds) {
            result.append("Order: ").append(id).append("\n");
        }
        return result.toString();
    }

    // S4973 BUG: strings compared with == instead of .equals()
    public boolean isSpecialOrder(String orderId) {
        return "SPECIAL".equals(orderId);
    }

    // S109 CODE_SMELL: magic number 0.9 — use a named constant
    public double applyDiscount(double price) {
        return price * DISCOUNT_FACTOR;
    }
}