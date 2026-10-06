import re
import html
from pathlib import Path
from datetime import datetime

import streamlit as st
import ollama

from modules.story_generator import generate_story
from modules.character_generator import generate_characters
from modules.scene_generator import generate_scenes

st.set_page_config(page_title="StoryWeave | StoryWeave", page_icon="🌸", layout="wide", initial_sidebar_state="expanded")

MODEL_NAME = "qwen2.5:3b"
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated" / "stories"
OUT.mkdir(parents=True, exist_ok=True)

DEFAULTS = {
    "page": "Create a Story", "story": "", "characters": "", "scenes": "",
    "story_title": "Untitled Story", "story_idea": "", "genre": "Fantasy",
    "character_count": 3, "gender": "Any", "tone": "Emotional",
    "story_length": "Medium", "scene_count": 6, "saved_stories": [],
    "enhanced_story": "", "last_error": ""
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,500;0,600;1,500;1,600&display=swap');
:root{--ink:#382b3d;--muted:#776979;--pink:#b44786;--border:#eaddea}
html,body,[class*="css"]{font-family:"DM Sans",sans-serif}
.stApp{background:radial-gradient(circle at 8% 12%,rgba(235,183,218,.22) 0 2px,transparent 3px),radial-gradient(circle at 88% 18%,rgba(207,190,239,.22) 0 2px,transparent 3px),linear-gradient(135deg,#fffafd,#f8f5fd);color:var(--ink)}
.block-container{max-width:1400px;padding-top:3rem;padding-bottom:4rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#fff8fc,#f6f0fb);border-right:1px solid var(--border)}
.sw-top{position:fixed;top:0;left:0;right:0;z-index:999;height:52px;padding:9px 28px;background:rgba(255,250,253,.9);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);pointer-events:none;font:italic 600 22px "Playfair Display",Georgia,serif;color:#8d3f78}
.sw-brand{text-align:center;padding:5px 0 18px}.sw-brand-title,.hero-title{font:italic 600 29px "Playfair Display",Georgia,serif;color:#8d3f78}.sw-brand-sub{font-size:12px;color:#7c6a7d}
.hero,.card,.recipe,.character,.scene,.status,.empty{background:rgba(255,255,255,.88);border:1px solid var(--border);border-radius:22px;box-shadow:0 10px 28px rgba(92,55,91,.055)}
.hero{padding:28px 30px;margin-bottom:22px;background:linear-gradient(135deg,rgba(255,255,255,.96),rgba(248,240,250,.85))}.kicker{color:var(--pink);font-weight:700;font-size:13px;letter-spacing:.08em;text-transform:uppercase}.hero-title{font-size:38px;color:#3f3043;margin:4px 0 7px}.hero-text{color:var(--muted);max-width:800px;line-height:1.65}.section-title{font:italic 600 23px "Playfair Display",Georgia,serif;color:#713f69;margin:12px 0}
.recipe{padding:20px 22px;margin:10px 0 20px;background:linear-gradient(135deg,#fff,#fbf1f8)}.recipe-title{font:italic 600 22px "Playfair Display",Georgia,serif;color:#7c3f73;margin-bottom:15px}.recipe-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px 52px}.recipe-item{font-size:15px;color:#514454}.recipe-item b{color:#7c3f73}
.character-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.character{padding:18px;min-height:245px;background:linear-gradient(150deg,#fff,#faf4fc)}.avatar{width:48px;height:48px;border-radius:15px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#f8dce9,#e8def8);font-size:24px}.char-name{font:500 20px "Playfair Display",Georgia,serif;color:#573c58;margin-top:10px}.role{color:#ad4a83;font-size:12px;font-weight:700;margin-bottom:10px}.field{font-size:13px;line-height:1.45;color:#625566;margin:7px 0}.field b{color:#75446f}
.film-wrap{overflow-x:auto;padding:5px 2px 15px}.film{display:flex;gap:16px;width:max-content}.scene{width:330px;min-height:390px;padding:18px;background:linear-gradient(160deg,#fff,#faf5fc)}.scene-num{display:inline-block;padding:5px 10px;border-radius:999px;background:#f6e1ef;color:#8d3f78;font-size:11px;font-weight:700}.scene-title{font:500 21px "Playfair Display",Georgia,serif;color:#513950;margin:10px 0 12px}.scene-field{font-size:12.5px;line-height:1.5;color:#625566;margin:8px 0}.scene-field b{color:#75446f}.mood{display:inline-block;padding:5px 9px;border-radius:999px;background:#eee8fa;color:#66518b;font-size:11px;font-weight:700}
.status-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.status{padding:17px}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:#64a46b;box-shadow:0 0 0 5px rgba(100,164,107,.11);margin-right:8px}.status-title{font-weight:700;color:#503a52}.status-value{color:#786978;font-size:13px;margin-top:7px}.card{padding:20px;margin-bottom:16px}.empty{padding:35px;text-align:center;color:#806f80;border-style:dashed}.small{font-size:12px;color:#8a7888}
.stButton>button,.stDownloadButton>button{border-radius:14px;border:1px solid #e4c9dd;background:#fff;color:#653d61;font-weight:600;transition:.2s}.stButton>button:hover,.stDownloadButton>button:hover{border-color:#b44786;color:#9c356f;transform:translateY(-1px);box-shadow:0 7px 20px rgba(180,71,134,.12)}
@media(max-width:900px){.character-grid,.status-grid,.recipe-grid{grid-template-columns:1fr}.hero-title{font-size:30px}}
</style>
<div class="sw-top">🌸 StoryWeave</div>
""")

def esc(x): return html.escape(str(x or "").strip())
def clean(x):
    x = re.sub(r"\*\*(.*?)\*\*", r"\1", str(x or ""))
    x = re.sub(r"__(.*?)__", r"\1", x)
    return re.sub(r"^#{1,6}\s*", "", x, flags=re.M).strip()

def title_of(story):
    for p in [r"(?is)^\s*###\s*Title\s*\n(.*?)(?=\n\s*###|\Z)", r"(?im)^\s*Title\s*:\s*(.+)$"]:
        m = re.search(p, story or "")
        if m:
            t = clean(m.group(1)).splitlines()[0].strip()
            if t: return t
    return "Untitled Story"

def story_body(story):
    m = re.search(r"(?is)###\s*Story\s*(.*?)(?=\n\s*###\s*(?:Scenes|Dialogue|Mood|Camera Direction)\b|\Z)", story or "")
    return m.group(1).strip() if m else (story or "").strip()

def fields(block, labels):
    out, current = {}, None
    for line in str(block).splitlines():
        s = clean(line).strip()
        hit = False
        for label in labels:
            m = re.match(rf"^{re.escape(label)}\s*:\s*(.*)$", s, re.I)
            if m:
                current = label; out[label] = m.group(1).strip(); hit = True; break
        if not hit and current and s:
            out[current] = (out.get(current, "") + " " + s).strip()
    return out

def parse_characters(text):
    ms = list(re.finditer(r"(?im)^\s*(?:###\s*)?Character\s+(\d+)\s*:?\s*$", text or ""))
    result=[]
    for i,m in enumerate(ms):
        block=(text[m.end():(ms[i+1].start() if i+1<len(ms) else len(text))]).strip()
        f=fields(block,["Character Name","Age","Role in Story","Personality","Physical Appearance","Clothing","Goals","Character Traits"])
        n=m.group(1); result.append({"n":n,"name":f.get("Character Name",f"Character {n}"),"age":f.get("Age","—"),"role":f.get("Role in Story","—"),"personality":f.get("Personality","—"),"appearance":f.get("Physical Appearance","—"),"clothing":f.get("Clothing","—"),"goals":f.get("Goals","—"),"traits":f.get("Character Traits","—")})
    return result

def parse_scenes(text):
    ms=list(re.finditer(r"(?im)^\s*(?:###\s*)?Scene\s+(\d+)\s*:?[ \t]*(.*?)\s*$",text or "")); result=[]
    labels=["Scene Title","Scene Description","Characters Present","Location","Dialogue","Mood","Visual Description","Camera Direction"]
    for i,m in enumerate(ms):
        block=text[m.end():(ms[i+1].start() if i+1<len(ms) else len(text))].strip(); f=fields(block,labels)
        num=m.group(1); result.append({"n":num,"title":clean(m.group(2)) or f.get("Scene Title",f"Scene {num}"),"description":f.get("Scene Description","—"),"characters":f.get("Characters Present","—"),"location":f.get("Location","—"),"dialogue":f.get("Dialogue","—"),"mood":f.get("Mood","—"),"visual":f.get("Visual Description","—"),"camera":f.get("Camera Direction","—")})
    return result

def save_file(name,data):
    p=OUT/name; p.write_text(data,encoding="utf-8"); return p

def storyboard_text():
    return "\n".join(["STORYWEAVE VISUAL STORYBOARD","="*60,"",f"TITLE: {st.session_state.story_title}","","STORY","-"*60,story_body(st.session_state.story),"","CHARACTERS","-"*60,st.session_state.characters,"","SCENES","-"*60,st.session_state.scenes])

def save_current():
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    slug=re.sub(r"[^A-Za-z0-9]+","_",st.session_state.story_title).strip("_")[:50] or "story"
    p=save_file(f"{slug}_{stamp}.txt",storyboard_text())
    st.session_state.saved_stories.append({"title":st.session_state.story_title,"path":str(p),"time":datetime.now().strftime("%d %b %Y, %I:%M %p")})

def enhance(text):
    prompt=f'''You are StoryWeave's professional story editor. Improve this story while preserving its original idea, characters, events and intent. Make it coherent, engaging, cinematic, emotionally consistent and grammatically polished. Do not explain your changes. Return only the improved story.\n\nUSER STORY:\n{text}'''
    r=ollama.chat(model=MODEL_NAME,messages=[{"role":"user","content":prompt}]); return r["message"]["content"]

def generate_all():
    st.session_state.last_error=""
    try:
        with st.status("✨ StoryWeave is creating your story...",expanded=True) as s:
            st.write("📝 Writing the story...")
            story=generate_story(st.session_state.story_idea,genre=st.session_state.genre,character_count=st.session_state.character_count,gender=st.session_state.gender,tone=st.session_state.tone,story_length=st.session_state.story_length,scene_count=st.session_state.scene_count)
            st.write("👤 Designing characters...")
            chars=generate_characters(story,character_count=st.session_state.character_count,gender=st.session_state.gender)
            st.write("🎬 Building cinematic scenes...")
            scenes=generate_scenes(story,scene_count=st.session_state.scene_count)
            st.session_state.story=story; st.session_state.characters=chars; st.session_state.scenes=scenes; st.session_state.story_title=title_of(story)
            save_file("story.txt",story_body(story)); save_file("characters.txt",chars); save_file("scenes.txt",scenes); save_file("storyboard.txt",storyboard_text())
            s.update(label="✨ StoryWeave generation complete!",state="complete",expanded=False)
    except Exception as e:
        st.session_state.last_error=str(e)

def show_characters(text):
    cards=parse_characters(text)
    if not cards: st.markdown(text); return
    icons=["🌸","🌙","✨","🪻","📖","🕊️"]; out=['<div class="character-grid">']
    for i,c in enumerate(cards):
        out.append(f'''<div class="character"><div class="avatar">{icons[i%6]}</div><div class="char-name">{esc(c["name"])}</div><div class="role">{esc(c["role"])}</div><div class="field"><b>Age:</b> {esc(c["age"])}</div><div class="field"><b>Personality:</b> {esc(c["personality"])}</div><div class="field"><b>Appearance:</b> {esc(c["appearance"])}</div><div class="field"><b>Clothing:</b> {esc(c["clothing"])}</div><div class="field"><b>Goals:</b> {esc(c["goals"])}</div><div class="field"><b>Traits:</b> {esc(c["traits"])}</div></div>''')
    out.append('</div>'); st.html(''.join(out))

def show_scenes(text):
    scenes=parse_scenes(text)
    if not scenes: st.markdown(text); return
    out=['<div class="film-wrap"><div class="film">']
    for s in scenes:
        out.append(f'''<div class="scene"><span class="scene-num">SCENE {esc(s["n"])}</span><div class="scene-title">{esc(s["title"])}</div><div class="scene-field"><b>📍 Location:</b> {esc(s["location"])}</div><div class="scene-field"><b>👥 Characters:</b> {esc(s["characters"])}</div><div class="scene-field"><b>📝 Description:</b> {esc(s["description"])}</div><div class="scene-field"><b>💬 Dialogue:</b> {esc(s["dialogue"])}</div><div class="scene-field"><b>🎭 Mood:</b> <span class="mood">{esc(s["mood"])}</span></div><div class="scene-field"><b>🖼️ Visual:</b> {esc(s["visual"])}</div><div class="scene-field"><b>📹 Camera:</b> {esc(s["camera"])}</div></div>''')
    out.append('</div></div>'); st.html(''.join(out))

def downloads():
    st.html('<div class="section-title">⬇️ Download Your Work</div>')
    c1,c2,c3=st.columns(3)
    with c1: st.download_button("📖 Download Story",story_body(st.session_state.story),"storyweave_story.txt","text/plain",use_container_width=True)
    with c2: st.download_button("👥 Download Characters",st.session_state.characters,"storyweave_characters.txt","text/plain",use_container_width=True)
    with c3: st.download_button("🎬 Download Storyboard",storyboard_text(),"storyweave_storyboard.txt","text/plain",use_container_width=True)
    if st.button("💾 Save This Story to My Stories",use_container_width=True): save_current(); st.success("Story saved locally in generated/stories.")

def sidebar():
    with st.sidebar:
        st.html('<div class="sw-brand"><div class="sw-brand-title">🌸 StoryWeave</div><div class="sw-brand-sub">AI-powered story & cinematic storyboard studio</div></div>')
        pages=[("✨ Create a Story","Create a Story"),("✍️ Write Your Story","Write Your Story"),("📚 My Stories","My Stories"),("🎬 Storyboard","Storyboard"),("🤖 AI Status","AI Status"),("⚙️ Settings","Settings"),("ℹ️ About","About")]
        for label,page in pages:
            if st.button(label,key="nav_"+page,use_container_width=True): st.session_state.page=page; st.rerun()
        st.divider(); st.html('<div class="small">Local AI • Ollama • qwen2.5:3b<br>No paid API required</div>')

def create_page():
    st.html('<div class="hero"><div class="kicker">AI Story Studio</div><div class="hero-title">✨ Create Your Story</div><div class="hero-text">Start with a single word, unfinished idea, complete concept, or nothing at all. StoryWeave turns it into a cinematic story, characters and storyboard.</div></div>')
    a,b=st.columns([1.5,1],gap="large")
    with a:
        st.html('<div class="section-title">📝 Your Story Idea</div>')
        st.session_state.story_idea=st.text_area("Story idea",st.session_state.story_idea,height=145,placeholder="Example: A girl discovers a mysterious glowing key...\n\nYou can leave this empty.",label_visibility="collapsed")
    with b:
        st.html('<div class="section-title">🎛️ Story Controls</div>')
        genres=["Fantasy","Mystery","Adventure","Romance","Thriller","Science Fiction","Horror","Comedy","Drama","Historical"]
        tones=["Emotional","Inspirational","Funny","Dark","Mysterious","Romantic","Adventurous","Hopeful","Suspenseful"]
        c1,c2=st.columns(2)
        with c1: st.session_state.genre=st.selectbox("Genre",genres,index=genres.index(st.session_state.genre))
        with c2: st.session_state.tone=st.selectbox("Story Tone",tones,index=tones.index(st.session_state.tone))
        c3,c4=st.columns(2)
        with c3: st.session_state.character_count=st.selectbox("Number of Characters",range(1,7),index=st.session_state.character_count-1)
        with c4:
            genders=["Any","Female","Male","Mixed"]; st.session_state.gender=st.selectbox("Character Gender",genders,index=genders.index(st.session_state.gender))
        c5,c6=st.columns(2)
        with c5:
            lengths=["Short","Medium","Long"]; st.session_state.story_length=st.selectbox("Story Length",lengths,index=lengths.index(st.session_state.story_length))
        with c6:
            counts=[3,4,5,6,7,8,10]; st.session_state.scene_count=st.selectbox("Number of Scenes",counts,index=counts.index(st.session_state.scene_count))
    st.html(f'''<div class="recipe"><div class="recipe-title">🎬 Story Recipe</div><div class="recipe-grid"><div class="recipe-item"><b>Genre:</b> {esc(st.session_state.genre)}</div><div class="recipe-item"><b>Tone:</b> {esc(st.session_state.tone)}</div><div class="recipe-item"><b>Characters:</b> {st.session_state.character_count}</div><div class="recipe-item"><b>Scenes:</b> {st.session_state.scene_count}</div><div class="recipe-item"><b>Length:</b> {esc(st.session_state.story_length)}</div><div class="recipe-item"><b>Gender:</b> {esc(st.session_state.gender)}</div></div></div>''')
    if st.session_state.last_error: st.error("Generation failed. Make sure Terminal 2 is running `ollama serve` and qwen2.5:3b is installed.\n\n"+st.session_state.last_error)
    if st.button("✨ Generate Complete Story",type="primary",use_container_width=True): generate_all(); st.rerun()
    if st.session_state.story:
        st.html(f'<div class="section-title">📖 {esc(st.session_state.story_title)}</div>'); st.markdown(story_body(st.session_state.story))
        st.html('<div class="section-title">👥 Characters</div>'); show_characters(st.session_state.characters)
        st.html('<div class="section-title">🎬 Cinematic Storyboard</div>'); show_scenes(st.session_state.scenes); downloads()

def write_page():
    st.html('<div class="hero"><div class="kicker">Creative Workspace</div><div class="hero-title">✍️ Write Your Story</div><div class="hero-text">Write freely, then optionally let your local StoryWeave AI polish it while preserving your original idea.</div></div>')
    draft=st.text_area("Your story",st.session_state.enhanced_story,height=360,placeholder="Start writing your story here...",label_visibility="collapsed")
    enhance_on=st.toggle("✨ Enhance with AI",True,help="Uses local Ollama. No paid API is required.")
    c1,c2=st.columns(2)
    with c1:
        if st.button("✨ Enhance My Story",type="primary",use_container_width=True,disabled=not draft.strip()):
            try:
                with st.spinner("StoryWeave is polishing your story..."): st.session_state.enhanced_story=enhance(draft)
                st.success("Your story has been enhanced."); st.rerun()
            except Exception as e: st.error(f"AI enhancement failed: {e}")
    with c2:
        if st.button("💾 Save Draft",use_container_width=True,disabled=not draft.strip()): save_file("my_story.txt",draft); st.session_state.enhanced_story=draft; st.success("Draft saved to generated/stories/my_story.txt")
    if not enhance_on: st.info("AI enhancement is turned off. You can still write and save your story.")
    final=st.session_state.enhanced_story or draft
    if final.strip(): st.divider(); st.html('<div class="section-title">📖 Preview</div>'); st.markdown(final)

def stories_page():
    st.html('<div class="hero"><div class="kicker">Your Library</div><div class="hero-title">📚 My Stories</div><div class="hero-text">Stories saved during this session are listed here. Generated files are stored in generated/stories.</div></div>')
    if not st.session_state.saved_stories:
        st.html('<div class="empty">📚<br><b>No saved stories yet</b><br>Generate a story and choose “Save This Story to My Stories”.</div>'); return
    for i,item in enumerate(reversed(st.session_state.saved_stories)):
        st.html(f'<div class="card"><div class="section-title">{esc(item["title"])}</div><div class="small">Saved {esc(item["time"])}</div></div>')
        p=Path(item["path"])
        if p.exists(): st.download_button("⬇️ Download",p.read_text(encoding="utf-8"),p.name,"text/plain",key=f"saved_{i}")

def storyboard_page():
    st.html('<div class="hero"><div class="kicker">Visual Direction</div><div class="hero-title">🎬 Storyboard</div><div class="hero-text">Explore your story as a cinematic film-strip. Each scene contains visual direction for future image generation.</div></div>')
    if not st.session_state.scenes: st.html('<div class="empty">🎬 Generate a story first to build your cinematic storyboard.</div>'); return
    st.html(f'<div class="section-title">🎞️ {esc(st.session_state.story_title)}</div>'); show_scenes(st.session_state.scenes)
    if st.session_state.characters: st.html('<div class="section-title">👥 Character Reference</div>'); show_characters(st.session_state.characters)

def status_page():
    st.html('<div class="hero"><div class="kicker">System Monitor</div><div class="hero-title">🤖 AI Status</div><div class="hero-text">StoryWeave uses local Ollama inference so the project can run without paid AI APIs.</div></div>')
    try:
        data=ollama.list(); models=data.get("models",[]) if isinstance(data,dict) else []; names=[str(x.get("name","")) for x in models if isinstance(x,dict)]; connected=True; err=""
    except Exception as e: names=[]; connected=False; err=str(e)
    ready=any(MODEL_NAME in n or n.startswith(MODEL_NAME) for n in names)
    st.html(f'''<div class="status-grid"><div class="status"><div class="status-title"><span class="dot"></span>Ollama</div><div class="status-value">{"Connected" if connected else "Not connected"}</div></div><div class="status"><div class="status-title"><span class="dot"></span>AI Model</div><div class="status-value">{MODEL_NAME} — {"Ready" if ready else "Not detected"}</div></div><div class="status"><div class="status-title"><span class="dot"></span>Generation Mode</div><div class="status-value">Local / no paid API</div></div></div>''')
    if names: st.divider(); st.html('<div class="section-title">📦 Installed Ollama Models</div>'); [st.write("• "+n) for n in names]
    elif not connected: st.warning("Ollama is not reachable. Open Terminal 2 and run `ollama serve`." ); st.code(err)

def settings_page():
    st.html('<div class="hero"><div class="kicker">Studio Preferences</div><div class="hero-title">⚙️ Settings</div><div class="hero-text">Configure the local AI workspace.</div></div>')
    st.text_input("Ollama Model",MODEL_NAME,disabled=True); st.info("StoryWeave uses local Ollama. No paid API is required.")
    if st.button("🧹 Clear Current Workspace",use_container_width=True):
        for k in ["story","characters","scenes","story_title","story_idea","enhanced_story","last_error"]: st.session_state[k]=DEFAULTS[k]
        st.success("Current workspace cleared."); st.rerun()

def about_page():
    st.html('<div class="hero"><div class="kicker">About the Project</div><div class="hero-title">🌸 StoryWeave</div><div class="hero-text">An AI-powered story and visual storyboard generator that turns simple ideas into structured cinematic stories.</div></div><div class="card"><div class="section-title">✨ What StoryWeave Does</div><p>StoryWeave accepts a word, unfinished idea, complete concept, or empty prompt and generates a complete story with characters, scenes, dialogue, moods, visual descriptions and camera directions.</p></div><div class="card"><div class="section-title">🧠 Technology</div><p>Python • Streamlit • Ollama • qwen2.5:3b</p><p class="small">Local AI is used for story, character, scene and enhancement generation. No paid Gemini image API is required.</p></div>')

sidebar()
p=st.session_state.page
if p=="Create a Story": create_page()
elif p=="Write Your Story": write_page()
elif p=="My Stories": stories_page()
elif p=="Storyboard": storyboard_page()
elif p=="AI Status": status_page()
elif p=="Settings": settings_page()
else: about_page()
