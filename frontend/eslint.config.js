import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import globals from 'globals'

export default [
  { ignores: ['dist/**', 'node_modules/**'] },
  js.configs.recommended,
  ...vue.configs['flat/essential'],
  { files: ['src/**/*.{js,vue}'], languageOptions: { globals: globals.browser } },
  {
    files: ['tests/**/*.mjs', 'vite.config.js', 'eslint.config.js'],
    languageOptions: { globals: globals.node },
  },
  {
    files: ['tests/**/*.browser.mjs'],
    languageOptions: { globals: { ...globals.node, ...globals.browser } },
  },
  {
    rules: {
      'no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
]
