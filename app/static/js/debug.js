(() => {
  // Minimal UI behaviors: auto-refresh countdown, pause/resume, expand details, copy
  const REFRESH_INTERVAL = 5; // seconds
  let remaining = REFRESH_INTERVAL;
  let paused = false;

  function $(s, el=document){return el.querySelector(s)}
  function $all(s, el=document){return Array.from(el.querySelectorAll(s))}

  function updateCounter(){
    const el = $('#auto-refresh-counter');
    if(!el) return;
    el.textContent = paused ? 'paused' : `Actualizando en: ${remaining}s`;
  }

  function tick(){
    if(paused) return;
    remaining -= 1;
    if(remaining <= 0){ location.reload(); return; }
    updateCounter();
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    // init counter element
    const counter = document.createElement('div');
    counter.id = 'auto-refresh-counter';
    counter.className = 'muted';
    const headerActions = document.querySelector('.header-actions');
    if(headerActions) headerActions.prepend(counter);
    updateCounter();

    // controls
    const pauseBtn = document.createElement('button');
    pauseBtn.className='btn ghost'; pauseBtn.textContent='Pausar';
    headerActions && headerActions.prepend(pauseBtn);
    pauseBtn.addEventListener('click', ()=>{
      paused = !paused; pauseBtn.textContent = paused ? 'Reanudar' : 'Pausar'; updateCounter();
    });

    // countdown interval
    setInterval(()=>{
      if(!paused){ remaining = Math.max(0, remaining-1); if(remaining===0) location.reload(); updateCounter(); }
    },1000);

    // expand detail toggles
    $all('.btn-expand').forEach(btn=>{
      btn.addEventListener('click', (ev)=>{
        const card = ev.currentTarget.closest('.event-card');
        const det = card.querySelector('.detail');
        if(det){ det.style.display = det.style.display === 'block' ? 'none' : 'block'; }
      });
    });

    // copy buttons
    $all('.copy-btn').forEach(b=>{
      b.addEventListener('click', (ev)=>{
        const tgt = ev.currentTarget.dataset.target;
        const el = document.getElementById(tgt);
        if(!el) return;
        navigator.clipboard.writeText(el.textContent).then(()=>{
          ev.currentTarget.textContent='Copiado'; setTimeout(()=>ev.currentTarget.textContent='Copiar',1400);
        });
      });
    });

    // minimal instant client-side search (progressive) — only filters visible cards
    const search = $('.filters .search');
    if(search){
      let timeout;
      search.addEventListener('input', (e)=>{
        clearTimeout(timeout);
        const q = e.target.value.trim().toLowerCase();
        timeout = setTimeout(()=>{
          $all('.event-card').forEach(card=>{
            const title = card.querySelector('.event-title').textContent.toLowerCase();
            const sub = (card.querySelector('.event-sub')||{textContent:''}).textContent.toLowerCase();
            card.style.display = (!q || title.includes(q) || sub.includes(q)) ? '' : 'none';
          });
        },200);
      });
    }
  });
})();
