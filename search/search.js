const api = require('../../utils/api.js');

Page({
  data: {
    keyword: '',
    products: [],
    notes: [],
    loading: false,
    hasMore: false,
    page: 1,
    productLimit: 20,
    noteLimit: 20,
    suggestions: [],
    showSuggestions: false,
    history: [],
    debounceTimer: null
  },

  onLoad(options) {
    if (options.keyword) {
      this.setData({ keyword: options.keyword });
      this.onSearch();
    }
    this.loadSearchHistory();
  },

  onShow() {
    this.loadSearchHistory();
  },

  onInput: function(e) {
    const keyword = e.detail.value;
    this.setData({ keyword });
    
    if (this.data.debounceTimer) {
      clearTimeout(this.data.debounceTimer);
    }
    
    if (keyword.trim()) {
      const timer = setTimeout(() => {
        this.loadSuggestions(keyword);
      }, 300);
      this.setData({ debounceTimer: timer, showSuggestions: true });
    } else {
      this.setData({ showSuggestions: false, suggestions: [] });
    }
  },

  clearInput: function() {
    this.setData({
      keyword: '',
      products: [],
      notes: [],
      suggestions: [],
      showSuggestions: false
    });
  },

  loadSuggestions: function(keyword) {
    api.get('/search/suggest', { keyword: keyword, limit: 10 }).then(res => {
      this.setData({
        suggestions: res.data || []
      });
    }).catch(err => {
      console.error('获取搜索建议失败:', err);
    });
  },

  selectSuggestion: function(e) {
    const text = e.currentTarget.dataset.text;
    this.setData({
      keyword: text,
      showSuggestions: false,
      suggestions: []
    });
    this.onSearch();
  },

  hideSuggestions: function() {
    setTimeout(() => {
      this.setData({ showSuggestions: false });
    }, 200);
  },

  loadSearchHistory: function() {
    const token = wx.getStorageSync('token');
    if (!token) {
      this.setData({ history: [] });
      return;
    }
    
    api.get('/search/history', { limit: 10 }).then(res => {
      this.setData({
        history: res.data || []
      });
    }).catch(err => {
      console.error('获取搜索历史失败:', err);
    });
  },

  clearHistory: function() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空搜索历史吗？',
      success: (res) => {
        if (res.confirm) {
          api.del('/search/history').then(() => {
            this.setData({ history: [] });
            wx.showToast({
              title: '已清空',
              icon: 'success'
            });
          }).catch(err => {
            console.error('清空搜索历史失败:', err);
          });
        }
      }
    });
  },

  selectHistory: function(e) {
    const keyword = e.currentTarget.dataset.keyword;
    this.setData({ keyword });
    this.onSearch();
  },

  onSearch: function() {
    if (!this.data.keyword || !this.data.keyword.trim()) {
      wx.showToast({
        title: '请输入搜索关键词',
        icon: 'none'
      });
      return;
    }
    
    this.setData({
      page: 1,
      showSuggestions: false
    });
    
    this.search();
  },

  search: function() {
    const that = this;
    const keyword = that.data.keyword.trim();
    
    that.setData({ loading: true });
    
    api.get('/search/unified', {
      keyword: keyword,
      page: that.data.page,
      productLimit: that.data.productLimit,
      noteLimit: that.data.noteLimit
    }).then(res => {
      const products = (res.data && res.data.products) || [];
      const notes = (res.data && res.data.notes) || [];
      
      let productList, noteList;
      if (that.data.page === 1) {
        productList = products;
        noteList = notes;
      } else {
        productList = [...that.data.products, ...products];
        noteList = [...that.data.notes, ...notes];
      }
      
      that.setData({
        products: productList,
        notes: noteList,
        loading: false,
        hasMore: products.length >= that.data.productLimit || notes.length >= that.data.noteLimit
      });
    }).catch(err => {
      console.error('搜索失败:', err);
      wx.showToast({
        title: '搜索失败',
        icon: 'none'
      });
      that.setData({
        loading: false
      });
    });
  },

  loadMore: function() {
    if (!this.data.hasMore || this.data.loading) {
      return;
    }
    
    this.setData({
      page: this.data.page + 1
    });
    
    this.search();
  },

  viewProduct: function(e) {
    const id = e.currentTarget.dataset.id;
    const product = e.currentTarget.dataset.product;
    
    console.log('点击商品:', id, product);
    
    if (id) {
      wx.navigateTo({
        url: '/pages/product-detail/product-detail?id=' + id
      });
    } else if (product && product.productId) {
      wx.navigateTo({
        url: '/pages/product-detail/product-detail?id=' + product.productId
      });
    } else {
      wx.showToast({
        title: '商品信息错误',
        icon: 'none'
      });
    }
  },

  addToCart: function(e) {
    const product = e.currentTarget.dataset.product;
    
    console.log('加入购物车:', product);
    
    if (!product) {
      wx.showToast({
        title: '商品信息错误',
        icon: 'none'
      });
      return;
    }
    
    const token = wx.getStorageSync('token');
    if (!token) {
      wx.showModal({
        title: '提示',
        content: '请先登录后再加入购物车',
        success: (res) => {
          if (res.confirm) {
            wx.switchTab({
              url: '/pages/profile/profile'
            });
          }
        }
      });
      return;
    }
    
    wx.showLoading({
      title: '添加中...'
    });
    
    api.post('/cart', {
      productId: product.id || product.productId,
      quantity: 1
    }).then(res => {
      wx.hideLoading();
      wx.showToast({
        title: '已加入购物车',
        icon: 'success'
      });
    }).catch(err => {
      wx.hideLoading();
      console.error('加入购物车失败:', err);
      wx.showToast({
        title: err.message || '添加失败',
        icon: 'none'
      });
    });
  },

  viewNote: function(e) {
    const id = e.currentTarget.dataset.id;
    const link = e.currentTarget.dataset.link;
    if (link) {
      wx.navigateTo({ url: link });
    } else {
      wx.showToast({
        title: '笔记详情功能开发中',
        icon: 'none'
      });
    }
  },

  onPullDownRefresh() {
    if (this.data.keyword) {
      this.setData({
        page: 1
      });
      this.search();
    }
    wx.stopPullDownRefresh();
  },

  onReachBottom() {
    this.loadMore();
  },

  onShareAppMessage() {
    return {
      title: '搜索',
      path: '/pages/search/search'
    };
  }
});
