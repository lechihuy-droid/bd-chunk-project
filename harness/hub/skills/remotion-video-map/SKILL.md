---
name: remotion-video-map
description: Author a complete VideoMap JSON contract for the Lucida Remotion renderer.
---

# Remotion VideoMap

1. Return one JSON object with `video`, `theme`, `assets`, and `scenes`.
2. Set `video` fields: `title`, `subtitle`, `format`, `width`, `height`, `fps`, `durationSec`, `style`, and `language`. The reference renderer uses 1080×1920 at 30fps.
3. Use `theme` for visual tokens and `assets[]` for referenced visual material.
4. Give every `scenes[]` item `id`, `intent`, `durationSec`, `headline`, `subtitle`, `content`, `style`, `motion`, `templateId`, and `templateRole`.
5. Choose slides mode for distinct cards or continuous mode for a flowing narrative; make scene durations agree with `video.durationSec`.

State uncertainty in the JSON content; do not invent verified facts.
