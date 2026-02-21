// pages/customer-chat/customer-chat.js
Page({
  data: {
    messages: [],
    inputContent: '',
    scrollToView: '',
    showQuickReplies: true,
    quickReplies: [
      '如何注册账号？',
      '如何添加宠物？',
      '订单支付问题',
      '优惠券如何使用？',
      '配送范围和时间',
      '退换货政策'
    ]
  },

  onLoad() {
    this.addWelcomeMessage();
  },

  addWelcomeMessage: function() {
    const welcomeMsg = {
      id: Date.now(),
      type: 'service',
      content: '您好！我是在线客服，很高兴为您服务。请问有什么可以帮助您的？',
      time: this.getCurrentTime()
    };

    this.setData({
      messages: [welcomeMsg]
    });
  },

  getCurrentTime: function() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
  },

  onInputChange: function(e) {
    this.setData({
      inputContent: e.detail.value
    });
  },

  sendMessage: function() {
    const content = this.data.inputContent.trim();
    if (!content) {
      return;
    }

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: content,
      time: this.getCurrentTime()
    };

    const messages = [...this.data.messages, userMessage];
    
    this.setData({
      messages: messages,
      inputContent: '',
      showQuickReplies: false,
      scrollToView: 'msg-' + (messages.length - 1)
    });

    setTimeout(() => {
      this.replyMessage(content);
    }, 1000);
  },

  sendQuickReply: function(e) {
    const content = e.currentTarget.dataset.content;
    
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: content,
      time: this.getCurrentTime()
    };

    const messages = [...this.data.messages, userMessage];
    
    this.setData({
      messages: messages,
      showQuickReplies: false,
      scrollToView: 'msg-' + (messages.length - 1)
    });

    setTimeout(() => {
      this.replyMessage(content);
    }, 1000);
  },

  replyMessage: function(userContent) {
    let replyContent = '';
    
    if (userContent.includes('注册') || userContent.includes('账号')) {
      replyContent = '注册账号非常简单：\n1. 打开APP点击"我的"\n2. 点击"登录/注册"\n3. 输入手机号获取验证码\n4. 设置密码即可完成注册\n\n如有其他问题请继续咨询~';
    } else if (userContent.includes('宠物') || userContent.includes('添加')) {
      replyContent = '添加宠物步骤：\n1. 进入"我的"页面\n2. 点击"我的宠物"\n3. 点击右下角"+"按钮\n4. 填写宠物信息并保存\n\n您的宠物信息我们会严格保密~';
    } else if (userContent.includes('订单') || userContent.includes('支付')) {
      replyContent = '关于订单支付：\n1. 选择商品加入购物车\n2. 结算时选择收货地址\n3. 选择支付方式（微信支付）\n4. 确认支付即可\n\n支付遇到问题可以拨打客服热线：400-888-8888';
    } else if (userContent.includes('优惠券')) {
      replyContent = '优惠券使用说明：\n1. 在首页点击"领取优惠券"\n2. 领取后下单时自动抵扣\n3. 每个订单只能使用一张优惠券\n4. 优惠券不可叠加使用\n\n您可以在"我的-优惠券"查看已领取的优惠券~';
    } else if (userContent.includes('配送') || userContent.includes('快递')) {
      replyContent = '配送说明：\n1. 配送范围：全国大部分地区\n2. 配送时间：下单后1-3个工作日\n3. 满99元免运费\n4. 可在订单详情查看物流信息\n\n如有特殊配送需求请备注说明~';
    } else if (userContent.includes('退') || userContent.includes('换货')) {
      replyContent = '退换货政策：\n1. 收货后7天内可申请退换\n2. 商品需保持原包装完好\n3. 在订单详情点击"申请售后"\n4. 客服会在24小时内处理\n\n如有问题请拨打：400-888-8888';
    } else {
      replyContent = '感谢您的咨询！您的问题已收到，人工客服将在24小时内与您联系。如需紧急帮助，请拨打客服热线：400-888-8888';
    }

    const replyMessage = {
      id: Date.now(),
      type: 'service',
      content: replyContent,
      time: this.getCurrentTime()
    };

    const messages = [...this.data.messages, replyMessage];
    
    this.setData({
      messages: messages,
      scrollToView: 'msg-' + (messages.length - 1)
    });
  },

  onShareAppMessage() {
    return {
      title: '在线客服',
      path: '/pages/customer-chat/customer-chat'
    };
  }
});
