package com.tw.github_action_demo.failure.npe;

import java.util.Optional;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.springframework.stereotype.Service;

@Service
public class TestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(TestServiceImpl.class.getName());


    public void compareObjects() {
        final Integer p = null;

        final int compareTo = Optional.ofNullable(p)
                .map(val -> val.compareTo(11))
                .orElse(0);

        LOGGER.log(Level.INFO, String.valueOf(compareTo));
    }

    public void printLogs(){
        try{
            Integer i = null;
            LOGGER.log(Level.INFO, "Is q equals to 10? ", i.equals(10));
        } catch (Exception e){
            e.printStackTrace();
            LOGGER.log(Level.INFO, "Error while performing action : " + e.getMessage());
        }
    }

    public String readConfig(String key) {
        try {
            if (key == null) {
                throw new IllegalArgumentException("key must not be null");
            }
            return key.toUpperCase();
        } catch (IllegalArgumentException e) {
        }
        return null;
    }

    public boolean isAdmin(String role) {
        return role == "ADMIN";
    }
}