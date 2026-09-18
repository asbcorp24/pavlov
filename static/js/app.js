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
