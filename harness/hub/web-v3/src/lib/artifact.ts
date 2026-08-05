import { t } from './i18n'
export type ArtifactMessage = { role: string; content: string; streaming?: boolean }
export type ArtifactSummary = { title: string; chars: number; items: number; codeBlocks: number }
const headingPattern = /^(#{1,3})\s+(.+)$/gm
function withoutCodeFences(content: string): string { const lines = content.split('\n'); const visible: string[] = []; let inCode = false; for (const line of lines) { if (line.startsWith('```')) { inCode = !inCode; continue }; if (!inCode) visible.push(line) }; return visible.join('\n') }
function headings(content: string): Array<{ level: number; text: string }> { return [...withoutCodeFences(content).matchAll(headingPattern)].map(match => ({ level: match[1].length, text: match[2].trim() })) }
function openingCodeFences(content: string): number { let inCode = false; let count = 0; for (const line of content.split('\n')) { if (!line.startsWith('```')) continue; if (!inCode) count++; inCode = !inCode }; return count }
export function isArtifact(message: ArtifactMessage): boolean { if (message.role !== 'assistant' || message.streaming === true) return false; return openingCodeFences(message.content) > 0 || message.content.length >= 1200 || headings(message.content).length >= 2 }
export function artifactSummary(content: string): ArtifactSummary { const parsedHeadings = headings(content); const title = parsedHeadings.find(heading => heading.level <= 2)?.text; const firstLine = content.split('\n').find(line => line.trim())?.trim() ?? ''; return { title: title ?? (firstLine.slice(0, 60) || t('artifacts.defaultTitle')), chars: content.length, items: parsedHeadings.length, codeBlocks: openingCodeFences(content) } }
export function artifactHeadings(content: string): string[] { return headings(content).map(heading => heading.text) }
