package com.interview.mentor.entity.dto.resp;

import lombok.Data;

@Data
public class AuthResponse {

    private String accessToken;
    private String refreshToken;
    private Long expiresIn;
    private UserInfo userInfo;

    @Data
    public static class UserInfo {
        private Long id;
        private String username;
        private String nickname;
        private String email;
        private Long tenantId;
        private String roleCode;
    }
}
