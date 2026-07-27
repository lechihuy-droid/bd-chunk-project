export type SseEvent = { event: string; data: unknown }

export async function* parseSse(stream: ReadableStream<Uint8Array>): AsyncGenerator<SseEvent> {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })
      const chunks = buffer.split(/\r?\n\r?\n/)
      buffer = chunks.pop() ?? ''
      for (const chunk of chunks) {
        const lines = chunk.split(/\r?\n/)
        const event = lines.find(line => line.startsWith('event:'))?.slice(6).trim() ?? 'message'
        const data = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).join('\n')
        if (data) { try { yield { event, data: JSON.parse(data) } } catch { yield { event, data } } }
      }
      if (done) break
    }
  } finally { reader.releaseLock() }
}

