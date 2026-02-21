const api = require('../../utils/api.js');

Page({
  data: {
    order: null,
    loading: false
  },

  onLoad(options) {
    if (options.id) {
      this.loadOrderDetail(options.id);
    }
  },

  loadOrderDetail: function(orderId) {
    wx.showLoading({
      title: '加载中...'
    });
    
    this.setData({ loading: true });
    
    api.get('/orders/' + orderId).then(res => {
      const order = res.data;
      console.log('订单详情数据:', order);
      console.log('收货地址数据:', order.address);
      
      const categoryIcons = {
        '狗粮': '🍖', '猫粮': '🍗', '零食': '🥩', '玩具': '🎾',
        '洗护': '🧴', '用品': '🛏️', '猫砂': '🧹', '保健品': '💊'
      };
      
      if (order.items && order.items.length > 0) {
        order.items.forEach(item => {
          item.categoryIcon = categoryIcons[item.category] || '📦';
        });
      }
      
      if (order.address && typeof order.address === 'string') {
        try {
          order.address = JSON.parse(order.address);
          console.log('解析后的收货地址:', order.address);
        } catch (e) {
          console.error('解析收货地址失败:', e);
        }
      }
      
      this.setData({
        order: order,
        loading: false
      });
      
      wx.hideLoading();
    }).catch(err => {
      console.error('获取订单详情失败');
      wx.hideLoading();
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
      this.setData({
        loading: false
      });
    });
  },

  getStatusText: function(status) {
    const statusMap = {
      'pending': '待付款',
      'paid': '已支付',
      'shipping': '待发货',
      'delivered': '待收货',
      'completed': '已完成',
      'canceled': '已取消'
    };
    return statusMap[status] || status;
  },

  getStatusIcon: function(status) {
    const iconMap = {
      'pending': '⏰',
      'paid': '💰',
      'shipping': '📦',
      'delivered': '🚚',
      'completed': '✅',
      'canceled': '❌'
    };
    return iconMap[status] || '📋';
  },

  cancelOrder: function() {
    wx.showModal({
      title: '提示',
      content: '确定要取消订单吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '处理中...'
          });
          api.post('/orders/cancel', {
            orderId: this.data.order.id
          }).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '订单已取消',
              icon: 'success'
            });
            setTimeout(() => {
              wx.navigateBack();
            }, 1500);
          }).catch(err => {
            console.error('取消订单失败');
            wx.hideLoading();
          });
        }
      }
    });
  },

  payOrder: function() {
    wx.showModal({
      title: '提示',
      content: '确定要支付订单吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '处理中...'
          });
          api.post('/orders/pay', {
            orderId: this.data.order.id
          }).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '支付成功',
              icon: 'success'
            });
            setTimeout(() => {
              this.loadOrderDetail(this.data.order.id);
            }, 1500);
          }).catch(err => {
            console.error('支付订单失败');
            wx.hideLoading();
          });
        }
      }
    });
  },

  confirmOrder: function() {
    wx.showModal({
      title: '提示',
      content: '确定要确认收货吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '处理中...'
          });
          api.post('/orders/confirm', {
            orderId: this.data.order.id
          }).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '已确认收货',
              icon: 'success'
            });
            setTimeout(() => {
              this.loadOrderDetail(this.data.order.id);
            }, 1500);
          }).catch(err => {
            console.error('确认收货失败');
            wx.hideLoading();
          });
        }
      }
    });
  },

  contactService: function() {
    wx.showModal({
      title: '联系客服',
      content: '客服电话：400-888-8888\n工作时间：9:00-18:00',
      showCancel: false
    });
  },

  onPullDownRefresh() {
    if (this.data.order) {
      this.loadOrderDetail(this.data.order.id);
    }
    wx.stopPullDownRefresh();
  },

  onShareAppMessage() {
    if (this.data.order) {
      return {
        title: '订单详情',
        path: '/pages/order-detail/order-detail?id=' + this.data.order.id
      };
    }
  }
});