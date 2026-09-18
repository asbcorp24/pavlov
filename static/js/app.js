function toggleFullscreen(){
  if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
  else document.exitFullscreen?.();
}
let lastTouch=Date.now();
["pointerdown","touchstart","keydown","mousemove"].forEach(e=>document.addEventListener(e,()=>lastTouch=Date.now(),{passive:true}));
setInterval(()=>{
  const isAdmin=location.pathname.startsWith("/admin");
  if(!isAdmin && location.pathname!=="/" && Date.now()-lastTouch>180000) location.href="/";
},15000);
document.querySelectorAll("audio").forEach(player=>{
  player.addEventListener("play",()=>{
    document.querySelectorAll("audio").forEach(other=>{ if(other!==player) other.pause(); });
  });
});

const saver=document.getElementById("screensaver");
const wake=document.getElementById("wakeMuseum");
let saverTimer;
function hideSaver(){
  if(!saver) return;
  saver.classList.remove("show");
  saver.setAttribute("aria-hidden","true");
  clearTimeout(saverTimer);
  if(!location.pathname.startsWith("/admin")){
    saverTimer=setTimeout(()=>{saver.classList.add("show");saver.setAttribute("aria-hidden","false");},60000);
  }
}
["pointerdown","touchstart","keydown","mousemove"].forEach(e=>document.addEventListener(e,hideSaver,{passive:true}));
wake?.addEventListener("click",hideSaver);
hideSaver();

const lb=document.getElementById("lightbox"), lbImg=document.getElementById("lightboxImage");
document.querySelectorAll(".gallery-thumb").forEach(btn=>btn.addEventListener("click",()=>{
  if(!lb||!lbImg)return;
  lbImg.src=btn.dataset.full;
  lb.hidden=false;
  document.body.classList.add("no-scroll");
}));
document.querySelector(".lightbox-close")?.addEventListener("click",()=>{
  if(lb)lb.hidden=true;
  document.body.classList.remove("no-scroll");
});
lb?.addEventListener("click",e=>{
  if(e.target===lb){lb.hidden=true;document.body.classList.remove("no-scroll");}
});

/* Full-screen museum music player */
const museumPlayer=document.getElementById("museumPlayer");
if(museumPlayer){
  const audio=museumPlayer.querySelector("audio");
  const play=museumPlayer.querySelector("[data-player-play]");
  const title=museumPlayer.querySelector("[data-player-title]");
  const subtitle=museumPlayer.querySelector("[data-player-subtitle]");
  const cover=museumPlayer.querySelector("[data-player-cover]");
  const progress=museumPlayer.querySelector("[data-player-progress]");
  const time=museumPlayer.querySelector("[data-player-time]");
  const tracks=[...document.querySelectorAll("[data-track]")];
  let active=null;
  const fmt=s=>{if(!Number.isFinite(s))return "0:00";const m=Math.floor(s/60),ss=Math.floor(s%60).toString().padStart(2,"0");return m+":"+ss;};
  function setTrack(el,autoplay=true){
    active=el;
    tracks.forEach(t=>t.classList.toggle("active",t===el));
    const src=el.dataset.audio||"";
    title.textContent=el.dataset.title||"";
    subtitle.textContent=el.dataset.subtitle||"";
    cover.src=el.dataset.image||cover.src;
    if(src){audio.src=src;play.disabled=false;if(autoplay)audio.play().catch(()=>{});}
    else{audio.removeAttribute("src");audio.load();play.disabled=true;}
  }
  tracks.forEach(el=>el.addEventListener("click",()=>setTrack(el,true)));
  play?.addEventListener("click",()=>{if(audio.paused)audio.play();else audio.pause();});
  audio.addEventListener("play",()=>play.textContent="Ⅱ");
  audio.addEventListener("pause",()=>play.textContent="▶");
  audio.addEventListener("timeupdate",()=>{
    const ratio=audio.duration?audio.currentTime/audio.duration:0;
    progress.value=ratio*100;
    time.textContent=fmt(audio.currentTime)+" / "+fmt(audio.duration);
  });
  progress?.addEventListener("input",()=>{if(audio.duration)audio.currentTime=(progress.value/100)*audio.duration;});
  if(tracks.length)setTrack(tracks.find(t=>t.dataset.audio)||tracks[0],false);
}
