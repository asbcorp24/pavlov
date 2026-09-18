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
