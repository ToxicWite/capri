// Обложки тем для Tavo Hub в формате 9:16. Hub показывает в карточке и на
// странице темы нижнюю часть картинки (примерно 44–97% высоты), поэтому чат
// с настоящим CSS темы и маленький логотип стоят внизу, сверху только фон.
// Для каждой темы две картинки: покой и генерация.
//
// Запуск: node tools/hub-previews.js   (нужен playwright)
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright')

const ROOT = path.resolve(__dirname, '..')
const W = 360 // CSS-пиксели, снимок в 3x -> 1080×1920
const H = 640

const THEMES = [
  {
    dir: 'capri',
    active: false, // у Капри генерация почти не меняет вид
    bg: 'center top / cover',
    name: 'Capri',
    title: `<img src="ASSETS/eye.png" style="width:24px">
      <span style="font:800 26px 'DejaVu Sans Mono',monospace;color:#2bff6a;letter-spacing:.08em;
        text-shadow:2px 0 0 #ff1644,-2px 0 0 #164cff,3px 3px 0 #7c3aff">CAPRI</span>`,
    avatar: ['#2bff6a', '#09070e'],
    lines: [
      ['c', '*glitches into view* "Hehe. You\'re late, choom."'],
      ['u', 'Get out of his head.'],
      ['c', '"Make me." *a hundred green eyes blink at once*'],
    ],
  },
  {
    dir: 'not-a-human',
    bg: 'center -280px / 420px auto',
    name: 'Guest',
    title: `<img src="ASSETS/energy-5.png" style="height:12px">
      <span style="font:600 15px Inter,sans-serif;color:#e9e4da;letter-spacing:.22em;white-space:nowrap">NO, I'M NOT A HUMAN</span>`,
    avatar: ['#6fe0d4', '#04100e'],
    lines: [
      ['c', '"Let me in. The sun is coming up."'],
      ['u', 'Show me your hands first.'],
      ['c', '*his nails are perfectly clean* "Please."'],
    ],
  },
  {
    dir: 'tlou-spores',
    bg: 'center top / cover',
    name: 'Joel',
    title: `<span style="font:700 26px Inter,sans-serif;color:#efe6d2;letter-spacing:.24em;text-shadow:0 3px 12px #000">SPORES</span>
      <span style="font:500 10px Inter,sans-serif;color:#d6ba6e;letter-spacing:.28em">TLOU · PART I</span>`,
    avatar: ['#d6ba6e', '#1c2018'],
    lines: [
      ['c', '"Mask on. Spores are thick down here."'],
      ['u', 'Is that... clicking?'],
      ['c', '*kills the flashlight* "Stay low. Not a sound."'],
    ],
  },
]

const rgba = (n) => {
  if (n == null) return 'inherit'
  const a = ((n >>> 24) & 255) / 255
  return `rgba(${(n >>> 16) & 255}, ${(n >>> 8) & 255}, ${n & 255}, ${a.toFixed(3)})`
}

// Силуэт «голова и плечи» вместо смайлика
const avatarSvg = ([fg, bg]) =>
  'data:image/svg+xml,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="${bg}"/>` +
      `<circle cx="32" cy="25" r="12" fill="${fg}" opacity="0.85"/><path d="M8 64c2-14 12-22 24-22s22 8 24 22z" fill="${fg}" opacity="0.85"/></svg>`
  )

function richText(text, font) {
  const tone = font.toneTextStyle
  const quote = font.quoteTextStyle
  return text.replace(/(\*[^*]+\*)|("[^"]+")/g, (_, act, q) =>
    act
      ? `<span style="color:${rgba(tone.color)};font-style:${tone.fontStyle}">${act}</span>`
      : `<span style="color:${rgba(quote.color)};font-weight:${quote.fontWeight}">${q}</span>`)
}

