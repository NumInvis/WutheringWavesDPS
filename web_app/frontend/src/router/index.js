import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Characters from '../views/Characters.vue'
import CharacterDetail from '../views/CharacterDetail.vue'
import Actions from '../views/Actions.vue'
import Echoes from '../views/Echoes.vue'
import Calculator from '../views/Calculator.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '首页' }
  },
  {
    path: '/characters',
    name: 'Characters',
    component: Characters,
    meta: { title: '角色数据库' }
  },
  {
    path: '/characters/:id',
    name: 'CharacterDetail',
    component: CharacterDetail,
    meta: { title: '角色详情' }
  },
  {
    path: '/actions',
    name: 'Actions',
    component: Actions,
    meta: { title: '动作查询' }
  },
  {
    path: '/echoes',
    name: 'Echoes',
    component: Echoes,
    meta: { title: '声骸数据库' }
  },
  {
    path: '/calculator',
    name: 'Calculator',
    component: Calculator,
    meta: { title: '伤害计算器' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 鸣潮动作数据汇总` : '鸣潮动作数据汇总'
  next()
})

export default router
