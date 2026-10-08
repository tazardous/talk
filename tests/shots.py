"""Screenshots of the main screens for a quick visual check (saved in tests/shots/, git-ignored)."""
from playwright.sync_api import sync_playwright
CH='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
URL='file://'+__file__.rsplit('/tests/',1)[0]+'/index.html'
SET="""localStorage.setItem('talk.v1',JSON.stringify({players:6,decks:['little'],cats:['school','home','feelings','future','fun'],everyone:true,stars:true,voice:false,sound:false,names:['Kellan','Diana','Gran','Pop','Mom','Bernie'],avs:[0,1,2,3,4,5]}))"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CH,args=['--no-sandbox'])
    for name,(w,h) in {'phone':(390,780),'land':(844,390),'desk':(1280,800)}.items():
        pg=b.new_page(viewport={'width':w,'height':h}); pg.goto(URL); pg.evaluate(SET); pg.reload(); pg.wait_for_function('window.__TK')
        pg.screenshot(path=f'tests/shots/{name}_setup.png')
        pg.click('#start'); pg.wait_for_timeout(300); pg.screenshot(path=f'tests/shots/{name}_pick.png')
        pg.click('.pill[data-cat=feelings]'); pg.click('[data-act=deeper]'); pg.wait_for_timeout(700); pg.screenshot(path=f'tests/shots/{name}_card.png')
        pg.close()
    b.close()
