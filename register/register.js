const api = require('../../utils/api.js');

Page({
  data: {
    phone: '',
    nickname: '',
    password: '',
    confirmPassword: '',
    loading: false,
    canSubmit: false
  },

  onLoad() {
    this.checkLogin();
  },

  checkLogin() {
    const token = wx.getStorageSync('token');
    if (token) {
      wx.reLaunch({
        url: '/pages/index/index'
      });
    }
  },

  onPhoneInput(e) {
    const phone = e.detail.value;
    this.setData({ phone });
    this.checkCanSubmit();
  },

  onNicknameInput(e) {
    const nickname = e.detail.value;
    this.setData({ nickname });
    this.checkCanSubmit();
  },

  onPasswordInput(e) {
    const password = e.detail.value;
    this.setData({ password });
    this.checkCanSubmit();
  },

  onConfirmPasswordInput(e) {
    const confirmPassword = e.detail.value;
    this.setData({ confirmPassword });
    this.checkCanSubmit();
  },

  checkCanSubmit() {
    const { phone, nickname, password, confirmPassword } = this.data;
    const phoneValid = /^1[3-9]\d{9}$/.test(phone);
    const nicknameValid = nickname.trim().length >= 2;
    const passwordValid = password.length >= 6 && password.length <= 20;
    const confirmValid = password === confirmPassword && confirmPassword.length > 0;
    this.setData({ canSubmit: phoneValid && nicknameValid && passwordValid && confirmValid });
  },

  register() {
    const that = this;
    const { phone, nickname, password, confirmPassword, loading, canSubmit } = that.data;
    
    if (loading || !canSubmit) {
      return;
    }

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({
        title: '请输入正确的手机号',
        icon: 'none'
      });
      return;
    }

    if (nickname.trim().length < 2) {
      wx.showToast({
        title: '昵称至少2个字符',
        icon: 'none'
      });
      return;
    }

    if (password.length < 6) {
      wx.showToast({
        title: '密码至少6位',
        icon: 'none'
      });
      return;
    }

    if (password.length > 20) {
      wx.showToast({
        title: '密码最多20位',
        icon: 'none'
      });
      return;
    }

    if (password !== confirmPassword) {
      wx.showToast({
        title: '两次密码不一致',
        icon: 'none'
      });
      return;
    }
    
    that.setData({ loading: true });
    
    wx.showLoading({
      title: '注册中...'
    });
    
    api.post('/auth/register', {
      phone: phone,
      nickname: nickname.trim(),
      password: password
    }).then(response => {
      wx.hideLoading();
      
      wx.showToast({
        title: '注册成功',
        icon: 'success',
        duration: 1500
      });
      
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }).catch(err => {
      wx.hideLoading();
      console.error('注册失败:', err);
      wx.showToast({
        title: err.message || '注册失败，请重试',
        icon: 'none'
      });
      that.setData({ loading: false });
    });
  },

  goToLogin() {
    wx.navigateBack();
  }
});
