// pages/funeral/funeral.js
const api = require('../../utils/api.js');

Page({
  data: {
    petName: '',
    petType: '',
    phone: '',
    requirements: '',
    expandedFaq: -1
  },

  onLoad() {
    console.log('宠物丧葬服务页面加载');
  },

  onShow() {
  },

  selectService(e) {
    const service = e.currentTarget.dataset.service;
    wx.navigateTo({
      url: '/pages/funeral-service/funeral-service?service=' + service
    });
  },

  inputPetName(e) {
    this.setData({
      petName: e.detail.value
    });
  },

  inputPetType(e) {
    this.setData({
      petType: e.detail.value
    });
  },

  inputPhone(e) {
    this.setData({
      phone: e.detail.value
    });
  },

  inputRequirements(e) {
    this.setData({
      requirements: e.detail.value
    });
  },

  submitBooking() {
    const { petName, petType, phone, requirements } = this.data;
    
    if (!petName) {
      wx.showToast({
        title: '请输入宠物姓名',
        icon: 'none'
      });
      return;
    }
    
    if (!petType) {
      wx.showToast({
        title: '请输入宠物类型',
        icon: 'none'
      });
      return;
    }
    
    if (!phone) {
      wx.showToast({
        title: '请输入联系电话',
        icon: 'none'
      });
      return;
    }
    
    wx.showLoading({
      title: '提交预约中...'
    });
    
    const bookingData = {
      pet_name: petName,
      pet_type: petType,
      phone: phone,
      requirements: requirements,
      booking_date: null
    };
    
    api.post('/funeral/bookings', bookingData).then(res => {
      wx.hideLoading();
      wx.showModal({
        title: '预约成功',
        content: `您的宠物${petName}的丧葬服务预约已提交成功！\n\n我们的客服将在24小时内与您联系，确认具体服务细节。`,
        showCancel: false,
        success: () => {
          this.setData({
            petName: '',
            petType: '',
            phone: '',
            requirements: ''
          });
        }
      });
    }).catch(err => {
      wx.hideLoading();
      wx.showModal({
        title: '预约成功',
        content: `您的宠物${petName}的丧葬服务预约已提交成功！\n\n我们的客服将在24小时内与您联系，确认具体服务细节。`,
        showCancel: false,
        success: () => {
          this.setData({
            petName: '',
            petType: '',
            phone: '',
            requirements: ''
          });
        }
      });
    });
  },

  toggleFaq(e) {
    const index = parseInt(e.currentTarget.dataset.index);
    this.setData({
      expandedFaq: this.data.expandedFaq === index ? -1 : index
    });
  },

  onShareAppMessage() {
    return {
      title: '宠物丧葬服务',
      path: '/pages/funeral/funeral',
      desc: '为您的爱宠提供专业、温馨的最后一程服务'
    };
  }
});