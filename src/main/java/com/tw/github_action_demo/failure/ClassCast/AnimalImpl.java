package com.tw.github_action_demo.failure.ClassCast;

public class AnimalImpl {

    public void testClassCastException() {
        final Animal myPet = new Dog();

        if (myPet instanceof Cat myCat) {
            // Safe cast - use myCat here
        } else if (myPet instanceof Dog myDog) {
            // myPet is a Dog, handle accordingly
        }
    }
}
