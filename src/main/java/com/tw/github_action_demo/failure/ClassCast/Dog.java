package com.tw.github_action_demo.failure.ClassCast;

public class Dog implements Animal {
    @Override
    public void run() {
        System.out.println("Dog is running");
    }
}
