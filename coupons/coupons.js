const api = require('../../utils/api.js');

Page({
  data: {
    activeTab: 'available',
    coupons: []
  },

  onLoad() {
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
    
    this.loadCoupons();
  },

  loadCoupons: function() {
    wx.showLoading({
      title: '加载中...'
    });
    
    const params = {};
    if (this.data.activeTab !== 'all') {
      params.status = this.data.activeTab;
    }
    
    api.get('/coupons', params).then(res => {
      const serverCoupons = res.data || [];
      if (serverCoupons.length > 0) {
        this.setData({
          coupons: serverCoupons
        });
        wx.hideLoading();
      } else {
        this.loadLocalCoupons();
      }
    }).catch(err => {
      console.error('获取优惠券列表失败:', err);
      this.loadLocalCoupons();
    });
  },

  loadLocalCoupons: function() {
    try {
      let myCoupons = wx.getStorageSync('myCoupons') || [];
      
      if (this.data.activeTab !== 'all') {
        myCoupons = myCoupons.filter(item => item.status === this.data.activeTab);
      }
      
      this.setData({
        coupons: myCoupons
      });
      wx.hideLoading();
    } catch (e) {
      console.error('读取本地优惠券失败:', e);
      this.setData({
        coupons: []
      });
      wx.hideLoading();
    }
  },

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
    this.loadCoupons();
  },

  useCoupon: function(e) {
    const couponId = e.currentTarget.dataset.id;
    const coupon = this.data.coupons.find(item => item.id === couponId);
    
    if (!coupon) {
      wx.showToast({
        title: '优惠券不存在',
        icon: 'none'
      });
      return;
    }
    
    wx.showModal({
      title: '使用优惠券',
      content: '是否前往商城使用此优惠券？\n\n优惠券：' + coupon.name + '\n优惠金额：¥' + (coupon.amount || coupon.value),
      confirmText: '去商城',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          wx.switchTab({
            url: '/pages/shop/shop'
          });
        }
      }
    });
  },

  viewDetail: function(e) {
    const couponId = e.currentTarget.dataset.id;
    wx.showToast({
      title: '优惠券详情功能开发中',
      icon: 'none'
    });
  },

  goToShop: function() {
    wx.switchTab({
      url: '/pages/shop/shop'
    });
  },

  onPullDownRefresh() {
    this.loadCoupons();
    wx.stopPullDownRefresh();
  },

  onShareAppMessage() {
    return {
      title: '我的优惠券',
      path: '/pages/coupons/coupons'
    };
  }
});