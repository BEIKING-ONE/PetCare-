Component({
  data: {
    selected: 0,
    color: "#9CA3AF",
    selectedColor: "#8B5CF6",
    list: [
      {
        pagePath: "/pages/index/index",
        text: "首页",
        iconPath: "/images/tabbar/home.png",
        selectedIconPath: "/images/tabbar/home-active.png"
      },
      {
        pagePath: "/pages/shop/shop",
        text: "商城",
        iconPath: "/images/tabbar/shop.png",
        selectedIconPath: "/images/tabbar/shop-active.png"
      },
      {
        pagePath: "/pages/message/message",
        text: "消息",
        iconPath: "/images/tabbar/message.png",
        selectedIconPath: "/images/tabbar/message-active.png"
      },
      {
        pagePath: "/pages/profile/profile",
        text: "我的",
        iconPath: "/images/tabbar/profile.png",
        selectedIconPath: "/images/tabbar/profile-active.png"
      }
    ],
    rippleIndex: -1,
    iconScale: [1, 1, 1, 1]
  },

  methods: {
    switchTab(e) {
      const index = e.currentTarget.dataset.index;
      const url = this.data.list[index].pagePath;
      
      if (this.data.selected === index) {
        return;
      }
      
      this.playRipple(index);
      
      this.setData({
        selected: index
      });
      
      wx.switchTab({
        url: url
      });
    },

    playRipple(index) {
      let iconScale = [1, 1, 1, 1];
      iconScale[index] = 0.85;
      
      this.setData({
        rippleIndex: index,
        iconScale: iconScale
      });
      
      setTimeout(() => {
        let newScale = [1, 1, 1, 1];
        newScale[index] = 1.08;
        this.setData({
          iconScale: newScale
        });
      }, 100);
      
      setTimeout(() => {
        let finalScale = [1, 1, 1, 1];
        finalScale[index] = 1;
        this.setData({
          iconScale: finalScale,
          rippleIndex: -1
        });
      }, 300);
    },

    onTouchStart(e) {
      const index = e.currentTarget.dataset.index;
      let iconScale = [...this.data.iconScale];
      iconScale[index] = 0.9;
      this.setData({ iconScale });
    },

    onTouchEnd(e) {
      const index = e.currentTarget.dataset.index;
      if (this.data.rippleIndex === -1) {
        let iconScale = [...this.data.iconScale];
        iconScale[index] = 1;
        this.setData({ iconScale });
      }
    }
  }
});
