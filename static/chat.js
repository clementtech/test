const chatEl = document.getElementById('chat')
const input = document.getElementById('message')
const sendBtn = document.getElementById('send')
const statusEl = document.getElementById('status')
const modelInput = document.getElementById('model')

function ts() {
  return new Date().toLocaleTimeString()
}

function makeBubble(role, text) {
  const li = document.createElement('li')
  li.className = 'bubble ' + role
  const body = document.createElement('div')
  body.className = 'body'
  body.textContent = text
  const meta = document.createElement('div')
  meta.className = 'meta'
  meta.textContent = ts()
  li.appendChild(body)
  li.appendChild(meta)
  return li
}

function append(role, text) {
  const el = makeBubble(role, text)
  chatEl.appendChild(el)
  chatEl.scrollTop = chatEl.scrollHeight
}

function setStatus(text) {
  statusEl.textContent = text || ''
}

async function sendMessage(msg) {
  const text = msg || input.value.trim()
  if (!text) return
  append('user', text)
  input.value = ''
  sendBtn.disabled = true
  setStatus('Gemma is typing...')
  // Build messages array; include a system prompt if homework assistant fields are set
  const messages = []
  const subj = document.getElementById('hw-subject') ? document.getElementById('hw-subject').value.trim() : ''
  const diff = document.getElementById('hw-difficulty') ? document.getElementById('hw-difficulty').value : ''
  const step = document.getElementById('hw-step') ? document.getElementById('hw-step').checked : false
  if (subj || diff || step) {
    let instr = 'You are a helpful homework assistant.'
    if (subj) instr += ` Subject: ${subj}.`
    if (diff) instr += ` Difficulty: ${diff}.`
    if (step) instr += ` Provide step-by-step solutions.`
    messages.push({ role: 'system', content: instr })
  }
  // if a file was attached and contains text, include it as a prior message
  if (attachedFile && attachedFile.text) {
    messages.push({ role: 'user', content: `Attached file (${attachedFile.filename}):\n${attachedFile.text}` })
  }
  messages.push({ role: 'user', content: text })

  const payload = { messages }
  const model = modelInput.value.trim()
  if (model) payload.model = model

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    const data = await res.json()
    if (!res.ok) {
      append('assistant', 'Error: ' + (data.message || data.error || res.statusText))
      if (data.example_install) append('assistant', 'Try: ' + data.example_install)
      return
    }

    const assistantText = data.assistant || (data.raw_response ? JSON.stringify(data.raw_response) : '')
    append('assistant', assistantText)
    // clear attachment after successful send
    if (attachedFile) {
      attachedFile = null
      attachedEl.textContent = ''
      fileInput.value = ''
    }
  } catch (err) {
    append('assistant', 'Network error: ' + err.message)
  } finally {
    sendBtn.disabled = false
    setStatus('')
  }
}

document.getElementById('composer').addEventListener('submit', (e) => { e.preventDefault(); sendMessage() })
input.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } })

// welcome message

// Load history from server
async function loadHistory(){
  try{
    const r = await fetch('/api/history')
    if (!r.ok) return
    const d = await r.json()
    console.log('history payload:', d)
    const h = d.history || []
    // group into conversations: naive split on 'assistant' entries to create sets
    const convs = []
    let cur = []
    h.forEach(m => {
      cur.push(m)
      if (m.role === 'assistant') {
        convs.push(cur)
        cur = []
      }
    })
    if (cur.length) convs.push(cur)

    renderConversations(convs)
    if (convs && convs.length > 0) {
      selectConversation(0)
      setStatus(`Loaded ${h.length} messages across ${convs.length} conversations`)
    } else {
      setStatus('No conversations found')
    }
  }catch(e){ console.warn('history load failed', e) }
}

loadHistory()

// welcome message if empty
if (!chatEl.children.length) append('assistant', "Hello — I'm Gemma (via Ollama). Type a message and press Enter.")

