const api = require('../../utils/api.js');

Page({
  data: {
    isEdit: false,
    petId: null,
    showEmojiPicker: false,
    isEmojiAvatar: false,
    pet: {
      name: '',
      type: '',
      breed: '',
      gender: '',
      birthday: '',
      weight: '',
      avatar: '',
      health_status: '',
      vaccine_record: ''
    },
    petTypes: ['狗', '猫', '鸟', '鱼', '兔子', '仓鼠', '其他'],
    petTypeIndex: 0,
    genders: ['公', '母'],
    genderIndex: 0,
    formattedBirthday: '',
    loading: false
  },

  onLoad(options) {
    this.checkLogin();
    
    if (options.id) {
      this.setData({ isEdit: true, petId: options.id });
      wx.setNavigationBarTitle({
        title: '编辑宠物'
      });
      this.loadPetDetail(options.id);
    } else {
      wx.setNavigationBarTitle({
        title: '添加宠物'
      });
    }
  },

  checkLogin: function() {
    const token = wx.getStorageSync('token');
    if (!token) {
      wx.reLaunch({
        url: '/pages/login/login'
      });
      return;
    }
  },

  showEmojiPicker: function() {
    this.setData({ showEmojiPicker: true });
  },

  hideEmojiPicker: function() {
    this.setData({ showEmojiPicker: false });
  },

  selectEmoji: function(e) {
    const emoji = e.currentTarget.dataset.emoji;
    this.setData({
      'pet.avatar': emoji,
      isEmojiAvatar: true,
      showEmojiPicker: false
    });
  },

  checkIsEmoji: function(avatar) {
    if (!avatar) return false;
    const emojiRegex = /[\u{1F300}-\u{1F9FF}]/u;
    return emojiRegex.test(avatar) || avatar.length <= 4;
  },

  formatDate: function(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}年${month}月${day}日`;
  },

  formatDateForSubmit: function(dateStr) {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        return dateStr;
      }
      return null;
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  },

  loadPetDetail: function(id) {
    wx.showLoading({ title: '加载中...' });
    
    api.get('/pets/' + id).then(res => {
      wx.hideLoading();
      const pet = res.data;
      
      const petTypeIndex = this.data.petTypes.indexOf(pet.type);
      const genderIndex = this.data.genders.indexOf(pet.gender);
      const isEmojiAvatar = this.checkIsEmoji(pet.avatar);
      const formattedBirthday = this.formatDate(pet.birthday);
      
      this.setData({
        pet: pet,
        petTypeIndex: petTypeIndex >= 0 ? petTypeIndex : 0,
        genderIndex: genderIndex >= 0 ? genderIndex : 0,
        isEmojiAvatar: isEmojiAvatar,
        formattedBirthday: formattedBirthday
      });
    }).catch(err => {
      wx.hideLoading();
      console.error('获取宠物详情失败:', err);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    });
  },

  chooseAvatar: function() {
    const that = this;
    
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath;
        const token = wx.getStorageSync('token');
        
        console.log('选择的图片路径:', tempFilePath);
        
        wx.showLoading({
          title: '上传中...'
        });
        
        wx.uploadFile({
          url: api.BASE_URL + '/upload',
          filePath: tempFilePath,
          name: 'file',
          header: {
            'Authorization': token ? 'Bearer ' + token : ''
          },
          success: (uploadRes) => {
            console.log('上传响应:', uploadRes.data);
            try {
              const data = JSON.parse(uploadRes.data);
              if (data.code === 200 || data.code === 0) {
                that.setData({
                  'pet.avatar': data.data.url,
                  isEmojiAvatar: false
                });
                wx.hideLoading();
                wx.showToast({
                  title: '上传成功',
                  icon: 'success'
                });
              } else {
                wx.hideLoading();
                wx.showToast({
                  title: data.message || '上传失败',
                  icon: 'none'
                });
              }
            } catch (e) {
              console.error('解析上传响应失败:', e);
              wx.hideLoading();
              wx.showToast({
                title: '上传失败',
                icon: 'none'
              });
            }
          },
          fail: (err) => {
            console.error('上传失败:', err);
            wx.hideLoading();
            wx.showToast({
              title: '上传失败',
              icon: 'none'
            });
          }
        });
      }
    });
  },

  onNameInput: function(e) {
    this.setData({
      'pet.name': e.detail.value
    });
  },

  onPetTypeChange: function(e) {
    this.setData({
      petTypeIndex: e.detail.value,
      'pet.type': this.data.petTypes[e.detail.value]
    });
  },

  onBreedInput: function(e) {
    this.setData({
      'pet.breed': e.detail.value
    });
  },

  onGenderChange: function(e) {
    this.setData({
      genderIndex: e.detail.value,
      'pet.gender': this.data.genders[e.detail.value]
    });
  },

  onBirthdayChange: function(e) {
    const formattedBirthday = this.formatDate(e.detail.value);
    this.setData({
      'pet.birthday': e.detail.value,
      formattedBirthday: formattedBirthday
    });
  },

  onWeightInput: function(e) {
    this.setData({
      'pet.weight': e.detail.value
    });
  },

  onHealthStatusInput: function(e) {
    this.setData({
      'pet.health_status': e.detail.value
    });
  },

  onVaccineRecordInput: function(e) {
    this.setData({
      'pet.vaccine_record': e.detail.value
    });
  },

  submitPet: function() {
    const that = this;
    const pet = that.data.pet;
    
    console.log('=== 提交宠物数据 ===');
    console.log('pet:', pet);
    
    if (!pet.name) {
      wx.showToast({
        title: '请输入宠物名称',
        icon: 'none'
      });
      return;
    }
    
    if (!pet.type) {
      wx.showToast({
        title: '请选择宠物类型',
        icon: 'none'
      });
      return;
    }
    
    that.setData({ loading: true });
    
    const submitData = {
      name: pet.name,
      type: pet.type,
      breed: pet.breed || '',
      gender: pet.gender || '',
      birthday: that.formatDateForSubmit(pet.birthday),
      weight: pet.weight || '',
      avatar: pet.avatar || '',
      health_status: pet.health_status || '',
      vaccine_record: pet.vaccine_record || ''
    };
    
    console.log('submitData:', submitData);
    
    const request = that.data.isEdit 
      ? api.put('/pets/' + that.data.petId, submitData)
      : api.post('/pets', submitData);
    
    request.then(res => {
      console.log(that.data.isEdit ? '编辑成功:' : '添加成功:', res);
      that.setData({ loading: false });
      
      wx.showToast({
        title: that.data.isEdit ? '修改成功' : '添加成功',
        icon: 'success'
      });
      
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }).catch(err => {
      that.setData({ loading: false });
      console.error(that.data.isEdit ? '编辑宠物失败:' : '添加宠物失败:', err);
      wx.showToast({
        title: err.message || '操作失败',
        icon: 'none'
      });
    });
  },

  onShareAppMessage() {
    return {
      title: '添加宠物',
      path: '/pages/pet-add/pet-add'
    };
  }
});
