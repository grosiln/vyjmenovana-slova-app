import streamlit as st
import streamlit.components.v1 as components


def spustit_hru():
    st.session_state.space_invaders = {"aktivni": True, "pozadat_navrat": False}


def _html_hry() -> str:
    return r"""
<div id="si-wrap" style="font-family: sans-serif; user-select: none;">
  <div style="color:#fff; background:#0b0f2a; padding:10px 14px; border-radius:12px 12px 0 0;
              display:flex; justify-content:space-between; font-weight:700; font-size:18px;">
    <span id="si-score">Skóre: 0</span>
    <span id="si-lives">❤️❤️❤️</span>
    <span id="si-stars">⭐ 0</span>
  </div>
  <canvas id="si-canvas" width="640" height="520"
          style="background:#000; display:block; margin:0 auto; outline: none; border: 2px solid #1a2050; cursor: crosshair;"></canvas>
  <div id="si-msg" style="color:#fff; background:#0b0f2a; padding:10px 14px;
                          border-radius:0 0 12px 12px; text-align:center; font-weight:600;">
    🔊 Klikni do hry pro zapnutí zvuku. Ovládání: ← → pohyb, Mezerník = střelba
  </div>
</div>

<script>
(function(){
  const canvas = document.getElementById('si-canvas');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const scoreEl = document.getElementById('si-score');
  const livesEl = document.getElementById('si-lives');
  const starsEl = document.getElementById('si-stars');
  const msgEl = document.getElementById('si-msg');

  // ---------- AUDIO ----------
  let audioCtx = null;
  let audioReady = false;
  function ensureAudio(){
    if(!audioCtx){
      try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); }
      catch(e){ audioCtx = null; }
    }
    if(audioCtx){
      if(audioCtx.state === 'suspended'){ audioCtx.resume(); }
      audioReady = true;
    }
  }
  // Zapni audio pri jakekoliv interakci (klik / klavesa) v iframe
  document.addEventListener('mousedown', ensureAudio);
  document.addEventListener('keydown', ensureAudio);
  document.addEventListener('touchstart', ensureAudio);

  function tone(freq, dur, type='square', vol=0.08){
    if(!audioCtx) return;
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.type = type; o.frequency.value = freq;
    g.gain.value = vol;
    o.connect(g); g.connect(audioCtx.destination);
    o.start();
    g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + dur);
    o.stop(audioCtx.currentTime + dur + 0.02);
  }
  function noise(dur, vol=0.25){
    if(!audioCtx) return;
    const len = Math.floor(audioCtx.sampleRate * dur);
    const buf = audioCtx.createBuffer(1, len, audioCtx.sampleRate);
    const d = buf.getChannelData(0);
    for(let i=0;i<len;i++){
      d[i] = (Math.random()*2-1) * Math.pow(1 - i/len, 2);
    }
    const src = audioCtx.createBufferSource(); src.buffer = buf;
    const g = audioCtx.createGain(); g.gain.value = vol;
    src.connect(g); g.connect(audioCtx.destination);
    src.start();
  }
  function sndShoot(){ tone(900, 0.08, 'square', 0.08); tone(1400, 0.05, 'square', 0.05); }
  function sndAlienShoot(){ tone(220, 0.14, 'sawtooth', 0.09); }
  function sndAlienHit(){ noise(0.18, 0.25); tone(520, 0.1, 'triangle', 0.08); }
  function sndPlayerBoom(){ noise(0.7, 0.35); tone(110, 0.5, 'sawtooth', 0.18); }
  function sndStar(){ tone(1200, 0.08, 'sine', 0.12); tone(1700, 0.1, 'sine', 0.1); }

  // ---------- STATE ----------
  // stav: 'playing' | 'gameover' | 'won'
  let state;
  let player, bullets, enemyBullets, enemies, stars;
  let dir, score, lives, starCount, tick, shootCd;
  let gameOverAnim;

  function makeEnemies(){
    const arr = [];
    const rows = 4, cols = 8;
    const offsetX = 60, offsetY = 50;
    for(let r=0;r<rows;r++){
      for(let c=0;c<cols;c++){
        arr.push({
          x: offsetX + c*64, y: offsetY + r*42,
          w: 40, h: 26, alive: true,
          kind: r
        });
      }
    }
    return arr;
  }

  function resetGame(){
    player = { x: W/2-24, y: H-46, w: 48, h: 22 };
    bullets = [];
    enemyBullets = [];
    stars = [];
    enemies = makeEnemies();
    dir = 1;
    score = 0; lives = 3; starCount = 0;
    tick = 0; shootCd = 0;
    state = 'playing';
    gameOverAnim = 0;
    msgEl.textContent = '← → pohyb, Mezerník = střelba. 3 životy. Hodně štěstí!';
  }

  function pozadejNavrat(){
    // Signal pro Streamlit: ulozime priznak do URL a refreshneme rodice s dotazem.
    // Protoze iframe nemuze primo klikat na Streamlit tlacitko, uzivatele dovedeme k tlacitku pod hrou.
    msgEl.innerHTML = '👇 <b>Klikni dole na tlačítko "⬅️ Zpět na výběr her"</b>';
    // Zvyraznim vizualne canvas, aby to bylo jasne
    canvas.style.opacity = '0.5';
  }

  // ---------- INPUT ----------
  const keys = {};
  canvas.tabIndex = 0;
  canvas.addEventListener('mousedown', ()=>{
    canvas.focus();
    ensureAudio();
    if(state === 'gameover' || state === 'won'){
      // Klik na hlasku = pozadat o navrat na vyber her
      pozadejNavrat();
    }
  });
  canvas.addEventListener('keydown', (e)=>{
    if(['ArrowLeft','ArrowRight','Space'].includes(e.code)) e.preventDefault();
    keys[e.code] = true;
    if(state === 'playing' && e.code === 'Space' && shootCd<=0){
      bullets.push({ x: player.x + player.w/2 - 2, y: player.y - 2, w: 4, h: 12 });
      shootCd = 12;
      sndShoot();
    }
    if((state === 'gameover' || state === 'won') && e.code === 'Enter'){
      resetGame();
      canvas.style.opacity = '1';
    }
  });
  canvas.addEventListener('keyup', (e)=>{ keys[e.code] = false; });

  // ---------- UPDATE ----------
  function update(){
    tick++;
    if(state !== 'playing'){
      gameOverAnim++;
      return;
    }

    const speed = 6;
    if(keys['ArrowLeft']) player.x -= speed;
    if(keys['ArrowRight']) player.x += speed;
    player.x = Math.max(6, Math.min(W - player.w - 6, player.x));

    if(shootCd > 0) shootCd--;

    bullets.forEach(b => b.y -= 9);
    bullets = bullets.filter(b => b.y + b.h > 0);
    enemyBullets.forEach(b => b.y += 5);
    enemyBullets = enemyBullets.filter(b => b.y < H);

    const alive = enemies.filter(e => e.alive);
    if(alive.length === 0){
      state = 'won';
      return;
    }
    const speedE = 0.6 + (enemies.length - alive.length) * 0.07;
    const minX = Math.min(...alive.map(e => e.x));
    const maxX = Math.max(...alive.map(e => e.x + e.w));
    if(maxX + dir*speedE > W - 6 || minX + dir*speedE < 6){
      dir *= -1;
      enemies.forEach(e => e.y += 18);
    } else {
      enemies.forEach(e => e.x += dir*speedE);
    }

    if(Math.random() < 0.025 && alive.length){
      const shooter = alive[Math.floor(Math.random()*alive.length)];
      enemyBullets.push({
        x: shooter.x + shooter.w/2 - 2,
        y: shooter.y + shooter.h,
        w: 4, h: 12
      });
      sndAlienShoot();
    }

    if(Math.random() < 0.005){
      stars.push({
        x: 20 + Math.random()*(W-60),
        y: -24, w: 24, h: 24
      });
    }
    stars.forEach(s => s.y += 2);
    stars = stars.filter(s => s.y < H);

    // bullets vs enemies
    for(const b of bullets){
      for(const e of enemies){
        if(!e.alive) continue;
        if(b.x < e.x + e.w && b.x + b.w > e.x &&
           b.y < e.y + e.h && b.y + b.h > e.y){
          e.alive = false;
          b.y = -999;
          score += 10;
          sndAlienHit();
        }
      }
    }

    // bullets vs falling stars
    for(const b of bullets){
      for(const s of stars){
        if(s.taken) continue;
        if(b.x < s.x + s.w && b.x + b.w > s.x &&
           b.y < s.y + s.h && b.y + b.h > s.y){
          s.taken = true;
          b.y = -999;
          starCount++;
          score += 5;
          sndStar();
        }
      }
    }
    stars = stars.filter(s => !s.taken);

    // enemy bullets vs player
    for(const b of enemyBullets){
      if(b.x < player.x + player.w && b.x + b.w > player.x &&
         b.y < player.y + player.h && b.y + b.h > player.y){
        b.y = H + 999;
        lives--;
        sndPlayerBoom();
        if(lives <= 0){
          state = 'gameover';
        }
      }
    }

    // enemies reached player line
    if(alive.some(e => e.y + e.h >= player.y - 4)){
      lives = 0;
      state = 'gameover';
      sndPlayerBoom();
    }
  }

  // ---------- DRAW ----------
  function drawShip(x, y, w, h){
    ctx.fillStyle = '#4fc3f7';
    ctx.fillRect(x, y+6, w, h-6);
    ctx.fillStyle = '#81d4fa';
    ctx.fillRect(x + w/2 - 5, y, 10, 8);
    ctx.fillStyle = '#1976d2';
    ctx.fillRect(x+4, y+h-4, 6, 4);
    ctx.fillRect(x+w-10, y+h-4, 6, 4);
  }
  function drawAlien(e){
    const palette = ['#b388ff','#80d8ff','#ffd54f','#ff8a80'];
    ctx.fillStyle = palette[e.kind % palette.length];
    ctx.fillRect(e.x, e.y+4, e.w, e.h-8);
    ctx.fillRect(e.x+4, e.y, e.w-8, 6);
    ctx.fillRect(e.x+2, e.y+e.h-4, 6, 4);
    ctx.fillRect(e.x+e.w-8, e.y+e.h-4, 6, 4);
    ctx.fillStyle = '#111';
    ctx.fillRect(e.x+8, e.y+10, 6, 6);
    ctx.fillRect(e.x+e.w-14, e.y+10, 6, 6);
  }

  function drawOverlay(){
    // polopruhledne pozadi
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    ctx.fillRect(0, H/2 - 110, W, 220);

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    if(state === 'gameover'){
      // puls efekt
      const pulse = 1 + Math.sin(gameOverAnim * 0.15) * 0.06;
      ctx.save();
      ctx.translate(W/2, H/2 - 40);
      ctx.scale(pulse, pulse);
      ctx.fillStyle = '#ff5252';
      ctx.font = 'bold 48px sans-serif';
      ctx.fillText('💀 KONEC HRY', 0, 0);
      ctx.restore();

      ctx.fillStyle = '#fff';
      ctx.font = 'bold 24px sans-serif';
      ctx.fillText('Nemáš životy.', W/2, H/2 + 10);

      ctx.fillStyle = '#ffd54f';
      ctx.font = 'bold 20px sans-serif';
      ctx.fillText('KLIKNI SEM pro návrat na výběr her', W/2, H/2 + 50);

      ctx.fillStyle = '#bbb';
      ctx.font = '16px sans-serif';
      ctx.fillText('(nebo stiskni Enter pro novou hru)', W/2, H/2 + 80);
    } else if(state === 'won'){
      ctx.fillStyle = '#81c784';
      ctx.font = 'bold 48px sans-serif';
      ctx.fillText('🎉 VYHRÁLS!', W/2, H/2 - 40);

      ctx.fillStyle = '#fff';
      ctx.font = 'bold 22px sans-serif';
      ctx.fillText('Skóre: ' + score + '   ⭐ ' + starCount, W/2, H/2 + 5);

      ctx.fillStyle = '#ffd54f';
      ctx.font = 'bold 20px sans-serif';
      ctx.fillText('KLIKNI SEM pro návrat na výběr her', W/2, H/2 + 45);

      ctx.fillStyle = '#bbb';
      ctx.font = '16px sans-serif';
      ctx.fillText('(nebo stiskni Enter pro novou hru)', W/2, H/2 + 75);
    }

    ctx.textAlign = 'start';
    ctx.textBaseline = 'alphabetic';
  }

  function draw(){
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, H);

    // hvezdy v pozadi
    for(let i=0;i<60;i++){
      const sx = (i*97 + tick*0.35) % W;
      const sy = (i*53 + tick*0.5) % H;
      ctx.fillStyle = (i % 7 === 0) ? '#88f' : '#334';
      ctx.fillRect(sx, sy, 2, 2);
    }

    drawShip(player.x, player.y, player.w, player.h);

    ctx.fillStyle = '#fff200';
    bullets.forEach(b => ctx.fillRect(b.x, b.y, b.w, b.h));

    ctx.fillStyle = '#ff5252';
    enemyBullets.forEach(b => ctx.fillRect(b.x, b.y, b.w, b.h));

    enemies.forEach(e => { if(e.alive) drawAlien(e); });

    ctx.font = '22px sans-serif';
    ctx.textBaseline = 'top';
    stars.forEach(s => ctx.fillText('⭐', s.x, s.y));

    // HUD
    scoreEl.textContent = 'Skóre: ' + score;
    livesEl.textContent = lives > 0 ? '❤️'.repeat(lives) : '💀';
    starsEl.textContent = '⭐ ' + starCount;

    if(state === 'gameover' || state === 'won'){
      drawOverlay();
    }
  }

  function loop(){
    update();
    draw();
    requestAnimationFrame(loop);
  }

  resetGame();
  loop();

  setTimeout(()=>{ try { canvas.focus(); } catch(e){} }, 200);
})();
</script>
"""


def render_hru():
    hra = st.session_state.get("space_invaders")
    if not hra:
        return

    st.subheader("👾 Space Invaders")
    st.caption(
        "1) Klikni do hry (zapne zvuk). 2) Šipky ← → = pohyb, Mezerník = střelba. "
        "Máš 3 životy. Po ztrátě klikni do hry pro návrat zpět."
    )

    components.html(_html_hry(), height=640, scrolling=False)

    st.markdown(
        """
        <style>
        button[kind="secondary"][data-testid^="baseButton"][key="si_back"] {
            background: linear-gradient(90deg, #ff5252 0%, #ff9800 100%) !important;
            color: white !important;
            font-weight: 800 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.button("⬅️ Zpět na výběr her", key="si_back", use_container_width=True):
        st.session_state.space_invaders = None
        st.rerun()
