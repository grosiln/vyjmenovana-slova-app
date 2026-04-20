import streamlit as st
import streamlit.components.v1 as components


def spustit_hru():
    st.session_state.space_invaders = {
        "aktivni": True,
        "start_potvrzen": False,
        "koncova_obrazovka": False,
        "skore": 0,
        "hvezdy": 0,
        "vyhra": False,
        "ulozeno": False,
        "jmeno_ulozene": "",
    }


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
          style="background:#000; display:block; margin:0 auto; outline: none;
                 border: 2px solid #1a2050; cursor: pointer;"></canvas>
</div>

<script>
(function(){
  const canvas = document.getElementById('si-canvas');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const scoreEl = document.getElementById('si-score');
  const livesEl = document.getElementById('si-lives');
  const starsEl = document.getElementById('si-stars');

  // ---------- AUDIO ----------
  let audioCtx = null;
  function ensureAudio(){
    if(!audioCtx){
      try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); }
      catch(e){ audioCtx = null; }
    }
    if(audioCtx && audioCtx.state === 'suspended'){ audioCtx.resume(); }
  }
  document.addEventListener('mousedown', ensureAudio);
  document.addEventListener('keydown', ensureAudio);
  document.addEventListener('touchstart', ensureAudio);
  try { ensureAudio(); } catch(e){}

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
    for(let i=0;i<len;i++){ d[i] = (Math.random()*2-1) * Math.pow(1 - i/len, 2); }
    const src = audioCtx.createBufferSource(); src.buffer = buf;
    const g = audioCtx.createGain(); g.gain.value = vol;
    src.connect(g); g.connect(audioCtx.destination);
    src.start();
  }
  function sndShoot(){ tone(900, 0.08, 'square', 0.08); tone(1400, 0.05, 'square', 0.05); }
  function sndAlienShoot(){ tone(220, 0.14, 'sawtooth', 0.09); }
  function sndAlienHit(){ noise(0.18, 0.25); tone(520, 0.1, 'triangle', 0.08); }
  function sndPlayerHit(){ tone(140, 0.35, 'sawtooth', 0.22); noise(0.3, 0.3); }
  function sndPlayerBoom(){ noise(0.9, 0.4); tone(90, 0.7, 'sawtooth', 0.22); }
  function sndStar(){ tone(1200, 0.08, 'sine', 0.12); tone(1700, 0.1, 'sine', 0.1); }

  // ---------- STATE ----------
  // 'playing' | 'gameover' | 'won'
  let state = 'playing';
  let player, bullets, enemyBullets, enemies, stars;
  let dir, score, lives, starCount, tick, shootCd;
  let hitFlash = 0;   // cervene bliknuti po zasahu
  let shake = 0;      // otresy obrazovky
  let invul = 0;      // necitelnost na zasahy po obdrzeni zasahu
  let floatTexts = []; // napisy typu -1 HP
  let saveBtnRect = null;
  let navigated = false;

  // ---------- TEMPO (zpomaleno pro deti) ----------
  const PLAYER_SPEED = 4;
  const BULLET_SPEED = 7;
  const ENEMY_BULLET_SPEED = 3.5;
  const ENEMY_DROP = 12;
  const ENEMY_SHOOT_CHANCE = 0.012;
  const STAR_DROP_CHANCE = 0.0035;
  const STAR_SPEED = 1.4;
  const SHOOT_CD = 14;

  function makeEnemies(){
    const arr = [];
    const rows = 4, cols = 8;
    const offsetX = 60, offsetY = 50;
    for(let r=0;r<rows;r++){
      for(let c=0;c<cols;c++){
        arr.push({ x: offsetX + c*64, y: offsetY + r*42, w: 40, h: 26, alive: true, kind: r });
      }
    }
    return arr;
  }

  function initGameData(){
    player = { x: W/2-24, y: H-46, w: 48, h: 22 };
    bullets = [];
    enemyBullets = [];
    stars = [];
    enemies = makeEnemies();
    dir = 1;
    score = 0; lives = 3; starCount = 0;
    tick = 0; shootCd = 0;
    hitFlash = 0; shake = 0; invul = 0;
    floatTexts = [];
    state = 'playing';
    saveBtnRect = null;
    navigated = false;
  }

  // ---------- NAVIGACE ZPET DO STREAMLITU ----------
  function navigateToParent(){
    if(navigated) return;
    navigated = true;
    const won = (state === 'won') ? '&si_won=1' : '';
    const qs = '?si_finished=1&si_score=' + score + '&si_stars=' + starCount + won;
    try { window.top.location.search = qs; return; } catch(e){}
    try { window.parent.location.search = qs; return; } catch(e){}
    try { window.location.search = qs; } catch(e){}
  }

  // ---------- INPUT ----------
  const keys = {};
  canvas.tabIndex = 0;
  canvas.addEventListener('mousedown', (ev)=>{
    canvas.focus(); ensureAudio();
    if((state === 'gameover' || state === 'won') && saveBtnRect){
      const rect = canvas.getBoundingClientRect();
      const mx = (ev.clientX - rect.left) * (W/rect.width);
      const my = (ev.clientY - rect.top) * (H/rect.height);
      if(mx >= saveBtnRect.x && mx <= saveBtnRect.x + saveBtnRect.w &&
         my >= saveBtnRect.y && my <= saveBtnRect.y + saveBtnRect.h){
        navigateToParent();
      }
    }
  });
  canvas.addEventListener('keydown', (e)=>{
    if(['ArrowLeft','ArrowRight','Space','Enter'].includes(e.code)) e.preventDefault();
    keys[e.code] = true;
    if(state === 'playing' && e.code === 'Space' && shootCd<=0){
      bullets.push({ x: player.x + player.w/2 - 2, y: player.y - 2, w: 4, h: 12 });
      shootCd = SHOOT_CD;
      sndShoot();
    }
    // Na konci hry pouze Enter navaha na ulozeni skore - Space by jinak
    // mohl omylem spustit novou hru (napr. kdyz je focus na tlacitku).
    if((state === 'gameover' || state === 'won') && e.code === 'Enter'){
      navigateToParent();
    }
  });
  canvas.addEventListener('keyup', (e)=>{ keys[e.code] = false; });

  // ---------- UPDATE ----------
  function update(){
    tick++;

    // Efekty dobihaji i po konci hry aby byly videt
    if(invul > 0) invul--;
    if(hitFlash > 0) hitFlash--;
    if(shake > 0) shake--;
    floatTexts.forEach(t => { t.y += t.vy; t.ttl--; });
    floatTexts = floatTexts.filter(t => t.ttl > 0);

    if(state !== 'playing') return;

    if(keys['ArrowLeft']) player.x -= PLAYER_SPEED;
    if(keys['ArrowRight']) player.x += PLAYER_SPEED;
    player.x = Math.max(6, Math.min(W - player.w - 6, player.x));

    if(shootCd > 0) shootCd--;

    bullets.forEach(b => b.y -= BULLET_SPEED);
    bullets = bullets.filter(b => b.y + b.h > 0);
    enemyBullets.forEach(b => b.y += ENEMY_BULLET_SPEED);
    enemyBullets = enemyBullets.filter(b => b.y < H);

    const alive = enemies.filter(e => e.alive);
    if(alive.length === 0){ state = 'won'; return; }

    const speedE = 0.35 + (enemies.length - alive.length) * 0.035;
    const minX = Math.min(...alive.map(e => e.x));
    const maxX = Math.max(...alive.map(e => e.x + e.w));
    if(maxX + dir*speedE > W - 6 || minX + dir*speedE < 6){
      dir *= -1;
      enemies.forEach(e => e.y += ENEMY_DROP);
    } else {
      enemies.forEach(e => e.x += dir*speedE);
    }

    if(Math.random() < ENEMY_SHOOT_CHANCE && alive.length){
      const shooter = alive[Math.floor(Math.random()*alive.length)];
      enemyBullets.push({ x: shooter.x + shooter.w/2 - 2, y: shooter.y + shooter.h, w: 4, h: 12 });
      sndAlienShoot();
    }

    if(Math.random() < STAR_DROP_CHANCE){
      stars.push({ x: 20 + Math.random()*(W-60), y: -24, w: 24, h: 24 });
    }
    stars.forEach(s => s.y += STAR_SPEED);
    stars = stars.filter(s => s.y < H);

    for(const b of bullets){
      for(const e of enemies){
        if(!e.alive) continue;
        if(b.x < e.x + e.w && b.x + b.w > e.x &&
           b.y < e.y + e.h && b.y + b.h > e.y){
          e.alive = false; b.y = -999; score += 10; sndAlienHit();
        }
      }
    }

    for(const b of bullets){
      for(const s of stars){
        if(s.taken) continue;
        if(b.x < s.x + s.w && b.x + b.w > s.x &&
           b.y < s.y + s.h && b.y + b.h > s.y){
          s.taken = true; b.y = -999; starCount++; score += 5; sndStar();
        }
      }
    }
    stars = stars.filter(s => !s.taken);

    for(const b of enemyBullets){
      if(invul > 0) break;
      if(b.x < player.x + player.w && b.x + b.w > player.x &&
         b.y < player.y + player.h && b.y + b.h > player.y){
        b.y = H + 999;
        lives--;
        hitFlash = 22;
        shake = 18;
        invul = 90;
        floatTexts.push({ text: '-1 ❤️', x: player.x + player.w/2, y: player.y - 8, vy: -1.6, ttl: 60 });
        if(lives <= 0){
          state = 'gameover';
          sndPlayerBoom();
        } else {
          sndPlayerHit();
        }
        break;
      }
    }

    if(alive.some(e => e.y + e.h >= player.y - 4)){
      lives = 0;
      state = 'gameover';
      hitFlash = 30; shake = 26;
      sndPlayerBoom();
    }
  }

  // ---------- DRAW ----------
  function drawShip(x, y, w, h){
    ctx.fillStyle = '#4fc3f7'; ctx.fillRect(x, y+6, w, h-6);
    ctx.fillStyle = '#81d4fa'; ctx.fillRect(x + w/2 - 5, y, 10, 8);
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
  function drawStarfield(){
    for(let i=0;i<60;i++){
      const sx = (i*97 + tick*0.35) % W;
      const sy = (i*53 + tick*0.5) % H;
      ctx.fillStyle = (i % 7 === 0) ? '#88f' : '#334';
      ctx.fillRect(sx, sy, 2, 2);
    }
  }
  function roundRect(x, y, w, h, r){
    ctx.beginPath();
    ctx.moveTo(x+r, y);
    ctx.lineTo(x+w-r, y); ctx.quadraticCurveTo(x+w, y, x+w, y+r);
    ctx.lineTo(x+w, y+h-r); ctx.quadraticCurveTo(x+w, y+h, x+w-r, y+h);
    ctx.lineTo(x+r, y+h); ctx.quadraticCurveTo(x, y+h, x, y+h-r);
    ctx.lineTo(x, y+r); ctx.quadraticCurveTo(x, y, x+r, y);
    ctx.closePath();
  }

  function drawSaveButton(cardX, cardY, cardW, cardH, colorBg, colorBgHover){
    const btnW = 320, btnH = 46;
    const btnX = cardX + (cardW - btnW)/2;
    const btnY = cardY + cardH - btnH - 20;
    ctx.fillStyle = colorBg;
    roundRect(btnX, btnY, btnW, btnH, 12); ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2;
    roundRect(btnX, btnY, btnW, btnH, 12); ctx.stroke();
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = 'bold 20px sans-serif';
    ctx.fillText('💾 ULOŽIT SKÓRE / POKRAČOVAT', btnX + btnW/2, btnY + btnH/2 + 1);
    ctx.textAlign = 'start'; ctx.textBaseline = 'alphabetic';
    saveBtnRect = { x: btnX, y: btnY, w: btnW, h: btnH };
  }

  function drawGameoverCard(){
    const cardX = 60, cardY = 110, cardW = W-120, cardH = H-220;
    ctx.fillStyle = '#ffffff';
    roundRect(cardX, cardY, cardW, cardH, 18); ctx.fill();
    ctx.strokeStyle = '#ff5252'; ctx.lineWidth = 4;
    roundRect(cardX, cardY, cardW, cardH, 18); ctx.stroke();

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    ctx.fillStyle = '#b71c1c';
    ctx.font = 'bold 44px sans-serif';
    ctx.fillText('💀 KONEC HRY', W/2, cardY + 58);

    ctx.fillStyle = '#222';
    ctx.font = 'bold 22px sans-serif';
    ctx.fillText('Už nemáš životy.', W/2, cardY + 105);

    ctx.fillStyle = '#2e7d32';
    ctx.font = 'bold 28px sans-serif';
    ctx.fillText('Skóre: ' + score + '    ⭐ ' + starCount, W/2, cardY + 150);

    ctx.fillStyle = '#455';
    ctx.font = '17px sans-serif';
    ctx.fillText('Klikni na tlačítko nebo stiskni Enter.', W/2, cardY + 190);
    ctx.fillText('Pokud se dostaneš do TOP 10, zapíšeš se do žebříčku!', W/2, cardY + 212);

    ctx.textAlign = 'start'; ctx.textBaseline = 'alphabetic';
    drawSaveButton(cardX, cardY, cardW, cardH, '#d32f2f', '#b71c1c');
  }

  function drawWonCard(){
    const cardX = 60, cardY = 110, cardW = W-120, cardH = H-220;
    ctx.fillStyle = '#ffffff';
    roundRect(cardX, cardY, cardW, cardH, 18); ctx.fill();
    ctx.strokeStyle = '#2e7d32'; ctx.lineWidth = 4;
    roundRect(cardX, cardY, cardW, cardH, 18); ctx.stroke();

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    ctx.fillStyle = '#2e7d32';
    ctx.font = 'bold 46px sans-serif';
    ctx.fillText('🎉 VYHRÁLS!', W/2, cardY + 60);

    ctx.fillStyle = '#222';
    ctx.font = 'bold 22px sans-serif';
    ctx.fillText('Všichni mimozemšťané zničeni!', W/2, cardY + 108);

    ctx.fillStyle = '#2e7d32';
    ctx.font = 'bold 28px sans-serif';
    ctx.fillText('Skóre: ' + score + '    ⭐ ' + starCount, W/2, cardY + 150);

    ctx.fillStyle = '#455';
    ctx.font = '17px sans-serif';
    ctx.fillText('Klikni na tlačítko nebo stiskni Enter.', W/2, cardY + 190);
    ctx.fillText('Dostaneš se do žebříčku TOP 10?', W/2, cardY + 212);

    ctx.textAlign = 'start'; ctx.textBaseline = 'alphabetic';
    drawSaveButton(cardX, cardY, cardW, cardH, '#2e7d32', '#1b5e20');
  }

  function drawGame(){
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
    drawStarfield();
    // Hrac: bliky behem invulnerability
    const blik = invul > 0 && (Math.floor(invul/5) % 2 === 0);
    if(!blik) drawShip(player.x, player.y, player.w, player.h);
    ctx.fillStyle = '#fff200';
    bullets.forEach(b => ctx.fillRect(b.x, b.y, b.w, b.h));
    ctx.fillStyle = '#ff5252';
    enemyBullets.forEach(b => ctx.fillRect(b.x, b.y, b.w, b.h));
    enemies.forEach(e => { if(e.alive) drawAlien(e); });
    ctx.font = '22px sans-serif';
    ctx.textBaseline = 'top';
    stars.forEach(s => ctx.fillText('⭐', s.x, s.y));
    ctx.textBaseline = 'alphabetic';
  }

  function drawFloatTexts(){
    ctx.textAlign = 'center';
    floatTexts.forEach(t => {
      const alpha = Math.max(0, Math.min(1, t.ttl/60));
      ctx.fillStyle = 'rgba(255, 82, 82,' + alpha + ')';
      ctx.strokeStyle = 'rgba(255,255,255,' + alpha + ')';
      ctx.lineWidth = 3;
      ctx.font = 'bold 30px sans-serif';
      ctx.strokeText(t.text, t.x, t.y);
      ctx.fillText(t.text, t.x, t.y);
    });
    ctx.textAlign = 'start';
  }

  function draw(){
    // Otresy obrazovky
    ctx.save();
    if(shake > 0){
      const sx = (Math.random()-0.5) * shake;
      const sy = (Math.random()-0.5) * shake;
      ctx.translate(sx, sy);
    }
    drawGame();
    drawFloatTexts();
    ctx.restore();

    // Cervene bliknuti pres celou obrazovku pri zasahu
    if(hitFlash > 0){
      const a = Math.min(0.55, hitFlash/22 * 0.55);
      ctx.fillStyle = 'rgba(255, 30, 30,' + a + ')';
      ctx.fillRect(0, 0, W, H);
      // Tlusty cerveny ramecek pro zvyraznene rozpoznani
      ctx.strokeStyle = 'rgba(255, 30, 30,' + Math.min(1, a*2) + ')';
      ctx.lineWidth = 8;
      ctx.strokeRect(4, 4, W-8, H-8);
    }

    if(state === 'gameover'){
      ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(0, 0, W, H);
      drawGameoverCard();
    } else if(state === 'won'){
      ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(0, 0, W, H);
      drawWonCard();
    }

    scoreEl.textContent = 'Skóre: ' + score;
    livesEl.textContent = lives > 0 ? '❤️'.repeat(lives) : '💀';
    starsEl.textContent = '⭐ ' + starCount;
  }

  function loop(){
    update();
    draw();
    requestAnimationFrame(loop);
  }

  initGameData();
  loop();
  setTimeout(()=>{ try { canvas.focus(); } catch(e){} }, 200);
})();
</script>
"""


def render_hru():
    hra = st.session_state.get("space_invaders")
    if not hra:
        return

    if hra.get("koncova_obrazovka"):
        _render_koncovou_obrazovku(hra)
        return

    if not hra.get("start_potvrzen"):
        _render_uvitaci_okno()
        return

    st.subheader("👾 Space Invaders")
    components.html(_html_hry(), height=640, scrolling=False)

    st.caption("🔚 Na konci hry tvé skóre automaticky uložíme a ukážeme, zda ses dostal do TOP 10 žebříčku.")

    if st.button("⬅️ Zpět na výběr her", key="si_back", use_container_width=True):
        st.session_state.space_invaders = None
        st.rerun()


def _render_uvitaci_okno():
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #1a237e 0%, #283593 55%, #5e35b1 100%);
            color: #fff;
            padding: 2rem 2rem 1.6rem 2rem;
            border-radius: 22px;
            box-shadow: 0 12px 28px rgba(0,0,0,0.25);
            text-align: center;
            max-width: 720px;
            margin: 0.5rem auto 1.2rem auto;
            border: 3px solid #ffd54f;
        ">
            <div style="font-size: 3.4rem; line-height: 1;">👾</div>
            <h2 style="color: #fff !important; margin: 0.6rem 0 0.4rem 0; font-size: 2.2rem;">
                Space Invaders
            </h2>
            <p style="color: #ffd54f; font-weight: 700; font-size: 1.15rem; margin: 0 0 1.1rem 0;">
                Jak se hraje
            </p>
            <div style="
                background: rgba(255,255,255,0.08);
                border-radius: 14px;
                padding: 0.9rem 1.2rem;
                text-align: left;
                max-width: 480px;
                margin: 0 auto 1.2rem auto;
                font-size: 1.08rem;
                line-height: 1.7;
            ">
                ⬅ ➡ &nbsp;&nbsp;Šipky = pohyb raketky<br>
                ␣ &nbsp;&nbsp;Mezerník = střelba<br>
                ❤️ ❤️ ❤️ &nbsp;&nbsp;Máš 3 životy<br>
                ⭐ &nbsp;&nbsp;Sestřel padající hvězdičky pro bonus<br>
                👾 &nbsp;&nbsp;Znič všechny mimozemšťany<br>
                🏆 &nbsp;&nbsp;TOP 10 skóre uvidíš v žebříčku
            </div>
            <p style="color: #fff; font-weight: 600; margin: 0 0 0.2rem 0;">
                🔊 Kliknutím na tlačítko dole se zapne zvuk a hra začne.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button(
            "▶ START HRY (zapne zvuk)",
            key="si_start_btn",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.space_invaders["start_potvrzen"] = True
            st.rerun()
        if st.button(
            "⬅️ Zpět na výběr her",
            key="si_start_cancel",
            use_container_width=True,
        ):
            st.session_state.space_invaders = None
            st.rerun()


def _render_koncovou_obrazovku(hra):
    # Lokalni import aby nevznikal circular
    from app import (
        patri_do_zebricku,
        zapis_do_zebricku,
        MAX_JMENO_ZEBRICEK,
        LIMIT_ZEBRICKU,
        nastav_sekci,
    )

    skore = int(hra.get("skore", 0))
    hvezdy = int(hra.get("hvezdy", 0))
    vyhra = bool(hra.get("vyhra", False))
    ulozeno = bool(hra.get("ulozeno", False))
    jmeno_ulozene = hra.get("jmeno_ulozene", "")

    nadpis = "🎉 VYHRÁLS!" if vyhra else "💀 Konec hry"
    barva = "#2e7d32" if vyhra else "#c62828"
    popis = "Všichni mimozemšťané zničeni!" if vyhra else "Došly ti životy."

    st.markdown(
        f"""
        <div style="
            background: white;
            border: 3px solid {barva};
            border-radius: 22px;
            padding: 1.4rem 1.6rem 1.2rem 1.6rem;
            text-align: center;
            box-shadow: 0 10px 26px rgba(0,0,0,0.12);
            margin: 0.4rem auto 1rem auto;
            max-width: 720px;
        ">
            <div style="color:{barva}; font-weight:900; font-size:2.1rem; line-height:1.2;">{nadpis}</div>
            <div style="color:#333; font-size:1.1rem; margin-top: 0.3rem;">{popis}</div>
            <div style="
                margin-top: 0.9rem;
                font-size: 1.6rem;
                font-weight: 900;
                color: #1f2640;
            ">
                Skóre: <span style="color:#2e7d32;">{skore}</span>
                &nbsp;&nbsp;
                ⭐ <span style="color:#8a6d00;">{hvezdy}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    patri = patri_do_zebricku(skore, "space")

    if ulozeno:
        st.success(
            f"✅ Uloženo do žebříčku jako **{jmeno_ulozene}** – skóre {skore} b."
        )
    elif patri:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg,#fff8cc 0%,#ffe69a 100%);
                border: 2px solid #e8b800;
                border-radius: 16px;
                padding: 0.9rem 1.1rem;
                text-align:center;
                font-size: 1.15rem;
                font-weight: 700;
                color: #5b4600;
                margin: 0.3rem auto 0.8rem auto;
                max-width: 720px;
            ">
                🏆 Tvé skóre se dostalo do TOP {LIMIT_ZEBRICKU}! Zapiš si své jméno.
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("si_save_form", clear_on_submit=False):
            jmeno = st.text_input(
                f"Tvé jméno (max {MAX_JMENO_ZEBRICEK} znaků)",
                max_chars=MAX_JMENO_ZEBRICEK,
                key="si_jmeno_input",
                placeholder="např. Tomík",
            )
            c1, c2 = st.columns(2)
            with c1:
                ulozit = st.form_submit_button(
                    "💾 Uložit do žebříčku",
                    use_container_width=True,
                    type="primary",
                )
            with c2:
                preskocit = st.form_submit_button(
                    "Přeskočit",
                    use_container_width=True,
                )
            if ulozit:
                jm = zapis_do_zebricku(jmeno, skore, hvezdy, "space")
                hra["ulozeno"] = True
                hra["jmeno_ulozene"] = jm
                st.session_state.space_invaders = hra
                st.rerun()
            if preskocit:
                st.session_state.space_invaders = None
                st.rerun()
    else:
        st.info("Tvé skóre se bohužel nevešlo do TOP 10. Zkus to znovu!")

    st.markdown("---")
    st.caption(
        "👉 Novou hru spustíš přes levé menu (Minihry). "
        "Tím předejdeš nechtěnému startu hry mezerníkem."
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏆 Zobrazit žebříček", key="si_end_zebricek", use_container_width=True):
            st.session_state.space_invaders = None
            nastav_sekci("Žebříček miniher")
            st.rerun()
    with c2:
        if st.button("⬅️ Zpět na výběr her", key="si_end_back", use_container_width=True):
            st.session_state.space_invaders = None
            st.rerun()
