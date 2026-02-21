const api = require('../../utils/api.js');

Page({
  data: {
    activities: [],
    filteredActivities: [],
    activeCategory: 'all',
    loading: false,
    hasMore: true,
    page: 1,
    pageSize: 10
  },

  onLoad: function() {
    this.loadActivities();
  },

  onShow: function() {
    this.loadActivities();
  },

  loadActivities: function() {
    const that = this;
    that.setData({ loading: true });
    
    // emoji映射关系
    const emojiMap = {
      limited: '🔥',
      member: '💎',
      festival: '🎉',
      newuser: '🎈'
    };
    
    const mockActivities = [
      {
        id: 1,
        title: '限时优惠活动',
        description: '精选商品限时优惠，低至5折起，数量有限，先到先得',
        type: 'limited',
        typeText: '限时',
        emoji: emojiMap.limited,
        image: 'https://images.unsplash.com/photo-1607082345960-f5071b5f1f2?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '2024-12-01 至 2024-12-31',
        status: 'ongoing',
        statusText: '进行中',
        price: '满199减50',
        participants: 1234
      },
      {
        id: 2,
        title: '会员专享福利',
        description: '会员专享折扣，享受专属优惠，每月更新，福利不断',
        type: 'member',
        typeText: '会员',
        emoji: emojiMap.member,
        image: 'https://images.unsplash.com/photo-1579168765467-3b235f938439?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '2024-12-01 至 2024-12-31',
        status: 'ongoing',
        statusText: '进行中',
        price: '8.8折',
        participants: 5678
      },
      {
        id: 3,
        title: '圣诞节特惠',
        description: '圣诞狂欢，全场满299减100，限时限量',
        type: 'festival',
        typeText: '节日',
        emoji: emojiMap.festival,
        image: 'https://images.unsplash.com/photo-1583337130417-3346a1be7dee?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '2024-12-20 至 2024-12-25',
        status: 'upcoming',
        statusText: '即将开始',
        price: '满299减100',
        participants: 0
      },
      {
        id: 4,
        title: '新人专属礼包',
        description: '新注册用户专享，首单立减30元，再送优惠券',
        type: 'newuser',
        typeText: '新人',
        emoji: emojiMap.newuser,
        image: 'https://images.unsplash.com/photo-1513360371669-4adf3dd7dff8?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '长期有效',
        status: 'ongoing',
        statusText: '进行中',
        price: '首单减30元',
        participants: 8901
      },
      {
        id: 5,
        title: '春节大促',
        description: '春节特惠，全场满399减150，限时限量',
        type: 'festival',
        typeText: '节日',
        emoji: emojiMap.festival,
        image: 'https://images.unsplash.com/photo-1583337130417-3346a1be7dee?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '2025-01-01 至 2025-01-31',
        status: 'upcoming',
        statusText: '即将开始',
        price: '满399减150',
        participants: 0
      },
      {
        id: 6,
        title: '限时秒杀',
        description: '每日限时秒杀，超低价格，数量有限',
        type: 'limited',
        typeText: '限时',
        emoji: emojiMap.limited,
        image: 'https://images.unsplash.com/photo-1607082345960-f5071b5f1f2?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '每日12:00-14:00',
        status: 'ongoing',
        statusText: '进行中',
        price: '低至3折',
        participants: 2345
      },
      {
        id: 7,
        title: '生日月特惠',
        description: '生日月专属福利，全场满199减50，限时限量',
        type: 'limited',
        typeText: '限时',
        emoji: emojiMap.limited,
        image: 'https://images.unsplash.com/photo-1607082345960-f5071b5f1f2?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '2024-12-01 至 2024-12-31',
        status: 'ongoing',
        statusText: '进行中',
        price: '满199减50',
        participants: 3456
      },
      {
        id: 8,
        title: 'VIP专享折扣',
        description: 'VIP会员专享折扣，享受更低价格，更多特权',
        type: 'member',
        typeText: '会员',
        emoji: emojiMap.member,
        image: 'https://images.unsplash.com/photo-1579168765467-3b235f938439?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '长期有效',
        status: 'ongoing',
        statusText: '进行中',
        price: '7.5折',
        participants: 2345
      },
      {
        id: 9,
        title: '元旦特惠',
        description: '元旦狂欢，全场满299减120，限时限量',
        type: 'festival',
        typeText: '节日',
        emoji: emojiMap.festival,
        image: 'https://images.unsplash.com/photo-1583337130417-3346a1be7dee?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '2025-01-01 至 2025-01-07',
        status: 'upcoming',
        statusText: '即将开始',
        price: '满299减120',
        participants: 0
      },
      {
        id: 10,
        title: '周末大促',
        description: '周末特惠，全场满399减200，限时限量',
        type: 'limited',
        typeText: '限时',
        emoji: emojiMap.limited,
        image: 'https://images.unsplash.com/photo-1607082345960-f5071b5f1f2?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '每周六周日',
        status: 'ongoing',
        statusText: '进行中',
        price: '满399减200',
        participants: 5678
      },
      {
        id: 11,
        title: '情人节特惠',
        description: '情人节专属优惠，全场满299减150，限时限量',
        type: 'festival',
        typeText: '节日',
        emoji: emojiMap.festival,
        image: 'https://images.unsplash.com/photo-1583337130417-3346a1be7dee?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '2025-02-14 至 2025-02-14',
        status: 'upcoming',
        statusText: '即将开始',
        price: '满299减150',
        participants: 0
      },
      {
        id: 12,
        title: '母亲节特惠',
        description: '母亲节感恩回馈，全场满199减80，限时限量',
        type: 'festival',
        typeText: '节日',
        emoji: emojiMap.festival,
        image: 'https://images.unsplash.com/photo-1583337130417-3346a1be7dee?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
        time: '2025-05-10 至 2025-05-10',
        status: 'upcoming',
        statusText: '即将开始',
        price: '满199减80',
        participants: 0
      }
    ];
    
    that.setData({
      activities: mockActivities
    });
    
    that.filterActivities();
  },

  filterActivities: function() {
    const that = this;
    const activeCategory = that.data.activeCategory;
    let filtered = that.data.activities;
    
    if (activeCategory !== 'all') {
      filtered = that.data.activities.filter(item => item.type === activeCategory);
    }
    
    that.setData({
      filteredActivities: filtered,
      loading: false
    });
  },

  switchCategory: function(e) {
    const category = e.currentTarget.dataset.cat;
    this.setData({
      activeCategory: category
    }, () => {
      this.filterActivities();
    });
  },

  viewActivityDetail: function(e) {
    const id = e.currentTarget.dataset.id;
    const activity = this.data.activities.find(item => item.id === id);
    
    if (activity) {
      wx.showModal({
        title: activity.title,
        content: `活动时间：${activity.time}\n活动描述：${activity.description}\n活动价格：${activity.price}\n参与人数：${activity.participants}人`,
        showCancel: false
      });
    }
  },

  loadMore: function() {
    const that = this;
    
    if (that.data.loading) {
      return;
    }
    
    wx.showLoading({
      title: '加载中...'
    });
    
    setTimeout(() => {
      // emoji映射关系
      const emojiMap = {
        limited: '🔥',
        member: '💎',
        festival: '🎉',
        newuser: '🎈'
      };
      
      const newActivities = [
        {
          id: 13,
          title: '儿童节特惠',
          description: '儿童节专属福利，全场满399减180，限时限量',
          type: 'festival',
          typeText: '节日',
          emoji: emojiMap.festival,
          image: 'https://images.unsplash.com/photo-1583337130417-3346a1be7dee?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
          time: '2025-06-01 至 2025-06-01',
          status: 'upcoming',
          statusText: '即将开始',
          price: '满399减180',
          participants: 0
        },
        {
          id: 14,
          title: '父亲节特惠',
          description: '父亲节感恩回馈，全场满299减100，限时限量',
          type: 'festival',
          typeText: '节日',
          emoji: emojiMap.festival,
          image: 'https://images.unsplash.com/photo-1583337130417-3346a1be7dee?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
          time: '2025-06-15 至 2025-06-15',
          status: 'upcoming',
          statusText: '即将开始',
          price: '满299减100',
          participants: 0
        }
      ];
      
      const updatedActivities = that.data.activities.concat(newActivities);
      
      that.setData({
        activities: updatedActivities,
        hasMore: false,
        loading: false
      });
      
      that.filterActivities();
      
      wx.hideLoading();
      wx.showToast({
        title: '加载成功',
        icon: 'success'
      });
    }, 1000);
  },

  onPullDownRefresh: function() {
    this.loadActivities();
    wx.stopPullDownRefresh();
  },

  onShareAppMessage: function() {
    return {
      title: '活动专区',
      path: '/pages/activity/activity'
    };
  }
});