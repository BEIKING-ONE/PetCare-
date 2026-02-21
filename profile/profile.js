const api = require('../../utils/api.js');

Page({
  data: {
    userInfo: {
      nickName: '宠物爱好者',
      avatarUrl: '\u{1F60A}'
    },
    emojiAvatars: [
      '\u{1F60A}', '\u{1F601}', '\u{1F604}', '\u{1F603}', '\u{1F642}', '\u{1F60D}', '\u{1F618}', '\u{1F60B}', '\u{1F60E}', '\u{1F634}',
      '\u{1F615}', '\u{1F62E}', '\u{1F632}', '\u{1F633}', '\u{1F622}', '\u{1F62D}', '\u{1F631}', '\u{1F616}', '\u{1F623}', '\u{1F61E}',
      '\u{1F624}', '\u{1F621}', '\u{1F608}', '\u{1F47F}', '\u{1F480}', '\u{1F4A9}', '\u{1F479}', '\u{1F47A}', '\u{1F47B}', '\u{1F47D}',
      '\u{1F47E}', '\u{1F916}', '\u{1F63A}', '\u{1F638}', '\u{1F639}', '\u{1F63B}', '\u{1F63C}', '\u{1F63D}', '\u{1F640}', '\u{1F63F}',
      '\u{1F63E}', '\u{1F648}', '\u{1F48B}', '\u{1F48C}', '\u{1F498}', '\u{1F49D}', '\u{1F496}', '\u{1F497}', '\u{1F493}', '\u{1F49E}',
      '\u{1F495}', '\u{1F49F}', '\u{1F494}', '\u{2764}', '\u{1F9E1}', '\u{1F49B}', '\u{1F49A}', '\u{1F499}', '\u{1F49C}', '\u{1F5A4}',
      '\u{1F90D}', '\u{1F90E}', '\u{1F4AF}', '\u{1F4A2}', '\u{1F4A5}', '\u{1F4AB}', '\u{1F4A6}', '\u{1F4A8}', '\u{1F573}', '\u{1F4A3}',
      '\u{1F4AC}', '\u{1F5EF}', '\u{1F4AD}', '\u{1F4A4}', '\u{1F44B}', '\u{1F91A}', '\u{1F590}', '\u{270B}', '\u{1F596}', '\u{1F44C}'
    ],
    showAvatarPicker: false,
    loading: false,
    couponCount: 0
  },

  onLoad: function() {
    this.checkLogin();
  },

  onShow: function() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({
        selected: 3
      });
    }
    this.checkLogin();
    this.loadCouponCount();
  },

  checkLogin: function() {
    const token = wx.getStorageSync('token');
    if (!token) {
      wx.reLaunch({
        url: '/pages/login/login'
      });
      return;
    }
    
    this.loadUserInfo();
  },

  loadCouponCount: function() {
    api.request({
      url: '/coupons',
      method: 'GET',
      silent: true
    }).then(res => {
      const coupons = res.data || [];
      if (coupons.length > 0) {
        const availableCoupons = coupons.filter(item => item.status === 'available');
        this.setData({ couponCount: availableCoupons.length });
      } else {
        this.loadLocalCouponCount();
      }
    }).catch(err => {
      console.error('获取优惠券数量失败:', err);
      this.loadLocalCouponCount();
    });
  },

  loadLocalCouponCount: function() {
    try {
      const myCoupons = wx.getStorageSync('myCoupons') || [];
      const availableCoupons = myCoupons.filter(item => item.status === 'available');
      this.setData({ couponCount: availableCoupons.length });
    } catch (e) {
      console.error('读取本地优惠券数量失败:', e);
      this.setData({ couponCount: 0 });
    }
  },

  loadUserInfo: function() {
    const storedUserInfo = wx.getStorageSync('userInfo');
    if (storedUserInfo && storedUserInfo.nickName) {
      console.log('从本地存储加载用户信息');
      
      if (!storedUserInfo.avatarUrl) {
        storedUserInfo.avatarUrl = '\u{1F60A}';
      }
      
      this.setData({
        userInfo: storedUserInfo
      });
      return;
    }
    
    this.setData({ loading: true });
    
    api.get('/user/info').then(res => {
      console.log('获取用户信息成功');
      const userInfo = res.data || {};
      
      if (!userInfo.nickName) {
        userInfo.nickName = '宠物爱好者';
      }
      
      if (!userInfo.avatarUrl) {
        userInfo.avatarUrl = '\u{1F60A}';
      }
      
      this.setData({
        userInfo: userInfo,
        loading: false
      });
      
      wx.setStorageSync('userInfo', userInfo);
    }).catch(err => {
      console.error('获取用户信息失败:', err);
      
      this.setData({ loading: false });
      
      const defaultUserInfo = {
        nickName: '宠物爱好者',
        avatarUrl: '\u{1F60A}'
      };
      
      this.setData({
        userInfo: defaultUserInfo
      });
      
      wx.setStorageSync('userInfo', defaultUserInfo);
      
      if (err.code !== 404) {
        wx.showToast({
          title: '获取用户信息失败',
          icon: 'none',
          duration: 2000
        });
      }
    });
  },

  isEmoji: function(str) {
    if (!str) return false;
    const emojiRegex = /[\u{1F300}-\u{1F9FF}]/u;
    return emojiRegex.test(str);
  },

  openAvatarPicker: function() {
    this.setData({
      showAvatarPicker: true
    });
  },

  closeAvatarPicker: function() {
    this.setData({
      showAvatarPicker: false
    });
  },

  selectEmojiAvatar: function(e) {
    const emoji = e.currentTarget.dataset.emoji;
    
    let userInfo = this.data.userInfo;
    userInfo.avatarUrl = emoji;
    
    this.setData({
      userInfo: userInfo,
      showAvatarPicker: false
    });
    
    wx.setStorageSync('userInfo', userInfo);
    
    wx.showToast({
      title: '头像已更新',
      icon: 'success',
      duration: 1500
    });
    
    api.put('/user/info', {
      avatar: emoji
    }).then(res => {
      console.log('头像已同步到服务器');
    }).catch(err => {
      console.error('同步头像到服务器失败:', err);
    });
  },

  changeNickName: function() {
    wx.showModal({
      title: '修改昵称',
      editable: true,
      placeholderText: '请输入新昵称',
      content: this.data.userInfo.nickName || '',
      success: (res) => {
        if (res.confirm && res.content && res.content.trim()) {
          const newNickname = res.content.trim();
          
          console.log('准备更新昵称:', newNickname);
          
          wx.showLoading({
            title: '更新中...'
          });
          
          api.put('/user/info', {
            nickname: newNickname
          }).then(res => {
            wx.hideLoading();
            console.log('更新昵称成功:', res);
            
            let userInfo = this.data.userInfo;
            userInfo.nickName = newNickname;
            
            this.setData({
              userInfo: userInfo
            });
            
            wx.setStorageSync('userInfo', userInfo);
            
            wx.showToast({
              title: '昵称已更新',
              icon: 'success'
            });
          }).catch(err => {
            wx.hideLoading();
            console.error('更新昵称失败:', err);
            
            let userInfo = this.data.userInfo;
            userInfo.nickName = newNickname;
            
            this.setData({
              userInfo: userInfo
            });
            
            wx.setStorageSync('userInfo', userInfo);
            
            wx.showToast({
              title: '昵称已更新（本地）',
              icon: 'success'
            });
          });
        }
      }
    });
  },

  goToSettings: function() {
    wx.navigateTo({
      url: '/pages/settings/settings'
    });
  },

  goToOrders: function(e) {
    var status = e.currentTarget.dataset.status;
    wx.navigateTo({
      url: '/pages/order/order?status=' + (status || 'all')
    });
  },

  goToCollection: function() {
    wx.navigateTo({
      url: '/pages/collection/collection'
    });
  },

  goToAddress: function() {
    wx.navigateTo({
      url: '/pages/address/address'
    });
  },

  goToCoupons: function() {
    wx.navigateTo({
      url: '/pages/coupons/coupons'
    });
  },

  goToPets: function() {
    wx.navigateTo({
      url: '/pages/pets/pets'
    });
  },

  goToService: function() {
    wx.navigateTo({
      url: '/pages/service/service'
    });
  },

  goToHealthCheck: function() {
    wx.navigateTo({
      url: '/pages/health/health'
    });
  },

  goToVaccine: function() {
    wx.navigateTo({
      url: '/pages/vaccine/vaccine'
    });
  },

  goToFuneral: function() {
    wx.navigateTo({
      url: '/pages/funeral/funeral'
    });
  },

  logout: function() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('token');
          wx.removeStorageSync('userInfo');
          wx.showToast({
            title: '已退出登录',
            icon: 'success'
          });
          setTimeout(() => {
            wx.reLaunch({
              url: '/pages/login/login'
            });
          }, 1500);
        }
      }
    });
  }
});
