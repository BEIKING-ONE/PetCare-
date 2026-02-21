const api = require('../../utils/api.js');

Page({
  data: {
    questions: [],
    filteredQuestions: [],
    searchKeyword: '',
    activeCategory: '',
    loading: false
  },

  onLoad() {
    this.loadQuestions();
  },

  onShow() {
    this.loadQuestions();
  },

  loadQuestions: function() {
    this.setData({ loading: true });
    
    api.get('/faq').then(res => {
      const questions = (res.data || []).map(item => ({
        ...item,
        expanded: false
      }));
      
      this.setData({
        questions: questions,
        filteredQuestions: questions,
        loading: false
      });
    }).catch(err => {
      console.error('获取常见问题失败:', err);
      
      const mockQuestions = [
        {
          id: '1',
          category: 'account',
          question: '如何修改个人信息？',
          answer: '您可以在"我的"页面点击头像或昵称进行修改，也可以在设置页面中修改更详细的个人信息。',
          expanded: false
        },
        {
          id: '2',
          category: 'account',
          question: '忘记密码怎么办？',
          answer: '请在登录页面点击"忘记密码"，通过手机验证码或邮箱验证来重置密码。如果仍有问题，请联系客服。',
          expanded: false
        },
        {
          id: '3',
          category: 'order',
          question: '如何查看订单状态？',
          answer: '您可以在"我的订单"页面查看所有订单的状态，包括待付款、待发货、待收货和已完成等状态。',
          expanded: false
        },
        {
          id: '4',
          category: 'order',
          question: '订单可以取消吗？',
          answer: '未发货的订单可以取消。请在订单详情页面点击"取消订单"按钮。已发货的订单无法取消，您可以选择拒收或申请退货。',
          expanded: false
        },
        {
          id: '5',
          category: 'payment',
          question: '支持哪些支付方式？',
          answer: '我们支持微信支付、支付宝、银行卡等多种支付方式，您可以在结算时选择您方便的支付方式。',
          expanded: false
        },
        {
          id: '6',
          category: 'payment',
          question: '支付失败怎么办？',
          answer: '请检查您的网络连接和账户余额。如果问题仍然存在，请尝试更换支付方式或联系客服寻求帮助。',
          expanded: false
        },
        {
          id: '7',
          category: 'delivery',
          question: '配送范围是哪些地区？',
          answer: '我们支持全国大部分地区配送，部分偏远地区可能需要额外运费或无法配送。具体请在结算时查看配送信息。',
          expanded: false
        },
        {
          id: '8',
          category: 'delivery',
          question: '如何查看物流信息？',
          answer: '在订单详情页面点击"查看物流"即可查看最新的物流信息。您也可以通过快递单号在快递官网查询。',
          expanded: false
        },
        {
          id: '9',
          category: 'other',
          question: '如何申请退款？',
          answer: '请在订单详情页面点击"申请退款"，填写退款原因后提交。我们会在1-3个工作日内处理您的退款申请。',
          expanded: false
        },
        {
          id: '10',
          category: 'other',
          question: '优惠券如何使用？',
          answer: '在结算页面，系统会自动显示可用的优惠券，您可以选择使用。请注意优惠券的使用条件和有效期。',
          expanded: false
        }
      ];
      
      this.setData({
        questions: mockQuestions,
        filteredQuestions: mockQuestions,
        loading: false
      });
    });
  },

  onSearchInput: function(e) {
    const keyword = e.detail.value.trim();
    this.setData({ searchKeyword: keyword });
    this.filterQuestions();
  },

  clearSearch: function() {
    this.setData({ searchKeyword: '' });
    this.filterQuestions();
  },

  switchCategory: function(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({ activeCategory: category });
    this.filterQuestions();
  },

  filterQuestions: function() {
    let filtered = this.data.questions;
    
    if (this.data.activeCategory) {
      filtered = filtered.filter(q => q.category === this.data.activeCategory);
    }
    
    if (this.data.searchKeyword) {
      const keyword = this.data.searchKeyword.toLowerCase();
      filtered = filtered.filter(q => 
        q.question.toLowerCase().includes(keyword) || 
        q.answer.toLowerCase().includes(keyword)
      );
    }
    
    this.setData({ filteredQuestions: filtered });
  },

  toggleQuestion: function(e) {
    const id = e.currentTarget.dataset.id;
    const questions = this.data.filteredQuestions.map(q => {
      if (q.id === id) {
        return { ...q, expanded: !q.expanded };
      }
      return q;
    });
    
    this.setData({ filteredQuestions: questions });
  },

  contactService: function() {
    wx.navigateTo({
      url: '/pages/service/service'
    });
  },

  onPullDownRefresh() {
    this.loadQuestions();
    wx.stopPullDownRefresh();
  },

  onShareAppMessage() {
    return {
      title: '常见问题',
      path: '/pages/faq/faq'
    };
  }
});
