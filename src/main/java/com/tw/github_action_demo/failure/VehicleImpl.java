package com.tw.github_action_demo.failure;

public class VehicleImpl {

    public void testVehicle() {
        Vehicle myVehicle = new Bike();

        if (myVehicle instanceof Car myCar) {
            myCar.drive();
        } else if (myVehicle instanceof Bike myBike) {
            myBike.ride();
        }
    }
}