package com.tw.github_action_demo.failure.ClassCast;

class AnimalImpl {

    public void testClassCastException() {
        final Animal animal = new Dog();

        if (animal instanceof Cat cat) {
            cat.meow();
        } else if (animal instanceof Dog dog) {
            dog.bark();
        }
    }
}