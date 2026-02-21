const api = require('../../utils/api.js');

Page({
  data: {
    cartItems: [],
    loading: false,
    allSelected: false,
    totalPrice: '0.00',
    selectedCount: 0
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
    
    this.loadCart();
  },

  loadCart: function() {
    wx.showLoading({
      title: '加载中...'
    });
    
    this.setData({ loading: true });
    
    api.get('/cart').then(res => {
      const cartItems = res.data || [];
      
      // 为每个商品设置默认的 selected 值
      const processedItems = cartItems.map(item => ({
        ...item,
        selected: item.selected !== undefined ? item.selected : false
      }));
      
      this.setData({
        cartItems: processedItems,
        loading: false
      });
      
      this.calculateTotal();
      wx.hideLoading();
    }).catch(err => {
      console.error('获取购物车失败:', err);
      wx.hideLoading();
      this.setData({
        cartItems: [],
        loading: false
      });
    });
  },

  toggleSelect: function(e) {
    const id = e.currentTarget.dataset.id;
    const cartItems = this.data.cartItems;
    const item = cartItems.find(item => item.id == id);
    
    if (item) {
      const newSelected = !item.selected;
      this.updateCartItem(id, { selected: newSelected });
      item.selected = newSelected;
      this.setData({ cartItems });
      this.calculateTotal();
    }
  },

  selectAll: function() {
    const allSelected = !this.data.allSelected;
    const cartItems = this.data.cartItems;
    
    cartItems.forEach(item => {
      item.selected = allSelected;
      this.updateCartItem(item.id, { selected: allSelected });
    });
    
    this.setData({
      cartItems,
      allSelected
    });
    
    this.calculateTotal();
  },

  increaseQty: function(e) {
    const id = e.currentTarget.dataset.id;
    const cartItems = this.data.cartItems;
    const item = cartItems.find(item => item.id == id);
    
    if (item) {
      const newQuantity = (item.quantity || 1) + 1;
      item.quantity = newQuantity;
      this.setData({ cartItems });
      this.updateCartItem(item.id, { quantity: newQuantity });
      this.calculateTotal();
    }
  },

  decreaseQty: function(e) {
    const id = e.currentTarget.dataset.id;
    const cartItems = this.data.cartItems;
    const item = cartItems.find(item => item.id == id);
    
    if (item && item.quantity > 1) {
      const newQuantity = item.quantity - 1;
      item.quantity = newQuantity;
      this.setData({ cartItems });
      this.updateCartItem(item.id, { quantity: newQuantity });
      this.calculateTotal();
    }
  },

  updateCartItem: function(cartId, data) {
    api.put('/cart/' + cartId, data).then(() => {
    }).catch(err => {
      console.error('更新购物车失败:', err);
      wx.showToast({
        title: '更新失败',
        icon: 'none'
      });
    });
  },

  calculateTotal: function() {
    const cartItems = this.data.cartItems;
    let totalPrice = 0;
    let selectedCount = 0;
    
    cartItems.forEach(item => {
      if (item.selected) {
        totalPrice += parseFloat(item.price) * (item.quantity || 1);
        selectedCount++;
      }
    });
    
    const allSelected = cartItems.length > 0 && selectedCount === cartItems.length;
    
    this.setData({
      totalPrice: totalPrice.toFixed(2),
      selectedCount,
      allSelected
    });
  },

  deleteItem: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确定要删除这个商品吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '处理中...'
          });
          api.del('/cart/' + id).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '已删除',
              icon: 'success'
            });
            this.loadCart();
          }).catch(err => {
            console.error('删除购物车项失败:', err);
            wx.hideLoading();
            wx.showToast({
              title: '删除失败',
              icon: 'none'
            });
          });
        }
      }
    });
  },

  clearCart: function() {
    wx.showModal({
      title: '提示',
      content: '确定要清空购物车吗？',
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '处理中...'
          });
          api.post('/cart/clear').then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '已清空购物车',
              icon: 'success'
            });
            this.loadCart();
          }).catch(err => {
            console.error('清空购物车失败:', err);
            wx.hideLoading();
            wx.showToast({
              title: '清空失败',
              icon: 'none'
            });
          });
        }
      }
    });
  },

  deleteSelected: function() {
    const selectedItems = this.data.cartItems.filter(item => item.selected);
    
    if (selectedItems.length === 0) {
      return;
    }
    
    wx.showModal({
      title: '提示',
      content: `确定要删除选中的 ${selectedItems.length} 个商品吗？`,
      success: (res) => {
        if (res.confirm) {
          wx.showLoading({
            title: '处理中...'
          });
          
          const deletePromises = selectedItems.map(item => api.del('/cart/' + item.id));
          
          Promise.all(deletePromises).then(() => {
            wx.hideLoading();
            wx.showToast({
              title: '已删除',
              icon: 'success'
            });
            this.loadCart();
          }).catch(err => {
            console.error('批量删除购物车项失败:', err);
            wx.hideLoading();
            wx.showToast({
              title: '删除失败',
              icon: 'none'
            });
          });
        }
      }
    });
  },

  checkout: function() {
    const selectedItems = this.data.cartItems.filter(item => item.selected);
    
    if (selectedItems.length === 0) {
      wx.showToast({
        title: '请选择要结算的商品',
        icon: 'none'
      });
      return;
    }
    
    // 将选中的商品存储到本地存储，确保订单创建页面能够获取到
    wx.setStorageSync('selectedCartItems', selectedItems);
    
    wx.navigateTo({
      url: '/pages/order-create/order-create'
    });
  },

  goToShop: function() {
    wx.switchTab({
      url: '/pages/shop/shop'
    });
  },

  onPullDownRefresh() {
    this.loadCart();
    wx.stopPullDownRefresh();
  },

  onShareAppMessage() {
    return {
      title: '我的购物车',
      path: '/pages/cart/cart'
    };
  }
});
