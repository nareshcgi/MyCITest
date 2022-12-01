package com.asc.springboot;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * ESS/ESP Sample Spring Boot application. Uses default Spring Boot Rest Controller.
 *
 * @author NSubramanyan
 */
@RestController
public class ASCSpringBootController {

    @GetMapping("/")
    public String sayHello() {
        return "Greetings from Spring Boot!";
    }
}
