package com.interview.mentor.security;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.interview.mentor.entity.User;
import com.interview.mentor.mapper.UserMapper;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    private final UserMapper userMapper;

    public CustomUserDetailsService(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getUsername, username));

        if (user == null) {
            throw new UsernameNotFoundException("用户不存在: " + username);
        }

        if (user.getStatus() == 0) {
            throw new UsernameNotFoundException("用户已被禁用: " + username);
        }

        List<SimpleGrantedAuthority> authorities = userMapper.selectRoleCodesByUserId(user.getId())
                .stream()
                .map(SimpleGrantedAuthority::new)
                .toList();

        // 返回携带 userId 的 AuthUser：loadUserByUsername 本就加载了完整 User，userId 顺手带上
        return new AuthUser(
                user.getId(),
                user.getUsername(),
                user.getPassword(),
                authorities
        );
    }
}
