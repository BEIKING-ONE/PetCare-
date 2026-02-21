const api = require('../../utils/api.js');

Page({
  data: {
    addresses: [],
    selectMode: false
  },

  onLoad(options) {
    this.setData({ selectMode: options.select === '1' });
    this.checkLogin();
  },

  onShow() {
    this.checkLogin();
  },

  checkLogin: function() {
    const token = wx.getStorageSync('token');
    if (!token) {
      wx.reLaunch({
        url: '/pages/login/login'
      });
      return;
    }
    
    this.loadAddresses();
  },

  loadAddresses: function() {
    wx.showLoading({
      title: '加载中...'
    });
    api.get('/addresses').then(res => {
      this.setData({
        addresses: res.data || []
      });
      wx.hideLoading();
    }).catch(err => {
      console.error('获取地址列表失败:', err);
      wx.hideLoading();
      this.setData({
        addresses: []
      });
    });
  },

  addAddress: function() {
    wx.navigateTo({
      url: '/pages/address-add/address-add'
    });
  },

  editAddress: function(e) {
    const addressId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/address-add/address-add?id=' + addressId
    });
  },

  setDefault: function(e) {
    const addressId = e.currentTarget.dataset.id;
    wx.showLoading({
      title: '处理中...'
    });
    api.put('/addresses/' + addressId + '/default').then(() => {
      wx.hideLoading();
      wx.showToast({
        title: '已设置为默认地址',
        icon: 'success'
      });
      this.loadAddresses();
    }).catch(err => {
      console.error('设置默认地址失败:', err);
      wx.hideLoading();
    });
  },

  deleteAddress: function(e) {
    const addressId = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确定要删除此地址吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '处理中...'
          });
          api.del('/addresses/' + addressId).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '地址已删除',
              icon: 'success'
            });
            this.loadAddresses();
          }).catch(err => {
            console.error('删除地址失败:', err);
            wx.hideLoading();
          });
        }
      }
    });
  },

  onPullDownRefresh() {
    this.loadAddresses();
    wx.stopPullDownRefresh();
  },

  selectAddress: function(e) {
    const addressId = e.currentTarget.dataset.id;
    const address = this.data.addresses.find(item => item.id == addressId);
    
    if (address) {
      const pages = getCurrentPages();
      const prevPage = pages[pages.length - 2];
      
      if (prevPage && prevPage.route === 'pages/order-create/order-create') {
        prevPage.setData({
          selectedAddress: address
        });
        wx.navigateBack();
      }
    }
  },

  onShareAppMessage() {
    return {
      title: '收货地址',
      path: '/pages/address/address'
    };
  }
});