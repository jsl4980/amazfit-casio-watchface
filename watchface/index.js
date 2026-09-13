import '../shared/device-polyfill'

/**
 * AE-1200WHD-1AV-style face for Amazfit Bip 6 (390×450).
 * Top-left dial → step progress · Map → HR · Top-right → battery
 * Bottom → day, month-day, HH:MM (no seconds)
 *
 * Uses the classic global hmUI API, so app.json must target apiVersion 1.0.x
 * (API 2.0+ with hmUI crashes to a black screen on Bip 6).
 */

const LARGE = [
  'font/large/0.png', 'font/large/1.png', 'font/large/2.png', 'font/large/3.png', 'font/large/4.png',
  'font/large/5.png', 'font/large/6.png', 'font/large/7.png', 'font/large/8.png', 'font/large/9.png'
]

const SMALL = [
  'font/small/0.png', 'font/small/1.png', 'font/small/2.png', 'font/small/3.png', 'font/small/4.png',
  'font/small/5.png', 'font/small/6.png', 'font/small/7.png', 'font/small/8.png', 'font/small/9.png'
]

const WEEK = [
  'week/mon.png', 'week/tue.png', 'week/wed.png', 'week/thu.png',
  'week/fri.png', 'week/sat.png', 'week/sun.png'
]

const STEP_PROGRESS = [
  'progress/0.png', 'progress/1.png', 'progress/2.png', 'progress/3.png', 'progress/4.png',
  'progress/5.png', 'progress/6.png', 'progress/7.png', 'progress/8.png', 'progress/9.png'
]

const BATTERY_PROGRESS = [
  'battery/0.png', 'battery/1.png', 'battery/2.png', 'battery/3.png', 'battery/4.png',
  'battery/5.png', 'battery/6.png', 'battery/7.png', 'battery/8.png', 'battery/9.png'
]

WatchFace({
  onInit() {
    console.log('ae1200whd onInit')
  },

  build() {
    hmUI.createWidget(hmUI.widget.IMG, {
      x: 0, y: 0, w: 390, h: 450,
      src: 'bg/bg.png',
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    // Dial center (100,130) r=64 → progress 140×140 @ (30,60)
    // Full-ring frames need IMG_LEVEL (IMG_PROGRESS stacks segments via x/y arrays)
    hmUI.createWidget(hmUI.widget.IMG_LEVEL, {
      x: 30, y: 60,
      w: 140, h: 140,
      image_array: STEP_PROGRESS,
      image_length: 10,
      type: hmUI.data_type.STEP,
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    // Centered in dial (100,130); w fits 5 small digits
    hmUI.createWidget(hmUI.widget.TEXT_IMG, {
      x: 45, y: 116, w: 110, h: 28,
      font_array: SMALL,
      invalid_image: 'font/invalid.png',
      h_space: 1,
      align_h: hmUI.align.CENTER_H,
      type: hmUI.data_type.STEP,
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    // Battery centered in BAT well (72×28 inside 96×52 @ 268,72)
    hmUI.createWidget(hmUI.widget.IMG_LEVEL, {
      x: 280, y: 84,
      w: 72, h: 28,
      image_array: BATTERY_PROGRESS,
      image_length: 10,
      type: hmUI.data_type.BATTERY,
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    hmUI.createWidget(hmUI.widget.TEXT_IMG, {
      x: 238, y: 168, w: 118, h: 60,
      font_array: LARGE,
      invalid_image: 'font/invalid.png',
      h_space: 2,
      align_h: hmUI.align.CENTER_H,
      type: hmUI.data_type.HEART,
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    hmUI.createWidget(hmUI.widget.IMG_WEEK, {
      x: 55, y: 265,
      week_en: WEEK, week_tc: WEEK, week_sc: WEEK,
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    hmUI.createWidget(hmUI.widget.IMG_DATE, {
      month_startX: 175,
      month_startY: 265,
      month_space: 1,
      month_zero: 0,
      month_en_array: SMALL,
      month_tc_array: SMALL,
      month_sc_array: SMALL,
      day_follow: 1,
      day_space: 1,
      day_zero: 1,
      day_en_array: SMALL,
      day_tc_array: SMALL,
      day_sc_array: SMALL,
      month_unit_en: 'font/dash.png',
      month_unit_tc: 'font/dash.png',
      month_unit_sc: 'font/dash.png',
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    hmUI.createWidget(hmUI.widget.IMG, {
      x: 155, y: 315,
      src: 'font/colon.png',
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    hmUI.createWidget(hmUI.widget.IMG_TIME, {
      hour_zero: 1,
      hour_startX: 55,
      hour_startY: 310,
      hour_space: 2,
      hour_array: LARGE,
      minute_zero: 1,
      minute_startX: 175,
      minute_startY: 310,
      minute_space: 2,
      minute_array: LARGE,
      am_x: 300, am_y: 270,
      am_sc_path: 'ampm/am.png',
      am_tc_path: 'ampm/am.png',
      am_en_path: 'ampm/am.png',
      pm_x: 300, pm_y: 270,
      pm_sc_path: 'ampm/pm.png',
      pm_tc_path: 'ampm/pm.png',
      pm_en_path: 'ampm/pm.png',
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    hmUI.createWidget(hmUI.widget.BUTTON, {
      x: 30, y: 60, w: 140, h: 140,
      normal_src: 'ui/tap_step.png',
      press_src: 'ui/tap_step.png',
      click_func: () => {
        hmApp.startApp({ appid: 1, url: 'activityAppScreen', native: true })
      }
    })

    hmUI.createWidget(hmUI.widget.BUTTON, {
      x: 230, y: 138, w: 134, h: 90,
      normal_src: 'ui/tap_hr.png',
      press_src: 'ui/tap_hr.png',
      click_func: () => {
        hmApp.startApp({ appid: 1, url: 'heart_app_Screen', native: true })
      }
    })
  },

  onDestroy() {
    console.log('ae1200whd onDestroy')
  }
})
