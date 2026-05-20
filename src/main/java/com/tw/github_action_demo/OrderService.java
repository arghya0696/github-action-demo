package com.tw.github_action_demo;

import java.util.*;
import java.util.logging.Logger;

public class OrderService {

    private static final Logger LOGGER = Logger.getLogger(OrderService.class.getName());

    // CODE_SMELL: too many parameters reduced by introducing an OrderRequest record
    public record OrderRequest(String id, String name) {}

    public String createOrder(final OrderRequest request) {
        Objects.requireNonNull(request, "request must not be null");
        return request.id() + request.name();
    }

    // BUG: NullPointerException risk (java:S2259)
    public int getOrderCount(final Map<String, List<String>> orders, final String customer) {
        return Optional.ofNullable(orders.get(customer))
                .map(List::size)
                .orElse(0);
    }

    // CODE_SMELL: empty catch swallows exception (java:S108)
    public int parseOrderId(final String raw) {
        try {
            return Integer.parseInt(raw);
        } catch (NumberFormatException e) {
            LOGGER.warning("Failed to parse order id: " + raw);
        }
        return -1;
    }

    // BUG: == used instead of .equals() for String comparison (java:S4973)
    public boolean isSameCustomer(final String a, final String b) {
        return Objects.equals(a, b);
    }

    // CODE_SMELL: System.out instead of logger (java:S106)
    public void printOrder(final String orderId) {
        LOGGER.info("Processing order: " + orderId);
    }
}