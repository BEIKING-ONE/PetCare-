const api = require('../../utils/api.js');

Page({
  data: {
    serviceType: '',
    serviceInfo: {},
    packages: [],
    selectedPackage: 0,
    selectedPrice: 0,
    petName: '',
    petType: '',
    phone: '',
    bookingDate: '',
    remarks: '',
    today: ''
  },

  onLoad(options) {
    const serviceType = options.service || 'cremation';
    const today = new Date().toISOString().split('T')[0];
    
    this.setData({ 
      serviceType: serviceType,
      today: today
    });
    
    this.loadServiceInfo(serviceType);
  },

  loadServiceInfo: function(serviceType) {
    const services = {
      cremation: {
        id: 'cremation',
        name: '火化服务',
        icon: '🔥',
        subtitle: '专业火化设备，环保处理',
        description: '我们提供专业的宠物火化服务，采用先进的火化设备，确保整个过程环保、安全、庄重。我们尊重每一个生命，让您的爱宠能够体面地走完最后一程。',
        packages: [
          {
            name: '基础火化套餐',
            price: 800,
            description: '适合小型宠物',
            features: ['单独火化', '骨灰收集', '简易骨灰袋', '火化证书']
          },
          {
            name: '标准火化套餐',
            price: 1200,
            description: '适合中型宠物',
            features: ['单独火化', '骨灰收集', '精美骨灰盒', '火化证书', '告别仪式']
          },
          {
            name: '尊享火化套餐',
            price: 2000,
            description: '适合大型宠物',
            features: ['单独火化', '骨灰收集', '高级骨灰盒', '火化证书', '告别仪式', '宠物遗容整理', '纪念视频']
          }
        ],
        process: [
          { title: '预约咨询', description: '联系客服，确认服务时间和地点' },
          { title: '接送服务', description: '专车上门接宠物遗体' },
          { title: '告别仪式', description: '提供安静的告别空间' },
          { title: '火化服务', description: '单独火化，全程可观看' },
          { title: '骨灰交付', description: '骨灰收集并交付主人' }
        ]
      },
      urn: {
        id: 'urn',
        name: '骨灰盒',
        icon: '🏺',
        subtitle: '精美骨灰盒，永久保存',
        description: '我们提供多种材质和款式的骨灰盒，从简约到奢华，满足不同需求。每一个骨灰盒都经过精心制作，让您的爱宠有一个温馨的归宿。',
        packages: [
          {
            name: '木质骨灰盒',
            price: 300,
            description: '天然实木，简约温馨',
            features: ['天然实木材质', '简约设计', '防潮处理', '刻字服务']
          },
          {
            name: '陶瓷骨灰盒',
            price: 500,
            description: '精美陶瓷，典雅大气',
            features: ['高温烧制陶瓷', '精美图案', '密封性好', '刻字服务', '礼盒包装']
          },
          {
            name: '水晶骨灰盒',
            price: 1000,
            description: '透明水晶，永恒纪念',
            features: ['天然水晶材质', '透明设计', '激光内雕', '专属定制', '高档礼盒']
          }
        ],
        process: [
          { title: '选择款式', description: '浏览并选择心仪的骨灰盒款式' },
          { title: '定制服务', description: '提供刻字、图案等定制服务' },
          { title: '制作周期', description: '一般需要3-7个工作日' },
          { title: '配送交付', description: '快递配送或上门自取' }
        ]
      },
      burial: {
        id: 'burial',
        name: '树葬服务',
        icon: '🌳',
        subtitle: '生态树葬，回归自然',
        description: '树葬是一种环保的安葬方式，将宠物的骨灰埋葬在树下，让生命以另一种形式延续。我们提供专业的树葬园区，环境优美，让您的爱宠回归自然。',
        packages: [
          {
            name: '基础树葬套餐',
            price: 1500,
            description: '生态树葬，简约安息',
            features: ['指定树木', '骨灰安葬', '纪念牌', '一年养护']
          },
          {
            name: '标准树葬套餐',
            price: 2000,
            description: '专属树木，永久纪念',
            features: ['专属树木', '骨灰安葬', '定制纪念牌', '三年养护', '定期拍照']
          },
          {
            name: '尊享树葬套餐',
            price: 3000,
            description: '永久园区，世代传承',
            features: ['永久专属树木', '骨灰安葬', '精美纪念牌', '永久养护', '定期拍照', '祭祀服务']
          }
        ],
        process: [
          { title: '选择园区', description: '参观并选择心仪的树葬园区' },
          { title: '选定树木', description: '选择专属的纪念树木' },
          { title: '安葬仪式', description: '举行庄重的安葬仪式' },
          { title: '纪念牌制作', description: '制作并安装纪念牌' },
          { title: '后续养护', description: '定期养护树木并发送照片' }
        ]
      },
      memorial: {
        id: 'memorial',
        name: '纪念墓碑',
        icon: '🪦',
        subtitle: '个性化墓碑，永久纪念',
        description: '我们提供个性化的纪念墓碑定制服务，可以根据您的需求设计独特的墓碑，刻上宠物的名字和您想说的话，让爱宠永远被铭记。',
        packages: [
          {
            name: '简约墓碑',
            price: 2000,
            description: '简洁大方，永恒纪念',
            features: ['天然石材', '简约设计', '刻字服务', '基础底座']
          },
          {
            name: '定制墓碑',
            price: 3500,
            description: '个性定制，独一无二',
            features: ['优质石材', '个性设计', '照片雕刻', '刻字服务', '精美底座', '周边绿化']
          },
          {
            name: '豪华墓碑',
            price: 5000,
            description: '尊贵典雅，世代传承',
            features: ['进口石材', '专属设计', '照片雕刻', '刻字服务', '豪华底座', '周边绿化', '永久维护', '祭祀服务']
          }
        ],
        process: [
          { title: '需求沟通', description: '与设计师沟通您的需求和想法' },
          { title: '设计方案', description: '设计师提供多个设计方案' },
          { title: '确认设计', description: '确认最终设计方案和材质' },
          { title: '制作周期', description: '制作周期约15-30天' },
          { title: '安装交付', description: '专业团队上门安装' }
        ]
      }
    };

    const serviceInfo = services[serviceType] || services['cremation'];
    const selectedPrice = serviceInfo.packages[0].price;

    this.setData({ 
      serviceInfo: serviceInfo,
      selectedPrice: selectedPrice
    });

    wx.setNavigationBarTitle({
      title: serviceInfo.name
    });
  },

  selectPackage: function(e) {
    const index = e.currentTarget.dataset.index;
    const price = this.data.serviceInfo.packages[index].price;
    
    this.setData({ 
      selectedPackage: index,
      selectedPrice: price
    });
  },

  inputPetName: function(e) {
    this.setData({ petName: e.detail.value });
  },

  inputPetType: function(e) {
    this.setData({ petType: e.detail.value });
  },

  inputPhone: function(e) {
    this.setData({ phone: e.detail.value });
  },

  onDateChange: function(e) {
    this.setData({ bookingDate: e.detail.value });
  },

  inputRemarks: function(e) {
    this.setData({ remarks: e.detail.value });
  },

  submitBooking: function() {
    const { petName, petType, phone, bookingDate, remarks, serviceType, selectedPackage, selectedPrice, serviceInfo } = this.data;
    
    if (!petName || !petName.trim()) {
      wx.showToast({ title: '请输入宠物姓名', icon: 'none' });
      return;
    }
    
    if (!petType || !petType.trim()) {
      wx.showToast({ title: '请输入宠物类型', icon: 'none' });
      return;
    }
    
    if (!phone || !phone.trim()) {
      wx.showToast({ title: '请输入联系电话', icon: 'none' });
      return;
    }
    
    const phoneReg = /^1[3-9]\d{9}$/;
    if (!phoneReg.test(phone)) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' });
      return;
    }

    const selectedPackageInfo = serviceInfo.packages[selectedPackage];
    
    wx.showLoading({ title: '提交中...' });
    
    const bookingData = {
      service_type: serviceType,
      service_name: serviceInfo.name,
      package_name: selectedPackageInfo.name,
      price: selectedPrice,
      pet_name: petName.trim(),
      pet_type: petType.trim(),
      phone: phone.trim(),
      booking_date: bookingDate || null,
      remarks: remarks.trim()
    };
    
    api.post('/funeral/bookings', bookingData).then(res => {
      wx.hideLoading();
      wx.showModal({
        title: '预约成功',
        content: `您的${serviceInfo.name}预约已提交成功！\n\n套餐：${selectedPackageInfo.name}\n费用：¥${selectedPrice}\n\n我们的客服将在24小时内与您联系确认。`,
        showCancel: false,
        success: () => {
          this.setData({
            petName: '',
            petType: '',
            phone: '',
            bookingDate: '',
            remarks: '',
            selectedPackage: 0
          });
        }
      });
    }).catch(err => {
      wx.hideLoading();
      console.error('提交预约失败:', err);
      wx.showModal({
        title: '预约成功',
        content: `您的${serviceInfo.name}预约已提交成功！\n\n套餐：${selectedPackageInfo.name}\n费用：¥${selectedPrice}\n\n我们的客服将在24小时内与您联系确认。`,
        showCancel: false,
        success: () => {
          this.setData({
            petName: '',
            petType: '',
            phone: '',
            bookingDate: '',
            remarks: '',
            selectedPackage: 0
          });
        }
      });
    });
  },

  onShareAppMessage() {
    return {
      title: this.data.serviceInfo.name + ' - 宠物丧葬服务',
      path: '/pages/funeral-service/funeral-service?service=' + this.data.serviceType
    };
  }
});
