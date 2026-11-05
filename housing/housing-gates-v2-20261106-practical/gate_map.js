/* Ward office reference points; never locations of the listed homes. */
(function (root) {
  'use strict';
  function summarize(data, urls) {
    const selected = new Set(urls || []), counts = {}, mapped = new Set();
    Object.entries(data.wards || {}).forEach(([name, ward]) => {
      let n = 0; for (const url of ward.urls || []) if (selected.has(url)) { n++; mapped.add(url); }
      if (n) counts[name] = n;
    });
    return {counts, unmapped: [...selected].filter(url => !mapped.has(url)).length};
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {summarize};
  if (!root || !root.document) return;
  const document = root.document;
  const mapDataUrl = new URL('gate-map-data.js', document.currentScript.src).href;
  let selected = [], map, layer, tileFailure = false, loading, initializing;
  const data = () => root.GATE_MAP_DATA;
  const status = () => document.getElementById('gate-map-status');
  const say = value => { if (status()) status().textContent = value; };
  document.addEventListener('gate:filtered', e => {
    selected = Array.isArray(e.detail && e.detail.urls) ? e.detail.urls.slice() : [];
    if (map) render();
  });
  function node(tag, value) { const el = document.createElement(tag); if (value != null) el.textContent = value; return el; }
  function popup(name, ward, urls) {
    const box=node('div'), heading=node('strong',name+' · '+urls.length+' tin'); box.appendChild(heading);
    box.appendChild(node('p','Điểm tham chiếu: vị trí văn phòng quận, không phải vị trí căn nhà.'));
    const source=node('a','Osaka City ward office data'); source.href=data().source_url; source.target='_blank'; source.rel='noopener noreferrer'; box.appendChild(source);
    box.appendChild(node('small',' (retrieved '+data().source_retrieved+')'));
    const list=node('div'); box.appendChild(list); let page=0;
    const controls=node('div'), prev=node('button','← Trước'), next=node('button','Tiếp →'), label=node('span');
    prev.type=next.type='button'; controls.append(prev,label,next); box.appendChild(controls);
    function draw() {
      list.replaceChildren();
      for (const url of urls.slice(page*20,page*20+20)) {
        const item=(root.GATE_LISTING_BY_URL && root.GATE_LISTING_BY_URL[url]) || {}; const row=node('p'), a=node('a',item.title || 'Xem tin SUUMO');
        try { const u=new URL(url); if (u.protocol !== 'https:' || u.hostname !== 'suumo.jp' || u.username || u.password) continue; }
        catch (_) { continue; }
        a.href=url; a.target='_blank'; a.rel='noopener noreferrer'; row.appendChild(a);
        const detail=[item.price_jpy ? Number(item.price_jpy).toLocaleString('ja-JP')+' JPY' : '',item.address].filter(Boolean).join(' · ');
        if (detail) row.appendChild(node('small',' '+detail)); list.appendChild(row);
      }
      prev.disabled=page===0; next.disabled=(page+1)*20>=urls.length; label.textContent=' '+(page+1)+' / '+Math.ceil(urls.length/20)+' ';
    }
    prev.onclick=()=>{page--;draw();}; next.onclick=()=>{page++;draw();}; draw(); return box;
  }
  function render() {
    if (!map || !data()) return;
    layer.clearLayers(); const selectedSet=new Set(selected), summary=summarize(data(),selected);
    Object.entries(summary.counts).forEach(([name,count]) => {
      const ward=data().wards[name]; const urls=ward.urls.filter(url=>selectedSet.has(url));
      const marker=root.L.circleMarker([ward.lat,ward.lon],{radius:Math.min(22,8+Math.sqrt(count)),color:'#145d72',fillColor:'#1b8494',fillOpacity:0.76,weight:2});
      marker.bindTooltip(name+' · '+count, {direction:'top'}); marker.bindPopup(()=>popup(name,ward,urls),{maxHeight:300}); layer.addLayer(marker);
    });
    say('Theo bộ lọc: '+selected.length+' tin · '+summary.unmapped+' tin chưa có điểm quận. Điểm trên bản đồ là văn phòng quận, không phải vị trí căn nhà.'+(tileFailure?' Không tải được nền bản đồ; danh sách vẫn sử dụng được.':''));
    map.invalidateSize();
  }
  function loadData() {
    if (data()) return Promise.resolve();
    return new Promise((resolve,reject)=>{
      const script=node('script'); script.src=mapDataUrl; script.onload=()=>data()?resolve():reject(new Error('map data missing')); script.onerror=reject; document.head.appendChild(script);
    });
  }
  function loadLeaflet() {
    if (root.L) return Promise.resolve();
    if (loading) return loading;
    loading=new Promise((resolve,reject)=>{
      const css=node('link'); css.rel='stylesheet'; css.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'; document.head.appendChild(css);
      const script=node('script'); script.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'; script.onload=resolve; script.onerror=reject; document.head.appendChild(script);
    });
    return loading;
  }
  root.initGateMap = function () {
    if (map) { render(); return Promise.resolve(); }
    if (initializing) return initializing;
    if (!/^https?:$/.test(root.location.protocol)) { say('Mở trang qua máy chủ web để tải bản đồ. Danh sách vẫn sử dụng được.'); return Promise.resolve(); }
    const el=document.getElementById('gate-map'); if (!el) return Promise.resolve();
    say('Đang tải bản đồ…');
    initializing=loadData().then(loadLeaflet).then(()=>{
      map=root.L.map(el,{scrollWheelZoom:false}).setView([34.685,135.51],11);
      const tiles=root.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'});
      tiles.on('tileerror',()=>{ tileFailure=true; render(); }); tiles.addTo(map);
      layer=root.L.layerGroup().addTo(map); render();
    }).catch(()=>{ loading=null; say('Không tải được bản đồ. Kiểm tra kết nối; danh sách vẫn sử dụng được.'); }).finally(()=>{ initializing=null; });
    return initializing;
  };
})(typeof window !== 'undefined' ? window : null);
