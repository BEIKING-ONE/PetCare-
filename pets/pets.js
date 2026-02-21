const api = require('../../utils/api.js');

Page({
  data: {
    pets: []
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
    
    this.loadPets();
  },

  loadPets: function() {
    wx.showLoading({
      title: '加载中...'
    });
    api.get('/pets').then(res => {
      const pets = (res.data || []).map(pet => {
        return {
          ...pet,
          typeName: this.getPetTypeName(pet.type),
          gender: this.getGenderName(pet.gender),
          birthday: this.formatDate(pet.birthday)
        };
      });
      this.setData({
        pets: pets
      });
      wx.hideLoading();
    }).catch(err => {
      console.error('获取宠物列表失败:', err);
      wx.hideLoading();
      this.setData({
        pets: []
      });
    });
  },

  getPetTypeName: function(type) {
    const typeMap = {
      'dog': '狗',
      'cat': '猫',
      'bird': '鸟',
      'fish': '鱼',
      'rabbit': '兔子',
      'hamster': '仓鼠',
      'other': '其他',
      '狗': '狗',
      '猫': '猫',
      '鸟': '鸟',
      '鱼': '鱼',
      '兔子': '兔子',
      '仓鼠': '仓鼠',
      '其他': '其他'
    };
    return typeMap[type] || type || '未知';
  },

  getGenderName: function(gender) {
    const genderMap = {
      'male': '公',
      'female': '母',
      '公': '公',
      '母': '母'
    };
    return genderMap[gender] || gender || '未知';
  },

  formatDate: function(dateStr) {
    if (!dateStr) return '未设置';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}年${month}月${day}日`;
  },

  addPet: function() {
    wx.navigateTo({
      url: '/pages/pet-add/pet-add'
    });
  },

  editPet: function(e) {
    const petId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/pet-add/pet-add?id=${petId}`
    });
  },

  viewPetDetail: function(e) {
    const petId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/pet-detail/pet-detail?id=${petId}`
    });
  },

  deletePet: function(e) {
    const petId = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确定要删除这只宠物吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '处理中...'
          });
          api.del('/pets/' + petId).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '宠物已删除',
              icon: 'success'
            });
            this.loadPets();
          }).catch(err => {
            console.error('删除宠物失败:', err);
            wx.hideLoading();
          });
        }
      }
    });
  },

  onPullDownRefresh() {
    this.loadPets();
    wx.stopPullDownRefresh();
  },

  onShareAppMessage() {
    return {
      title: '我的宠物',
      path: '/pages/pets/pets'
    };
  }
});