function page(t, m, generating) {
  const assets = 'file://' + path.join(ROOT, 'themes', t.dir, 'assets') + '/'
  const css = m.custom_css.replaceAll('theme/assets/', assets)
  const bg = m.background.image.replace('theme/assets/', assets)
  const cf = m.character_bubble_font
  const uf = m.user_bubble_font
  const ava = avatarSvg(t.avatar)
  const userAva = avatarSvg(['#9a9a92', '#2a2a28'])
  const rows = t.lines.map(([who, text]) => {
    const c = who === 'c'
    return `<div class="row ${c ? '' : 'u'}">
      <img class="tavo-avatar ${c ? 'tavo-character-avatar' : 'tavo-user-avatar'}" src="${c ? ava : userAva}">
      <div class="col"><div class="tavo-speaker-name">${c ? t.name : 'You'}</div>
        <div class="tavo-bubble ${c ? 'tavo-character-bubble' : 'tavo-user-bubble'}">
          <div class="tavo-bubble-content ${c ? 'tavo-character-bubble-content' : 'tavo-user-bubble-content'}">
            <div class="tavo-message-content" style="color:${rgba((c ? cf : uf).textStyle.color)}">${richText(text, c ? cf : uf)}</div>
          </div></div></div></div>`
  }).join('')
  const con = m.console
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    html,body{margin:0}
    body{width:${W}px;height:${H}px;overflow:hidden;display:flex;flex-direction:column;
      background:${rgba(m.background.color)} url("${bg}") ${t.bg} no-repeat;font-family:Inter,"Roboto",sans-serif}
    .head{height:322px;box-sizing:border-box;display:flex;align-items:flex-end;justify-content:center;
      gap:10px;padding-bottom:4px}
    .top{display:flex;flex-direction:column}
    .list{flex:1;padding:6px 12px 0;display:flex;flex-direction:column;gap:6px}
    .row{display:flex;gap:7px;align-items:flex-start}.row.u{flex-direction:row-reverse}
    img.tavo-avatar{width:30px;height:30px;flex:none}
    .col{display:flex;flex-direction:column;gap:3px;max-width:82%}.u .col{align-items:flex-end}
    .tavo-speaker-name{font-size:10px}
    .tavo-bubble{padding:7px 10px}
    .tavo-message-content{font-size:13px;line-height:1.45}
    .tavo-composer{padding:6px 10px 6px}
    .tavo-composer-shell{display:flex;align-items:center;gap:8px;padding:9px 12px;
      background-color:${rgba(con.color)};border-radius:${con.radius}px}
    .tavo-composer-input{flex:1;font-size:13px;color:${rgba(con.placeholderColor)}}
    .ic{width:18px;height:18px}
  </style><style>${css}</style></head><body>
    <div class="head">${t.title.replaceAll('ASSETS/', assets)}</div><div class="top">
    <div class="list">${rows}</div>
    <div class="tavo-composer"><div class="tavo-composer-shell">
      <svg class="ic tavo-composer-add-icon" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" stroke="${rgba(con.fontColor)}" stroke-width="2"/></svg>
      <div class="tavo-composer-input">Say something…</div>
      ${generating
        ? `<svg class="ic tavo-composer-stop-icon" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2" fill="${rgba(con.sendColor)}"/></svg>`
        : `<svg class="ic tavo-composer-send-icon" viewBox="0 0 24 24"><path d="M4 12l16-8-5 16-3-6z" fill="${rgba(con.sendColor)}"/></svg>`}
    </div></div></div></body></html>`
}

;(async () => {
  const browser = await chromium.launch()
  const p = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 3 })
  for (const t of THEMES) {
    const m = JSON.parse(fs.readFileSync(path.join(ROOT, 'themes', t.dir, 'theme.json'), 'utf8'))
    const states = t.active === false ? [['hub', false]] : [['hub', false], ['hub-active', true]]
    for (const [suffix, gen] of states) {
      const html = path.join(ROOT, 'themes', t.dir, `.preview-${suffix}.html`)
      fs.writeFileSync(html, page(t, m, gen))
      await p.goto('file://' + html)
      await p.waitForTimeout(gen ? 3200 : 1200)
      const out = path.join(ROOT, 'themes', t.dir, `preview-${suffix}.png`)
      await p.screenshot({ path: out })
      fs.unlinkSync(html)
      console.log(out)
    }
  }
  await browser.close()
})()
