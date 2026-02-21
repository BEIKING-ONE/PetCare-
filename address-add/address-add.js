// pages/address-add/address-add.js
var api = require('../../utils/api.js');

Page({
  data: {
    id: null,
    name: '',
    phone: '',
    province: '',
    city: '',
    district: '',
    detail: '',
    isDefault: false,
    loading: false,
    submitting: false,
    region: []
  },

  onLoad: function(options) {
    this.checkLogin();
    if (options.id) {
      this.setData({ id: options.id });
      this.loadAddressDetail(options.id);
    }
  },

  checkLogin: function() {
    var token = wx.getStorageSync('token');
    if (!token) {
      wx.reLaunch({
        url: '/pages/login/login'
      });
      return;
    }
  },

  loadAddressDetail: function(addressId) {
    var that = this;
    wx.showLoading({
      title: '加载中...'
    });
    api.get('/addresses/' + addressId).then(function(res) {
      var address = res.data;
      that.setData({
        name: address.name,
        phone: address.phone,
        province: address.province,
        city: address.city,
        district: address.district,
        detail: address.detail,
        isDefault: address.is_default,
        region: [address.province, address.city, address.district]
      });
      wx.hideLoading();
    }).catch(function(err) {
      console.error('获取地址详情失败:', err);
      wx.hideLoading();
      wx.showToast({
        title: '获取地址失败',
        icon: 'none'
      });
    });
  },

  bindNameInput: function(e) {
    this.setData({ name: e.detail.value });
  },

  bindPhoneInput: function(e) {
    this.setData({ phone: e.detail.value });
  },

  bindRegionChange: function(e) {
    var region = e.detail.value;
    this.setData({
      region: region,
      province: region[0],
      city: region[1],
      district: region[2]
    });
  },

  bindDetailInput: function(e) {
    this.setData({ detail: e.detail.value });
  },

  toggleDefault: function(e) {
    this.setData({ isDefault: e.detail.value });
  },

  validateForm: function() {
    if (!this.data.name.trim()) {
      wx.showToast({ title: '请输入收货人姓名', icon: 'none' });
      return false;
    }
    if (!this.data.phone.trim()) {
      wx.showToast({ title: '请输入手机号码', icon: 'none' });
      return false;
    }
    if (!/^1[3-9]\d{9}$/.test(this.data.phone)) {
      wx.showToast({ title: '请输入正确的手机号码', icon: 'none' });
      return false;
    }
    if (!this.data.province) {
      wx.showToast({ title: '请选择省份', icon: 'none' });
      return false;
    }
    if (!this.data.city) {
      wx.showToast({ title: '请选择城市', icon: 'none' });
      return false;
    }
    if (!this.data.district) {
      wx.showToast({ title: '请选择区县', icon: 'none' });
      return false;
    }
    if (!this.data.detail.trim()) {
      wx.showToast({ title: '请输入详细地址', icon: 'none' });
      return false;
    }
    return true;
  },

  submitAddress: function() {
    var that = this;
    if (!that.validateForm()) {
      return;
    }
    if (that.data.submitting) {
      return;
    }
    that.setData({ submitting: true });
    var addressData = {
      name: that.data.name,
      phone: that.data.phone,
      province: that.data.province,
      city: that.data.city,
      district: that.data.district,
      detail: that.data.detail,
      is_default: that.data.isDefault
    };
    var promise = null;
    if (that.data.id) {
      promise = api.put('/addresses/' + that.data.id, addressData);
    } else {
      promise = api.post('/addresses', addressData);
    }
    promise.then(function(res) {
      that.setData({ submitting: false });
      wx.showToast({
        title: that.data.id ? '地址编辑成功' : '地址添加成功',
        icon: 'success'
      });
      setTimeout(function() {
        wx.navigateBack();
      }, 1500);
    }).catch(function(err) {
      console.error('提交地址失败:', err);
      that.setData({ submitting: false });
      wx.showToast({
        title: '操作失败，请重试',
        icon: 'none'
      });
    });
  },

  navigateBack: function() {
    wx.navigateBack();
  },

  onShareAppMessage: function() {
    return {
      title: '添加收货地址',
      path: '/pages/address-add/address-add'
    };
  }
});