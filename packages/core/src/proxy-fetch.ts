/**
 * Proxy-aware Fetch Utility
 * 自动读取 HTTP_PROXY/HTTPS_PROXY 环境变量
 */

import { ProxyAgent, fetch as undiciFetch, type RequestInfo, type RequestInit } from 'undici'

const proxyUrl = process.env.HTTP_PROXY || process.env.HTTPS_PROXY

// 创建复用的 ProxyAgent（避免每次请求都创建新实例）
const proxyAgent = proxyUrl ? new ProxyAgent(proxyUrl) : undefined

if (proxyUrl) {
  console.log(`[ProxyFetch] Using proxy: ${proxyUrl}`)
}

/**
 * 支持代理的 fetch 函数
 * 如果设置了 HTTP_PROXY/HTTPS_PROXY 环境变量，自动使用代理
 */
export async function proxyFetch(
  url: string | URL | RequestInfo,
  init?: RequestInit
): Promise<Response> {
  if (proxyAgent) {
    return undiciFetch(url, { ...init, dispatcher: proxyAgent }) as unknown as Response
  }
  return fetch(url.toString(), init as globalThis.RequestInit)
}

/**
 * 获取代理 URL（供其他库使用）
 */
export function getProxyUrl(): string | undefined {
  return proxyUrl
}

/**
 * 检查是否启用了代理
 */
export function isProxyEnabled(): boolean {
  return !!proxyUrl
}