// Clear history handler
const clearBtn = document.getElementById('clearHistory')
if (clearBtn) clearBtn.addEventListener('click', async () => {
  try{
    const r = await fetch('/api/clear-history', { method: 'POST' })
    if (r.ok){
      // remove rendered messages
      chatEl.innerHTML = ''
      append('assistant', "History cleared.")
    } else {
      append('assistant', 'Failed to clear history')
    }
  }catch(e){ append('assistant', 'Failed to clear history: ' + e.message) }
})

// Render conversation list
const convsEl = document.getElementById('conversations')
let conversations = []
let activeIndex = -1

function renderConversations(convs){
  conversations = convs
  convsEl.innerHTML = ''
  convs.forEach((c, i) => {
    const div = document.createElement('div')
    div.className = 'conversation-item'
    div.textContent = (c.find(m=>m.role==='user')||{content:'Chat'}).content.slice(0,40)
    div.addEventListener('click', () => selectConversation(i))
    convsEl.appendChild(div)
  })
}

function selectConversation(i){
  if (!conversations || i < 0 || i >= conversations.length) return
  activeIndex = i
  // highlight
  Array.from(convsEl.children).forEach((ch, idx) => ch.classList.toggle('active', idx===i))
  // render conversation
  chatEl.innerHTML = ''
  for (const m of conversations[i]) append(m.role, m.content)
  // scroll chat into view
  chatEl.scrollTop = chatEl.scrollHeight
}

// New chat (does not clear saved history)
const newBtn = document.getElementById('newChat')
if (newBtn) newBtn.addEventListener('click', () => {
  activeIndex = -1
  Array.from(convsEl.children).forEach(ch => ch.classList.remove('active'))
  chatEl.innerHTML = ''
  append('assistant', "New chat — I'm Gemma. Type a message.")
})

// Helpers to get current conversation (from selected conv or DOM)
function getCurrentConversation(){
  if (activeIndex >= 0 && conversations[activeIndex]){
    return conversations[activeIndex]
  }
  // read from DOM
  const items = []
  chatEl.querySelectorAll('.bubble').forEach(b => {
    const role = b.classList.contains('user') ? 'user' : 'assistant'
    const content = b.querySelector('.body') ? b.querySelector('.body').textContent : b.textContent
    items.push({role, content})
  })
  return items
}

// File upload handling
const fileInput = document.getElementById('fileInput')
const uploadBtn = document.getElementById('uploadBtn')
const attachedEl = document.getElementById('attachedFile')
let attachedFile = null

if (uploadBtn && fileInput) uploadBtn.addEventListener('click', async () => {
  const file = fileInput.files[0]
  if (!file) return alert('Select a file first')
  const form = new FormData()
  form.append('file', file)
  try{
    const r = await fetch('/api/upload', { method: 'POST', body: form })
    const data = await r.json()
    if (r.ok && data.filename){
      attachedFile = data
      attachedEl.textContent = `Attached: ${data.filename}`
    } else {
      alert('Upload failed')
    }
  }catch(e){ alert('Upload failed: ' + e.message) }
})

// Download current conversation as .txt
const downloadBtn = document.getElementById('downloadBtn')
if (downloadBtn) downloadBtn.addEventListener('click', () => {
  const conv = getCurrentConversation()
  if (!conv || !conv.length) return alert('No conversation to download')
  const filename = prompt('Filename', 'conversation') || 'conversation'
  const lines = conv.map(m => (m.role === 'user' ? 'User: ' : 'Assistant: ') + m.content)
  const blob = new Blob([lines.join('\n')], {type: 'text/plain;charset=utf-8'})
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename + '.txt'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
})

// Save conversation to server (exports/)
const saveServerBtn = document.getElementById('saveServerBtn')
if (saveServerBtn) saveServerBtn.addEventListener('click', async () => {
  const conv = getCurrentConversation()
  if (!conv || !conv.length) return alert('No conversation to save')
  const filename = prompt('Filename on server', 'conversation') || 'conversation'
  try{
    const r = await fetch('/api/save-conversation', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ conversation: conv, filename })
    })
    const data = await r.json()
    if (r.ok && data.url){
      // open the returned URL in a new tab
      window.open(data.url, '_blank')
    } else {
      alert('Save failed: ' + (data.error || 'unknown'))
    }
  }catch(e){ alert('Save failed: ' + e.message) }
})
