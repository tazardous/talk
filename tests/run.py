"""Tests for Talk Time Cards: card content, setup screen, full games for 2-6 players in both modes,
topic drawing, swap / dig deeper, stars, persistence, XSS escaping, and layout fit on phone / tablet / desktop."""
import sys
from playwright.sync_api import sync_playwright
CH = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
URL = 'file://' + __file__.rsplit('/tests/', 1)[0] + '/index.html'
fails = []
def chk(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails.append(m)

CONTENT = """(()=>{const T=__TK.T, bad=[], seen=new Map(); let n=0;
 for(const d of __TK.DECKS.map(x=>x.id)) for(const c of __TK.CATS.map(x=>x.id)){
  const a=(T[d]||{})[c]; if(!a||a.length<14){bad.push(['too few',d,c,a&&a.length]);continue;}
  for(const s of a){ n++; const parts=s.split(' | ');
    if(parts.length!==2){bad.push(['format',s]);continue;}
    const [p,f]=parts;
    if(!/[?.!]$/.test(p)||!/[?.!]$/.test(f)) bad.push(['punct',s]);
    if(p.length>110||f.length>80) bad.push(['long',s]);
    if(p.length<12||f.length<8) bad.push(['short',s]);
    if(seen.has(p)) bad.push(['dup',p,seen.get(p),d+c]); seen.set(p,d+c);
  }}
 return {n,bad};})()"""

def overflow_check(page, label):
    r = page.evaluate("""()=>{const W=document.documentElement.clientWidth,H=document.documentElement.clientHeight,out=[];
      const scr=document.querySelector('.screen.on'); if(!scr) return ['no screen'];
      if(document.documentElement.scrollWidth>W+1) out.push('page scrollWidth '+document.documentElement.scrollWidth+'>'+W);
      scr.querySelectorAll('button,input,.pl,.card,.back,.pill,.act').forEach(el=>{
        const b=el.getBoundingClientRect(); if(b.width===0) return;
        if(b.right>W+1||b.left<-1) out.push('x-overflow '+(el.className||el.tagName)+' '+Math.round(b.left)+'..'+Math.round(b.right));
      });
      const foot=document.querySelector('#foot'); if(scr.id==='game'&&foot){const b=foot.getBoundingClientRect(); if(b.bottom>H+1) out.push('footer below fold '+Math.round(b.bottom)+'>'+H);
        foot.querySelectorAll('button').forEach(el=>{const q=el.getBoundingClientRect(); if(q.bottom>H+1||q.top<0) out.push('foot button off-screen '+el.textContent.trim());});}
      return out;}""")
    chk(not r, f'layout {label}: {r}')

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CH, args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': 390, 'height': 780})
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text else None)
    pg.goto(URL); pg.wait_for_function('window.__TK')

    # ---- content ----
    r = pg.evaluate(CONTENT)
    chk(not r['bad'], f"content: {r['n']} cards, problems={r['bad'][:5]}")
    chk(r['n'] >= 140, f"at least 140 cards ({r['n']})")

    # ---- setup screen ----
    chk(pg.locator('#plist .prow').count() == 3, 'default 3 player rows')
    for n in (2, 4, 5, 6):
        pg.click(f'#optPlayers button[data-n="{n}"]')
        chk(pg.locator('#plist .prow').count() == n, f'{n} player rows')
    pg.click('#optPlayers button[data-n="2"]')
    chk(pg.locator('#optPlayers button').count() == 5, 'counts 2..6 offered')
    pg.click('#optPlayers button[data-n="6"]')
    avs = pg.evaluate("__TK.save.avs.slice(0,6)")
    chk(len(set(avs)) == 6, f'6 distinct avatars {avs}')
    for _ in range(14): pg.click('#plist .prow:nth-child(1) .av')
    avs = pg.evaluate("__TK.save.avs.slice(0,6)")
    chk(len(set(avs)) == 6, f'avatars stay distinct after cycling {avs}')
    # names + XSS
    pg.fill('#plist .prow:nth-child(1) input', '<img src=x onerror=window.__x=1>')
    pg.fill('#plist .prow:nth-child(2) input', 'Diana')
    pg.fill('#plist .prow:nth-child(3) input', 'Kellan')
    chk(pg.evaluate("__TK.save.names[0].length")<=14, 'name capped at 14')
    # deck/topic guards
    pg.click('#optDecks .chip[data-id="little"]')
    chk(pg.evaluate("__TK.save.decks.length")==1, 'cannot deselect last deck')
    pg.click('#optDecks .chip[data-id="big"]'); pg.click('#optDecks .chip[data-id="little"]')
    chk(pg.evaluate("__TK.save.decks.join()")=='big', 'switch to big deck only')
    pg.click('#optDecks .chip[data-id="little"]')
    chk(pg.evaluate("__TK.save.decks.join()")=='little,big', 'both decks selected (ordered)')
    for c in ('school', 'home', 'feelings', 'future'): pg.click(f'#optCats .chip[data-id="{c}"]')
    pg.click('#optCats .chip[data-id="fun"]')
    chk(pg.evaluate("__TK.save.cats.join()")=='fun', 'cannot deselect last topic')
    for c in ('school', 'home', 'feelings', 'future'): pg.click(f'#optCats .chip[data-id="{c}"]')
    # persistence
    pg.click('.tg[data-k="stars"]'); pg.click('.tg[data-k="everyone"]')
    pg.reload(); pg.wait_for_function('window.__TK')
    s = pg.evaluate("__TK.save")
    chk(s['players'] == 6 and s['names'][1] == 'Diana' and s['stars'] and s['everyone'] and s['decks'] == ['little', 'big'], 'setup restored after reload')
    chk(pg.evaluate("window.__x")is None, 'XSS name not executed')
    pg.evaluate("localStorage.setItem('talk.v1','{bad json')"); pg.reload(); pg.wait_for_function('window.__TK')
    chk(pg.evaluate("__TK.save.players")>=2, 'survives corrupt storage')
    pg.evaluate("localStorage.setItem('talk.v1',JSON.stringify({players:99,avs:[1,1,1,1,1,1],decks:['x'],cats:[],names:[1,2]}))"); pg.reload(); pg.wait_for_function('window.__TK')
    s = pg.evaluate("__TK.save")
    chk(s['players'] == 6 and len(set(s['avs'])) == 6 and s['decks'] == ['little'] and len(s['cats']) == 5, f'sanitizes bad storage {s["players"]},{s["decks"]}')
    overflow_check(pg, 'setup 390x780')

    # ---- full games ----
    PLAY = """async(args)=>{const [mode,count]=args; const sleep=ms=>new Promise(r=>setTimeout(r,ms)); const log={turns:[],ids:[],errors:[]};
      const G=()=>__TK.G; let guard=0;
      for(let k=0;k<count&&guard++<5000;){
        if(G().phase==='pick'){
          const cat=['', 'school','home','feelings','future','fun'][k%6]; const prev=G().bag.length;
          const who=document.querySelector('.pl.cur .n').textContent;
          const btn=cat?document.querySelector('.pill[data-cat="'+cat+'"]'):document.querySelector('.pill.any');
          if(!btn){log.errors.push('missing pill '+cat);break;}
          btn.click(); await sleep(5);
          if(G().phase!=='card'){log.errors.push('no card drawn');break;}
          if(cat&&G().card.c!==cat) log.errors.push('wrong cat '+cat+' got '+G().card.c);
          log.turns.push(who); log.ids.push(G().card.id);
          if(!document.querySelector('.card .q').textContent.length) log.errors.push('empty card');
          if(k%5===2){document.querySelector('[data-act=deeper]').click(); if(!document.querySelector('.deep')) log.errors.push('no follow-up shown'); }
          if(k%7===3){const before=G().card.id; document.querySelector('[data-act=swap]').click(); if(G().card.id===before) log.errors.push('swap kept same card'); log.ids[log.ids.length-1]=G().card.id;}
          if(document.querySelector('.bonus button')&&k%2===0) document.querySelector('.bonus button').click();
          k++;
        } else {
          document.querySelector('[data-act=next]').click(); await sleep(2);
        }
      }
      return log;}"""
    for n in (2, 3, 4, 5, 6):
        for every in (False, True):
            for stars in (False, True):
                pg.evaluate(f"""localStorage.setItem('talk.v1',JSON.stringify({{players:{n},decks:['little','big'],cats:['school','home','feelings','future','fun'],everyone:{str(every).lower()},stars:{str(stars).lower()},voice:false,sound:false,names:['A','B','C','D','E','F'],avs:[0,1,2,3,4,5]}}))""")
                pg.reload(); pg.wait_for_function('window.__TK')
                pg.click('#start')
                log = pg.evaluate(PLAY, ['x', 30])
                # speaker/turn rotation: each new card is started by the next player in order
                exp = [['A', 'B', 'C', 'D', 'E', 'F'][i % n] for i in range(30)]
                ok_rot = log['turns'] == exp
                chk(not log['errors'] and ok_rot and len(log['ids']) == 30, f"game n={n} everyone={every} stars={stars}: 30 cards, rotation ok, errors={log['errors'][:2]}")
                # no repeats within first bag
                bag_total = pg.evaluate("__TK.G.played+__TK.G.bag.length+(__TK.G.card?1:0)+__TK.G.discard.length-__TK.G.played") if False else None
                chk(len(set(log['ids'])) == 30, f'  no repeated cards in 30 draws (n={n})')
                if stars:
                    tot = pg.evaluate("__TK.G.players.reduce((a,p)=>a+p.stars,0)")
                    chk(tot > 0, f'  stars awarded ({tot})')
                else:
                    chk(pg.evaluate("document.querySelector('.pl .s').textContent")=='', '  no star text when stars off')

    # ---- everyone mode semantics ----
    pg.evaluate("""localStorage.setItem('talk.v1',JSON.stringify({players:4,decks:['little'],cats:['fun','home'],everyone:true,stars:true,voice:false,sound:false,names:['A','B','C','D'],avs:[0,1,2,3]}))""")
    pg.reload(); pg.wait_for_function('window.__TK'); pg.click('#start')
    chk(pg.locator('.pill').count() == 3, 'pills show only enabled topics + surprise')
    pg.click('.pill.any')
    seq = []
    for i in range(4):
        seq.append(pg.inner_text('.pl.cur .n'))
        btn = pg.inner_text('.act.go')
        pg.click('.act.go')
    chk(seq == ['A', 'B', 'C', 'D'], f'everyone mode goes around the table {seq}')
    chk('Done' in btn, 'last speaker sees Done button')
    chk(pg.inner_text('.pl.cur .n') == 'B' and pg.evaluate("__TK.G.phase") == 'pick', 'next card starts with the next player')
    chk(pg.evaluate("__TK.G.players.map(p=>p.stars).join()") == '1,1,1,1', 'each speaker got a star')
    # bonus star: once per player per card
    pg.click('.pill.any')
    nb = pg.locator('.bonus button').count()
    pg.click('.bonus button >> nth=0')
    chk(pg.locator('.bonus button').count() == nb - 1, 'bonus star is one per player per card')
    # voice: prompt spoken
    pg.evaluate("window.__sp=[];window.SpeechSynthesisUtterance=function(t){this.text=t};speechSynthesis.speak=u=>__sp.push(u.text);0")
    pg.evaluate("__TK.save.voice=true")
    pg.click('.act >> nth=0')   # dig deeper
    chk(pg.evaluate("__sp.length")==1 and pg.evaluate("__sp[0]==__TK.G.card.f"), 'follow-up spoken on dig deeper')
    # end screen
    pg.click('[data-act=finish]')
    chk(pg.is_visible('#end') and 'card' in pg.inner_text('#endStat'), 'end screen shows summary')
    chk(pg.locator('#endRank .r').count() == 4, 'end screen lists all players')
    pg.click('[data-act=resume]'); chk(pg.is_visible('#game'), 'keep playing returns to game')
    pg.click('[data-act=finish]'); pg.click('[data-act=setup]'); chk(pg.is_visible('#setup'), 'new game returns to setup')

    # ---- deck exhaustion reshuffles without crashing ----
    pg.evaluate("""localStorage.setItem('talk.v1',JSON.stringify({players:2,decks:['little'],cats:['fun'],everyone:false,stars:false,voice:false,sound:false,names:['A','B'],avs:[0,1]}))""")
    pg.reload(); pg.wait_for_function('window.__TK'); pg.click('#start')
    res = pg.evaluate("""()=>{const seen=[];for(let i=0;i<40;i++){document.querySelector('.pill[data-cat=fun]').click(); seen.push(__TK.G.card.id); document.querySelector('[data-act=next]').click();} return {n:new Set(seen).size,r:__TK.G.reshuffles,left:__TK.G.bag.length};}""")
    chk(res['n'] == 14 and res['r'] >= 2, f'deck of 14 reshuffles when empty {res}')

    # ---- layout at several sizes with 6 players and long names ----
    pg.evaluate("""localStorage.setItem('talk.v1',JSON.stringify({players:6,decks:['little','big'],cats:['school','home','feelings','future','fun'],everyone:true,stars:true,voice:false,sound:false,names:['Maximilian12345','Bernadette','Kellan','Diana','Zoe','Bernie'],avs:[0,1,2,3,4,5]}))""")
    for (w, h) in ((360, 640), (390, 780), (844, 390), (768, 1024), (1024, 768), (1440, 900)):
        pg.set_viewport_size({'width': w, 'height': h}); pg.reload(); pg.wait_for_function('window.__TK')
        overflow_check(pg, f'setup {w}x{h}')
        pg.click('#start'); overflow_check(pg, f'game pick {w}x{h}')
        # longest card
        pg.evaluate("""()=>{__TK.G.bag.sort((a,b)=>b.p.length-a.p.length); }""")
        pg.click('.pill.any'); pg.click('[data-act=deeper]'); overflow_check(pg, f'game card+deeper {w}x{h}')
        # main card text must be reachable (stage scrolls if needed)
        ok = pg.evaluate("""()=>{const s=document.querySelector('#stage'); const q=document.querySelector('.card .q'); s.scrollTop=0; const b=q.getBoundingClientRect(),sb=s.getBoundingClientRect();
            return s.scrollHeight<=s.clientHeight+1 || (b.left>=0&&b.right<=innerWidth);}""")
        chk(ok, f'card readable {w}x{h}')

    chk(not errs, f'no page errors: {errs[:3]}')
    br.close()
print('\nFAILS', len(fails))
for f in fails: print(' -', f)
sys.exit(1 if fails else 0)
