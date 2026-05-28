package com.tw.github_action_demo;

import org.springframework.stereotype.Service;
import java.util.Optional;
import java.util.logging.Level;
import java.util.logging.Logger;


@Service
public class NPETestServiceImpl {

    private static final Logger LOGGER = Logger.getLogger(NPETestServiceImpl.class.getName());

    public void testNPE() {
        final Integer p = 5;

//            final Integer q =  null;
//            LOGGER.log(Level.INFO, "Is q equals to 10? ", q.equals(10));

        final int compareTo = Optional.ofNullable(p)
                .map(value -> value.compareTo(10))
                .orElseThrow(() -> new IllegalArgumentException("Value 'p' must not be null"));

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