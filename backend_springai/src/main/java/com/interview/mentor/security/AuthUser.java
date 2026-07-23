package com.interview.mentor.security;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.User;

import java.util.Collection;

/**
 * 携带业务 userId 的认证 principal。
 *
 * <p>继承 Spring {@link User}（保留 username/password/authorities 的既有语义），
 * 额外携带 {@code userId}。因 CustomUserDetailsService 加载认证信息时本就查出了完整用户，
 * userId 顺手带上，控制器即可从 Authentication 直接取，无需再查库或改 token。
 */
public class AuthUser extends User {

    private final Long userId;

    public AuthUser(Long userId,
                    String username,
                    String password,
                    Collection<? extends GrantedAuthority> authorities) {
        super(username, password, authorities);
        this.userId = userId;
    }

    public Long getUserId() {
        return userId;
    }
}
