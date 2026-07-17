package com.interview.mentor.controller;

import com.interview.mentor.entity.dto.req.LoginRequest;
import com.interview.mentor.entity.dto.req.RegisterRequest;
import com.interview.mentor.entity.dto.resp.AuthResponse;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.security.JwtTokenProvider;
import com.interview.mentor.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final JwtTokenProvider tokenProvider;
    private final AuthService authService;

    public AuthController(AuthenticationManager authenticationManager,
                          JwtTokenProvider tokenProvider,
                          AuthService authService) {
        this.authenticationManager = authenticationManager;
        this.tokenProvider = tokenProvider;
        this.authService = authService;
    }

    @PostMapping("/login")
    public ResponseEntity<Result<AuthResponse>> login(@Valid @RequestBody LoginRequest request) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.getUsername(), request.getPassword()));

        AuthResponse response = authService.login(authentication);
        return ResponseEntity.ok(Result.success(response));
    }

    @PostMapping("/register")
    public ResponseEntity<Result<AuthResponse>> register(@Valid @RequestBody RegisterRequest request) {
        AuthResponse response = authService.register(request);
        return ResponseEntity.ok(Result.success(response));
    }

    @PostMapping("/refresh")
    public ResponseEntity<Result<AuthResponse>> refreshToken(@RequestParam String refreshToken) {
        AuthResponse response = authService.refreshToken(refreshToken);
        return ResponseEntity.ok(Result.success(response));
    }
}
