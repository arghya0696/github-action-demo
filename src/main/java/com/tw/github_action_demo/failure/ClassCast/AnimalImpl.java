package com.tw.github_action_demo.failure.ClassCast;

public class AnimalImpl {

    public void testClassCastException() {
        Animal myPet = new Dog();

        Cat myCat = (Cat) myPet;
    }
}
