package com.tw.github_action_demo.failure.classcast;

public class AnimalImpl {

    public void testClassCastException() {
        final Animal myPet = new Dog();

        if (myPet instanceof Cat) {
            // Safe cast - use myCat here
        } else if (myPet instanceof Dog) {
            // myPet is a Dog, handle accordingly
        }
    }
}