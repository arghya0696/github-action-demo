package com.tw.github_action_demo.failure;

import java.util.logging.Logger;

public class Bike extends Vehicle {
    private static final Logger LOGGER = Logger.getLogger(Bike.class.getName());

    void ride() { LOGGER.info("Riding a bike"); }
}