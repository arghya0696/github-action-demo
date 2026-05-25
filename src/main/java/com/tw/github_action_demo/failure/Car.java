package com.tw.github_action_demo.failure;

import java.util.logging.Logger;

public class Car extends Vehicle {
    private static final Logger LOGGER = Logger.getLogger(Car.class.getName());

    public void drive() { LOGGER.info("Driving a car"); }
}