(()=>{'use strict';
const $=id=>document.getElementById(id), KEY='osaka-housing:stars:v1';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])), norm=s=>String(s??'').normalize('NFKC').toLocaleLowerCase();
const CAT={used_condo:'Chung cư cũ',used_house:'Nhà riêng cũ',new_house:'Nhà riêng mới',new_condo_project:'Dự án chung cư mới',new_condo_unit:'Căn chung cư mới bán lại'};
const BUILD={completed:'Đã xong',completing_this_month:'Xong trong tháng 11',future:'Đang/sắp xây',after_contract:'Xây sau hợp đồng',unknown:'Chưa rõ'};
const WATCH={touches_band:'Khoảng giá chạm 4.000–5.000万',price_undisclosed:'Chưa công bố giá',fees_undisclosed:'Chưa công bố phí',outside_band:'Ngoài dải giá'};
const BASIS={station:'so theo ga',ward:'so theo quận',station_old_house_land_proxy:'giá đất theo ga',ward_old_house_land_proxy_coarse:'giá đất theo quận (thô)',insufficient_comparables:'thiếu mẫu so sánh',land_estimate_exceeds_price:'ước tính đất vượt giá rao'};
const REASON={built_before_1982:'Xây trước 1982',rights_not_freehold:'Không phải sở hữu đất',leasehold_claim:'Ghi đất thuê',multi_lot_entry:'Tin gộp nhiều lô',land_estimate_exceeds_price:'Ước tính đất vượt giá rao',residual_capped_at_price:'Ước tính đất vượt giá rao',renovation_cost_not_included:'Chưa tính chi phí cải tạo',new_build_year_unknown:'Chưa rõ năm hoàn thành','identity:price_conflict':'Các tin lệch giá','identity:weak_key_not_merged':'Thiếu trường để gom',cheaper_route_has_no_brokerage_listing:'Có tin khác của cùng căn không mất phí môi giới'};
const SUUMO={not_in_suumo:'Không có trên SUUMO 02/11',in_suumo_other_price:'Có trên SUUMO nhưng ở giá khác'};
let rows=[],filtered=[],stars=new Set(),page=0;
try{const a=JSON.parse(localStorage.getItem(KEY)||'[]');if(Array.isArray(a))stars=new Set(a.filter(x=>typeof x==='string'))}catch{$('storage-note').textContent='Không đọc/lưu được sao trong trình duyệt này.'}
const yen=v=>v==null?'':Math.round(v).toLocaleString('ja-JP')+' yên', man=v=>(v/10000).toLocaleString('ja-JP');
function safe(u){try{const x=new URL(u);return ['https:','http:'].includes(x.protocol)?x.href:''}catch{return ''}}
function price(r){if(r.price_min==null)return r.price_raw?esc(r.price_raw):'Chưa công bố giá';return r.price_max&&r.price_max!==r.price_min?`${man(r.price_min)}–${man(r.price_max)} 万円`:`${man(r.price_min)} 万円`}
function reasons(s){return String(s||'').split(';').filter(Boolean).map(x=>REASON[x]||x).join(' · ')}
function num(id){const v=$(id).value.trim();if(v==='')return null;const n=Number(v);return Number.isFinite(n)&&n>=0?n:NaN}
function apply(){const q=norm($('query').value).trim().split(/\s+/).filter(Boolean),b=$('band').value,c=$('category').value,w=$('ward').value,bs=$('build').value,br=$('broker').value,fav=$('favorites').value,lo=num('price-min'),hi=num('price-max'),wk=num('walk-max');
 if([lo,hi,wk].some(Number.isNaN)){$('error').textContent='Giá và thời gian đi bộ phải là số không âm.';return []}
 if(lo!=null&&hi!=null&&lo>hi){$('error').textContent='Giá tối thiểu lớn hơn giá tối đa.';return []}
 $('error').textContent='';
 return rows.filter(r=>{const pmin=r.price_min,pmax=r.price_max??r.price_min;
  if(lo!=null||hi!=null){if(pmin==null){if(r.category!=='new_condo_project')return false}else{if(lo!=null&&pmax<lo*10000)return false;if(hi!=null&&pmin>hi*10000)return false}}
  if(wk!=null&&!(r.walk_minutes!=null&&r.walk_minutes<=wk))return false;
  if(c&&r.category!==c)return false;if(w&&r.ward!==w)return false;if(bs&&r.build_status!==bs)return false;if(br==='none'&&!r.no_brokerage)return false;if(fav&&!stars.has(r.url))return false;
  return q.every(t=>norm([r.address,r.name,r.station_raw,r.ward,CAT[r.category]].join(' ')).includes(t))})}
