package com.tw.github_action_demo.failure.ClassCast;

public class AnimalImpl {

    public void testClassCastException() {
        Animal myPet = new Dog();

        Dog myDog = (Dog) myPet;

        myDog.run();
    }
}