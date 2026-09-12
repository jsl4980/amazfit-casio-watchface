import './shared/device-polyfill'

App({
  globalData: {},
  onCreate(options) {
    console.log('ae1200 app onCreate')
  },

  onDestroy(options) {
    console.log('ae1200 app onDestroy')
  }
})
