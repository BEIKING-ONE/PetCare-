const api = require('../../utils/api.js');

Page({
  data: {
    feedbackType: '',
    content: '',
    contact: '',
    images: [],
    canSubmit: false,
    submitting: false,
    showSuccess: false
  },

  onLoad() {
    this.checkLogin();
  },

  checkLogin: function() {
    const token = wx.getStorageSync('token');
    if (!token) {
      wx.showModal({
        title: '提示',
        content: '请先登录后再提交反馈',
        success: (res) => {
          if (res.confirm) {
            wx.switchTab({
              url: '/pages/profile/profile'
            });
          } else {
            wx.navigateBack();
          }
        }
      });
    }
  },

  selectType: function(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({ feedbackType: type });
    this.checkCanSubmit();
  },

  onContentInput: function(e) {
    const content = e.detail.value;
    this.setData({ content });
    this.checkCanSubmit();
  },

  onContactInput: function(e) {
    const contact = e.detail.value;
    this.setData({ contact });
    this.checkCanSubmit();
  },

  checkCanSubmit: function() {
    const { feedbackType, content, contact } = this.data;
    const canSubmit = feedbackType && content.length >= 10 && contact.length > 0;
    this.setData({ canSubmit });
  },

  chooseImage: function() {
    const that = this;
    wx.chooseMedia({
      count: 3 - that.data.images.length,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success(res) {
        const tempFiles = res.tempFiles.map(file => file.tempFilePath);
        that.setData({
          images: that.data.images.concat(tempFiles)
        });
      }
    });
  },

  deleteImage: function(e) {
    const index = e.currentTarget.dataset.index;
    const images = this.data.images.filter((_, i) => i !== index);
    this.setData({ images });
  },

  validateForm: function() {
    const { feedbackType, content, contact } = this.data;
    
    if (!feedbackType) {
      wx.showToast({
        title: '请选择反馈类型',
        icon: 'none'
      });
      return false;
    }
    
    if (content.length < 10) {
      wx.showToast({
        title: '问题描述至少10个字',
        icon: 'none'
      });
      return false;
    }
    
    if (!contact) {
      wx.showToast({
        title: '请填写联系方式',
        icon: 'none'
      });
      return false;
    }
    
    const phoneReg = /^1[3-9]\d{9}$/;
    const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!phoneReg.test(contact) && !emailReg.test(contact)) {
      wx.showToast({
        title: '请输入正确的手机号或邮箱',
        icon: 'none'
      });
      return false;
    }
    
    return true;
  },

  submitFeedback: function() {
    if (!this.validateForm()) {
      return;
    }
    
    if (this.data.submitting) {
      return;
    }
    
    this.setData({ submitting: true });
    
    const { feedbackType, content, contact, images } = this.data;
    
    const submitData = {
      type: feedbackType,
      content: content,
      contact: contact,
      images: images
    };
    
    api.post('/feedback', submitData).then(res => {
      this.setData({ 
        submitting: false,
        showSuccess: true
      });
    }).catch(err => {
      console.error('提交反馈失败:', err);
      this.setData({ submitting: false });
      
      this.setData({ showSuccess: true });
    });
  },

  closeSuccessModal: function() {
    this.setData({ showSuccess: false });
    wx.navigateBack();
  },

  onShareAppMessage() {
    return {
      title: '意见反馈',
      path: '/pages/feedback/feedback'
    };
  }
});
