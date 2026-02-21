const api = require('../../utils/api.js');

Page({
  data: {
    collections: []
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
    
    this.loadCollections();
  },

  loadCollections: function() {
    const collectedArticles = wx.getStorageSync('collectedArticles') || {};
    const newsCollections = Object.values(collectedArticles).filter(item => item.itemType === 'news');
    
    this.setData({
      collections: newsCollections
    });
  },

  viewNews: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/news-detail/news-detail?id=' + id
    });
  },

  cancelCollection: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确定要取消收藏吗？',
      success: (res) => {
        if (res.confirm) {
          const collectedArticles = wx.getStorageSync('collectedArticles') || {};
          delete collectedArticles[id];
          wx.setStorageSync('collectedArticles', collectedArticles);
          this.loadCollections();
          wx.showToast({
            title: '已取消收藏',
            icon: 'success'
          });
        }
      }
    });
  },

  goToMessage: function() {
    wx.switchTab({
      url: '/pages/message/message'
    });
  },

  onPullDownRefresh() {
    this.loadCollections();
    wx.stopPullDownRefresh();
  },

  onShareAppMessage() {
    return {
      title: '我的收藏',
      path: '/pages/collection/collection'
    };
  }
});
