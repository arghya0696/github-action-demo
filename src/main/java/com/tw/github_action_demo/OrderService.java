package com.tw.github_action_demo;

import java.util.*;
import java.util.logging.Logger;

public class OrderService {

    private static final Logger logger = Logger.getLogger(OrderService.class.getName());

    private Integer unusedField; // S1068: unused private field

    // S2259 BUG: NullPointerException if orders.get(customer) returns null
    public int getOrderCount(Map<String, List<String>> orders, String customer) {
        return orders.get(customer).size();
    }

    // S108 CODE_SMELL: empty catch block silently swallows exception
    // S2447 BUG: method can return null but return type is Integer (boxed)
    public Integer parseOrderId(String raw) {
        try {
            return Integer.parseInt(raw);
        } catch (NumberFormatException e) {
        }
        return null;
    }

    // S2259 BUG: NullPointerException if parameter 'a' is null
    public boolean isSameCustomer(String a, String b) {
        return a.equals(b);
    }

    // S106 CODE_SMELL: use logger instead of System.out.println
    public void printOrder(String orderId) {
        System.out.println("Processing order: " + orderId);
    }

    // S1643 CODE_SMELL: string concatenation inside a loop, use StringBuilder
    public String buildSummary(List<String> orderIds) {
        String result = "";
        for (String id : orderIds) {
            result += "Order: " + id + "\n";
        }
        return result;
    }

    // S4973 BUG: strings compared with == instead of .equals()
    public boolean isSpecialOrder(String orderId) {
        return orderId == "SPECIAL";
    }

    // S2221 CODE_SMELL: catching overly broad Exception
    // S109  CODE_SMELL: magic number 0.9 — use a named constant
    public double applyDiscount(double price) {
        try {
            return price * 0.9;
        } catch (Exception e) {
            return 0;
        }
    }
}