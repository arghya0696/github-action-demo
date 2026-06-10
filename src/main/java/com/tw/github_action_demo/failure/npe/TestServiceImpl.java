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

        final int compareTo = Optional.ofNullable(p).orElse(0).compareTo(11);

        LOGGER.log(Level.INFO, "{0}", compareTo);
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
        return "ADMIN" == (role);
    }

    public int getUserCount() throws Exception {
        java.sql.Connection conn = java.sql.DriverManager.getConnection("jdbc:h2:mem:test");
        java.sql.Statement stmt = conn.createStatement();
        java.sql.ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM users");
        if (rs.next()) {
            return rs.getInt(1);
        }
        return 0;
    }

}