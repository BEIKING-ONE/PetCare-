const api = require('../../utils/api.js');

Page({
  data: {
    coupons: [],
    loading: false
  },

  onLoad() {
    this.loadCoupons();
  },

  onShow() {
    this.loadCoupons();
  },

  loadCoupons: function() {
    this.setData({ loading: true });
    
    api.request({
      url: '/coupons/available',
      method: 'GET',
      silent: true
    }).then(res => {
      const coupons = res.data || [];
      if (coupons.length > 0) {
        this.setData({ 
          coupons: coupons,
          loading: false 
        });
      } else {
        this.loadMockCoupons();
      }
    }).catch(err => {
      console.error('获取优惠券列表失败:', err);
      this.loadMockCoupons();
    });
  },

  loadMockCoupons: function() {
    const mockCoupons = [
      {
        id: 1,
        name: '新人专享券',
        amount: 10,
        minAmount: 50,
        expireTime: '2024-12-31',
        received: false
      },
      {
        id: 2,
        name: '满100减20',
        amount: 20,
        minAmount: 100,
        expireTime: '2024-12-31',
        received: false
      },
      {
        id: 3,
        name: '满200减50',
        amount: 50,
        minAmount: 200,
        expireTime: '2024-12-31',
        received: false
      },
      {
        id: 4,
        name: '宠物用品专享',
        amount: 15,
        minAmount: 80,
        expireTime: '2024-12-31',
        received: false
      }
    ];
    
    const myCoupons = wx.getStorageSync('myCoupons') || [];
    const receivedIds = myCoupons.map(item => item.id);
    
    mockCoupons.forEach(item => {
      if (receivedIds.includes(item.id)) {
        item.received = true;
      }
    });
    
    this.setData({ 
      coupons: mockCoupons,
      loading: false 
    });
  },

  receiveCoupon: function(e) {
    const couponId = e.currentTarget.dataset.id;
    const token = wx.getStorageSync('token');
    
    if (!token) {
      wx.showModal({
        title: '提示',
        content: '请先登录后再领取优惠券',
        success: (res) => {
          if (res.confirm) {
            wx.switchTab({
              url: '/pages/profile/profile'
            });
          }
        }
      });
      return;
    }
    
    const coupon = this.data.coupons.find(item => item.id === couponId);
    if (!coupon) return;
    
    wx.showLoading({ title: '领取中...' });
    
    api.post('/coupons/' + couponId + '/receive').then(res => {
      wx.hideLoading();
      
      this.saveCouponToLocal(coupon);
      
      wx.showToast({
        title: '领取成功',
        icon: 'success'
      });
      
      const coupons = this.data.coupons.map(item => {
        if (item.id === couponId) {
          item.received = true;
        }
        return item;
      });
      this.setData({ coupons: coupons });
    }).catch(err => {
      wx.hideLoading();
      
      this.saveCouponToLocal(coupon);
      
      const coupons = this.data.coupons.map(item => {
        if (item.id === couponId) {
          item.received = true;
        }
        return item;
      });
      this.setData({ coupons: coupons });
      
      wx.showToast({
        title: '领取成功',
        icon: 'success'
      });
    });
  },

  saveCouponToLocal: function(coupon) {
    try {
      let myCoupons = wx.getStorageSync('myCoupons') || [];
      const exists = myCoupons.find(item => item.id === coupon.id);
      if (!exists) {
        myCoupons.push({
          id: coupon.id,
          name: coupon.name,
          amount: coupon.amount,
          minAmount: coupon.minAmount,
          expireTime: coupon.expireTime,
          status: 'available',
          receivedAt: new Date().toISOString()
        });
        wx.setStorageSync('myCoupons', myCoupons);
      }
    } catch (e) {
      console.error('保存优惠券到本地失败:', e);
    }
  },

  onPullDownRefresh() {
    this.loadCoupons();
    wx.stopPullDownRefresh();
  },

  onShareAppMessage() {
    return {
      title: '优惠券中心 - 宠物管家',
      path: '/pages/coupon-center/coupon-center'
    };
  }
});