function bandOk(r,b){return !b||(b==='ranked'?'ABCD'.includes(r.band)&&r.band.length===1:r.band===b)}
function sorter(k){const v=r=>k==='price'?r.price_min:k==='walk'?r.walk_minutes:r[k];return (a,b)=>(v(a)??Infinity)-(v(b)??Infinity)||String(a.id).localeCompare(String(b.id))}
function card(r){const saved=stars.has(r.url),u=safe(r.url);const area=r.unit_m2?(r.unit_m2_max&&r.unit_m2_max!==r.unit_m2?`${r.unit_m2}–${r.unit_m2_max} m²`:`${r.unit_m2} m²`):[r.land_m2&&`đất ${r.land_m2}`,r.building_m2&&`nhà ${r.building_m2}`].filter(Boolean).join(' / ')+(r.land_m2||r.building_m2?' m²':'');
 const cost=r.net_month!=null?`<div class="cost">Chi phí ở thực <b>${yen(r.net_month)}</b>/tháng · ${yen(r.net_m2)}/m² · kịch bản xấu ${yen(r.net_stress)}</div>`:(r.category==='new_condo_project'?`<div class="cost">${esc(WATCH[r.watch]||'')}${r.fees_m2?` · phí ${yen(r.fees_m2)}/m²/tháng`:''}${r.keep?` · giữ giá khu ${r.keep.toFixed(2)}`:''}</div>`:'');
 const attrs=[['Loại',CAT[r.category]||r.category],['Quận',r.ward],['Ga',r.station_raw],['Diện tích',area],['Bố trí',r.layout],[r.category.startsWith('new')?'Hoàn thành':'Năm xây',r.built],['Bàn giao',r.handover],['Tình trạng xây',BUILD[r.build_status]],['Tổng số căn',r.units_total],['Tầng',r.floor],['Người bán',r.seller],['Phí môi giới',r.no_brokerage?'Không mất phí':''],['Tỷ lệ giữ giá',r.keep!=null&&r.category!=='new_condo_project'?r.keep.toFixed(2):''],['Cách ước tính',BASIS[r.residual_basis]||r.residual_basis],['Số mẫu so sánh',r.groups],['Phí định kỳ',r.recurring!=null?yen(r.recurring)+'/tháng':r.fees_min?`${yen(r.fees_min)}–${yen(r.fees_max)}/tháng`:''],['So với SUUMO',SUUMO[r.suumo_status]?SUUMO[r.suumo_status]+(r.suumo_prices?` (${r.suumo_prices})`:''):''],['Nguồn',`${r.source} · ${r.snapshot}`],['Số tin cùng căn',r.listing_count>1?r.listing_count:'']].filter(([,v])=>v!==undefined&&v!==null&&v!=='');
 const rs=reasons(r.reasons),others=String(r.other_urls||'').split(' ').map(safe).filter(Boolean);
 return `<article class="card"><div class="top"><span class="pill ${esc(r.band)}">Nhóm ${esc(r.band)}</span><span class="muted">${esc(CAT[r.category]||'')}</span><button class="star" data-url="${esc(r.url)}" aria-label="Lưu" aria-pressed="${saved}">${saved?'★':'☆'}</button></div><div class="price">${price(r)}</div>${cost}<h2>${esc(r.name||r.address||'')}</h2>${r.name?`<div class="muted">${esc(r.address||'')}</div>`:''}<dl class="attrs">${attrs.map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>${rs?`<p class="muted">${esc(rs)}</p>`:''}<p>${u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">Mở tin gốc</a>`:''}${others.length?` · ${others.slice(0,4).map((x,i)=>`<a href="${esc(x)}" target="_blank" rel="noopener noreferrer">tin ${i+2}</a>`).join(' · ')}`:''}</p></article>`}
function render(){const base=apply(),b=$('band').value;filtered=base.filter(r=>bandOk(r,b)).sort(sorter($('sort').value));
 const cnt={};for(const r of base)cnt[r.band]=(cnt[r.band]||0)+1;
 $('counts').innerHTML=['A','B','C','D','U','S','P','N'].map(k=>`<span class="pill ${k}">${k}: ${cnt[k]||0}</span>`).join('');
 const size=Number($('size').value),pages=Math.max(1,Math.ceil(filtered.length/size));page=Math.min(page,pages-1);
 $('cards').innerHTML=filtered.slice(page*size,(page+1)*size).map(card).join('')||'<p>Không có mục phù hợp. Hãy nới bộ lọc.</p>';
 $('count').textContent=`${filtered.length} mục`;$('page').textContent=`${page+1} / ${pages}`;$('prev').disabled=page===0;$('next').disabled=page>=pages-1}
function options(id,vals,label){for(const v of [...new Set(vals.filter(Boolean))].sort()){const o=document.createElement('option');o.value=v;o.textContent=label?label(v):v;$(id).append(o)}}
fetch('listing-data.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).then(d=>{rows=d.rows;options('category',rows.map(r=>r.category),v=>CAT[v]||v);options('ward',rows.map(r=>r.ward));$('status').textContent=`${rows.length} mục · ${d.policy_version}`;render()}).catch(e=>{$('status').textContent='Không tải được dữ liệu ('+e.message+').'});
['query','band','category','ward','price-min','price-max','walk-max','build','broker','sort','favorites','size'].forEach(id=>$(id).addEventListener(['query','price-min','price-max','walk-max'].includes(id)?'input':'change',()=>{page=0;render()}));
$('reset').onclick=()=>{['query','walk-max'].forEach(i=>$(i).value='');$('price-min').value='4000';$('price-max').value='5000';['category','ward','build','broker','favorites'].forEach(i=>$(i).value='');$('band').value='ranked';$('sort').value='net_m2';page=0;render()};
$('prev').onclick=()=>{page--;render();scrollTo(0,0)};$('next').onclick=()=>{page++;render();scrollTo(0,0)};
$('cards').addEventListener('click',e=>{const b=e.target.closest('.star');if(!b)return;const u=b.dataset.url;stars.has(u)?stars.delete(u):stars.add(u);try{localStorage.setItem(KEY,JSON.stringify([...stars]))}catch{$('storage-note').textContent='Không lưu được sao trong trình duyệt này.'}render()});
})();
