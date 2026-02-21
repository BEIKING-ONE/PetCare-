const api = require('../../utils/api.js');

Page({
  data: {
    product: null,
    loading: true
  },

  onLoad(options) {
    if (options.id) {
      this.loadProductDetail(options.id);
    }
  },

  loadProductDetail(productId) {
    wx.showLoading({
      title: '加载中...'
    });
    
    api.get('/products/' + productId).then(res => {
      const product = res.data;
      const price = parseFloat(product.price) || 0;
      const originalPrice = parseFloat(product.original_price) || price;
      product.price = price.toFixed(2);
      product.original_price = originalPrice.toFixed(2);
      
      const categoryIcons = {
        '狗粮': '🍖', '猫粮': '🍗', '零食': '🥩', '玩具': '🎾',
        '洗护': '🧴', '用品': '🛏️', '猫砂': '🧹', '保健品': '💊'
      };
      product.categoryIcon = categoryIcons[product.category] || '📦';
      product.sales = product.sales || 0;
      product.stock = product.stock || 0;
      product.is_hot = product.is_hot || false;
      
      this.setData({
        product: product,
        loading: false
      });
      wx.hideLoading();
    }).catch(err => {
      console.error('获取商品详情失败:', err);
      wx.hideLoading();
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    });
  },

  addToCart() {
    if (!this.data.product) {
      return;
    }
    
    const token = wx.getStorageSync('token');
    if (!token) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      return;
    }
    
    api.post('/cart', {
      product_id: this.data.product.id,
      quantity: 1
    }).then(res => {
      wx.showToast({
        title: '已加入购物车',
        icon: 'success'
      });
    }).catch(err => {
      console.error('加入购物车失败:', err);
    });
  },

  buyNow() {
    if (!this.data.product) {
      return;
    }
    
    const token = wx.getStorageSync('token');
    if (!token) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      return;
    }
    
    wx.showToast({
      title: '立即购买功能开发中',
      icon: 'none'
    });
  },

  onShareAppMessage() {
    if (this.data.product) {
      return {
        title: this.data.product.name,
        path: '/pages/product-detail/product-detail?id=' + this.data.product.id
      };
    }
  }
});
