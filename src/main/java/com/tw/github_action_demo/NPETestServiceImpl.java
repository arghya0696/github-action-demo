package com.tw.github_action_demo;

import java.util.Optional;
import java.util.logging.Level;
import java.util.logging.Logger;


public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Integer p = null;

//            final Integer q =  null;
//            LOGGER.log(Level.INFO, "Is q equals to 10? ", q.equals(10));

        final int compareTo = Optional.ofNullable(p)
                .orElse(0)
                .compareTo(10);

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
}