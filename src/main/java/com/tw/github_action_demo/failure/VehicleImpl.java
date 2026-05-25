package com.tw.github_action_demo.failure;

public class VehicleImpl {

    public void testVehicle() {
        Vehicle myVehicle = new Bike();

        // 2. Dangerous Downcasting (CRASHES HERE)
        // You tell Java: "Trust me, this vehicle is a Car."
        // Java realizes at runtime it is actually a Bike, not a Car.
        Car myCar = (Car) myVehicle;

        myCar.drive();
    }
}
