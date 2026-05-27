package com.tw.github_action_demo.failure.ClassCast;

public class AnimalImpl {

    public void testClassCastException() {
        Animal myPet = new Dog();

        if (myPet instanceof Cat myCat) {
            // use myCat here if needed
        }
    }
}