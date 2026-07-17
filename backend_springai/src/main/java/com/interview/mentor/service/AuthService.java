package com.interview.mentor.service;

import com.interview.mentor.entity.dto.req.RegisterRequest;
import com.interview.mentor.entity.dto.resp.AuthResponse;
import org.springframework.security.core.Authentication;

public interface AuthService {

    AuthResponse login(Authentication authentication);

    AuthResponse register(RegisterRequest request);

    AuthResponse refreshToken(String refreshToken);
}
