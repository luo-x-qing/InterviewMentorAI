package com.interview.mentor.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.interview.mentor.entity.User;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.exception.BusinessException;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.interview.mentor.entity.User;
import com.interview.mentor.entity.dto.resp.Result;
import com.interview.mentor.exception.BusinessException;
import com.interview.mentor.mapper.UserMapper;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;

@RestController
@RequestMapping("/user")
public class UserController {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;

    public UserController(UserMapper userMapper,
                          PasswordEncoder passwordEncoder) {
        this.userMapper = userMapper;
        this.passwordEncoder = passwordEncoder;
    }

    /**
     * 获取当前用户信息
     */
    @GetMapping("/profile")
    public Result<User> getProfile(Authentication authentication) {
        String username = authentication.getName();
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        if (user == null) {
            throw new BusinessException(404, "用户不存在");
        }
        user.setPassword(null); // 脱敏
        return Result.success(user);
    }

    /**
     * 修改个人信息
     */
    @PutMapping("/profile")
    public Result<User> updateProfile(@RequestBody Map<String, String> request,
                                       Authentication authentication) {
        String username = authentication.getName();
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        if (user == null) {
            throw new BusinessException(404, "用户不存在");
        }

        if (request.containsKey("nickname")) {
            user.setNickname(request.get("nickname"));
        }
        if (request.containsKey("email")) {
            user.setEmail(request.get("email"));
        }
        if (request.containsKey("phone")) {
            user.setPhone(request.get("phone"));
        }
        if (request.containsKey("avatarUrl")) {
            user.setAvatarUrl(request.get("avatarUrl"));
        }
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);

        user.setPassword(null);
        return Result.success(user);
    }

    /**
     * 修改密码
     */
    @PutMapping("/password")
    public Result<Void> changePassword(@RequestBody Map<String, String> request,
                                        Authentication authentication) {
        String username = authentication.getName();
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>().eq(User::getUsername, username));
        if (user == null) {
            throw new BusinessException(404, "用户不存在");
        }

        String oldPassword = request.get("oldPassword");
        String newPassword = request.get("newPassword");

        if (!passwordEncoder.matches(oldPassword, user.getPassword())) {
            throw new BusinessException(400, "原密码错误");
        }

        user.setPassword(passwordEncoder.encode(newPassword));
        user.setUpdatedAt(LocalDateTime.now());
        userMapper.updateById(user);

        return Result.success();
    }
}
