package com.interview.mentor.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.interview.mentor.entity.User;
import com.interview.mentor.entity.UserRole;
import com.interview.mentor.entity.dto.req.RegisterRequest;
import com.interview.mentor.entity.dto.resp.AuthResponse;
import com.interview.mentor.exception.BusinessException;
import com.interview.mentor.mapper.UserMapper;
import com.interview.mentor.mapper.UserRoleMapper;
import com.interview.mentor.security.JwtTokenProvider;
import com.interview.mentor.service.AuthService;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class AuthServiceImpl implements AuthService {

    private static final Long DEFAULT_TENANT_ID = 1L;
    private static final Long ROLE_TENANT_MEMBER_ID = 3L;

    private final JwtTokenProvider tokenProvider;
    private final UserMapper userMapper;
    private final UserRoleMapper userRoleMapper;
    private final PasswordEncoder passwordEncoder;

    public AuthServiceImpl(JwtTokenProvider tokenProvider,
                           UserMapper userMapper,
                           UserRoleMapper userRoleMapper,
                           PasswordEncoder passwordEncoder) {
        this.tokenProvider = tokenProvider;
        this.userMapper = userMapper;
        this.userRoleMapper = userRoleMapper;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public AuthResponse login(Authentication authentication) {
        UserDetails userDetails = (UserDetails) authentication.getPrincipal();
        String username = userDetails.getUsername();

        // 查询完整用户信息
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        if (user == null) {
            throw new BusinessException(401, "用户不存在");
        }

        // 更新最后登录时间
        user.setLastLoginAt(LocalDateTime.now());
        userMapper.updateById(user);

        // 查询用户角色
        List<String> roleCodes = userRoleMapper.selectRoleCodesByUserId(user.getId());
        String primaryRole = roleCodes.isEmpty() ? "TENANT_MEMBER" : roleCodes.get(0);

        // 构建带角色的 Authentication
        List<SimpleGrantedAuthority> authorities = roleCodes.stream()
                .map(SimpleGrantedAuthority::new)
                .toList();
        Authentication authWithRoles = new org.springframework.security.authentication
                .UsernamePasswordAuthenticationToken(userDetails, null, authorities);

        return buildAuthResponse(authWithRoles, user, primaryRole);
    }

    @Override
    @Transactional
    public AuthResponse register(RegisterRequest request) {
        // 检查用户名是否已存在
        Long count = userMapper.selectCount(
                new LambdaQueryWrapper<User>().eq(User::getUsername, request.getUsername()));
        if (count > 0) {
            throw new BusinessException(400, "用户名已存在");
        }

        // 创建用户
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setNickname(request.getNickname() != null ? request.getNickname() : request.getUsername());
        user.setEmail(request.getEmail());
        user.setPhone(request.getPhone());
        user.setTenantId(request.getTenantId() != null ? request.getTenantId() : DEFAULT_TENANT_ID);
        user.setStatus(1);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.insert(user);

        // 默认分配 TENANT_MEMBER 角色
        UserRole userRole = new UserRole();
        userRole.setUserId(user.getId());
        userRole.setRoleId(ROLE_TENANT_MEMBER_ID);
        userRoleMapper.insert(userRole);

        // 构建 Authentication（带角色权限）
        List<SimpleGrantedAuthority> authorities = List.of(
                new SimpleGrantedAuthority("TENANT_MEMBER"));
        Authentication authentication = new org.springframework.security.authentication
                .UsernamePasswordAuthenticationToken(
                        user.getUsername(), null, authorities);

        return buildAuthResponse(authentication, user, "TENANT_MEMBER");
    }

    @Override
    public AuthResponse refreshToken(String refreshToken) {
        if (!tokenProvider.validateToken(refreshToken)) {
            throw new BusinessException(401, "Refresh Token 无效或已过期");
        }

        String username = tokenProvider.getUsernameFromToken(refreshToken);

        // 查询用户及角色
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        if (user == null) {
            throw new BusinessException(401, "用户不存在");
        }

        List<String> roleCodes = userRoleMapper.selectRoleCodesByUserId(user.getId());
        String primaryRole = roleCodes.isEmpty() ? "TENANT_MEMBER" : roleCodes.get(0);
        List<SimpleGrantedAuthority> authorities = roleCodes.stream()
                .map(SimpleGrantedAuthority::new)
                .toList();

        Authentication authentication = new org.springframework.security.authentication
                .UsernamePasswordAuthenticationToken(
                        new org.springframework.security.core.userdetails.User(
                                username, user.getPassword(), authorities),
                        null, authorities);

        return buildAuthResponse(authentication, user, primaryRole);
    }

    private AuthResponse buildAuthResponse(Authentication authentication,
                                           User user,
                                           String roleCode) {
        String accessToken = tokenProvider.generateAccessToken(authentication, user.getTenantId());
        String refreshToken = tokenProvider.generateRefreshToken(authentication);

        AuthResponse response = new AuthResponse();
        response.setAccessToken(accessToken);
        response.setRefreshToken(refreshToken);
        response.setExpiresIn(tokenProvider.getAccessTokenExpiration());

        AuthResponse.UserInfo userInfo = new AuthResponse.UserInfo();
        userInfo.setId(user.getId());
        userInfo.setUsername(user.getUsername());
        userInfo.setNickname(user.getNickname());
        userInfo.setEmail(user.getEmail());
        userInfo.setTenantId(user.getTenantId());
        userInfo.setRoleCode(roleCode);
        response.setUserInfo(userInfo);

        return response;
    }
}
