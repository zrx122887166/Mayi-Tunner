// import router from './router'
// import NProgress from 'nprogress' // progress bar
// import 'nprogress/nprogress.css' // progress bar style
// NProgress.configure({ showSpinner: false }) // NProgress Configuration
// console.log(router)
// router.beforeEach(async(to, from, next) => {
//   console.log('asdassd')

//   next()
// })

// router.afterEach(() => {
//   // finish progress bar
//   console.log('123123')
//   NProgress.done()
// })


// src/apis/permission.js
import axios from 'axios';

// 新增工具分类的接口请求（路径要和你后端的分类新增接口一致）
export const addMenu = (menuData) => {
  return axios.post(`${process.env.VUE_APP_BASE_API}/testrunner/menu/add`, menuData);
};