#!/usr/bin/env bun
/**
 * @marketpulse/cli
 * CLI entry point
 */

import { APP_NAME, APP_VERSION } from '@marketpulse/shared'
import { startServer } from '@marketpulse/server'

const COMMANDS = {
  server: '启动 API 服务器',
  tui: '启动终端界面 (TUI)',
  desktop: '启动桌面应用',
  help: '显示帮助信息',
  version: '显示版本号',
} as const

function printHelp() {
  console.log(`
${APP_NAME} v${APP_VERSION}
企业级金融智能助手

用法:
  marketpulse [命令] [选项]

命令:
  server      ${COMMANDS.server}
  tui         ${COMMANDS.tui}
  desktop     ${COMMANDS.desktop}
  help        ${COMMANDS.help}
  version     ${COMMANDS.version}

选项:
  -h, --help      显示帮助
  -v, --version   显示版本

示例:
  marketpulse              启动 TUI (默认)
  marketpulse server       启动 API 服务器
  marketpulse server -p 8080  指定端口
`)
}

function printVersion() {
  console.log(`${APP_NAME} v${APP_VERSION}`)
}

async function main() {
  const args = process.argv.slice(2)
  const command = args[0] || 'tui'

  switch (command) {
    case 'server':
      startServer()
      break

    case 'tui':
      console.log('🚧 TUI 尚未实现，请等待后续版本')
      console.log('💡 你可以先使用 `marketpulse server` 启动 API 服务')
      break

    case 'desktop':
      console.log('🚧 Desktop 应用尚未实现，请等待后续版本')
      break

    case 'help':
    case '-h':
    case '--help':
      printHelp()
      break

    case 'version':
    case '-v':
    case '--version':
      printVersion()
      break

    default:
      console.error(`未知命令: ${command}`)
      printHelp()
      process.exit(1)
  }
}

main().catch((error) => {
  console.error('Error:', error)
  process.exit(1)
})
