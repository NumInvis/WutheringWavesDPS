const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 13078,
    proxy: {
      '/api': {
        target: 'http://localhost:12056',
        changeOrigin: true
      }
    }
  }
})
