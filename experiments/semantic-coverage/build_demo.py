#!/usr/bin/env python3
"""Build a self-contained demo.html: each spec annotated in reading order as a TABLE --
the wide column is the block text, and every embedding model gets its own score column.
Click a score column's header to make it control the heat-map, threshold, histogram, and
overview ruler, so you can compare how different models score the same block.

Consumes the scores-<behaviour>-<provider>.json files score.py writes, plus the full
block text (reading order) from cite.py. All data is embedded, so demo.html opens directly
in a browser with no server. Re-run after any score.py run.

    python3 build_demo.py     # -> demo.html
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "engine" / "spec-cite"))
import cite  # noqa: E402
import score  # noqa: E402  (reuse units_meta so demo locators match the scores exactly)

SPECS = ("constitution", "model-spec")
SPEC_LABEL = {"constitution": "Anthropic constitution", "model-spec": "OpenAI model-spec"}


def blocks():
    """Full text of every non-empty block, reading order, keyed by the same locator
    score.py uses (so scores join by locator)."""
    out = []
    for chunk in ("paragraph", "sentence"):
        for loc, spec, section, text in score.units_meta(chunk):
            out.append({"loc": loc, "spec": spec, "section": section, "text": text, "chunk": chunk})
    return out


def configs():
    """Every scores-*.json, keyed 'behaviour|model'."""
    out = {}
    for f in sorted(HERE.glob("scores-*.json")):
        d = json.loads(f.read_text())
        chunk = d.get("chunk", "paragraph")
        out[f"{d['behaviour']}|{d['model']}|{chunk}"] = {
            "behaviour": d["behaviour"], "label": d["label"],
            "provider": d["provider"], "model": d["model"], "chunk": chunk,
            "query": d.get("query", ""), "source": d.get("source", ""),
            "scores": {r["locator"]: r["score"] for r in d["results"]},
        }
    return out


def comparisons():
    """Per non-K3 column: how it maps onto K3 (from compare.py --emit). {} if absent."""
    f = HERE / "compare.json"
    return json.loads(f.read_text()) if f.exists() else {}


TEMPLATE = r"""<!doctype html><meta charset=utf-8><title>Semantic coverage demo</title>
<meta name=robots content="noindex, nofollow">
<style>
body{font:14px/1.55 system-ui,-apple-system,sans-serif;margin:0;color:#111}
header{position:sticky;top:0;background:#fff;border-bottom:1px solid #ddd;padding:.7rem 1.25rem;z-index:7}
.row{display:flex;gap:1.4rem;align-items:flex-end;flex-wrap:wrap}
label,.hcap{font-size:11px;color:#666;display:flex;flex-direction:column;gap:.2rem;text-transform:uppercase;letter-spacing:.03em}
select,input[type=range]{font:14px system-ui}
#hist{background:#fbfbfc;border:1px solid #eee;border-radius:3px;display:block}
#stats{margin-left:auto;font-size:12px;color:#333;text-align:right;text-transform:none;letter-spacing:0}
#dir{max-width:64rem;margin:.8rem auto 0;padding:0 1.5rem}
#dir summary{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#777;cursor:pointer}
#dir .box{background:#f6f8fa;border:1px solid #e3e7ea;border-radius:6px;padding:.6rem .8rem;margin-top:.45rem}
#dir .q{font-size:13px;white-space:pre-wrap}
#dir .src{font-size:11px;color:#777;margin-top:.4rem;font-style:italic}
#dir mark.exp{background:#fdf0b8;color:#111;border-radius:2px;padding:0 1px}
#dir .mech{font-size:11px;color:#555;margin-top:.5rem;line-height:1.45;border-top:1px solid #e3e7ea;padding-top:.4rem}
#cmp{max-width:64rem;margin:.55rem auto 0;padding:0 1.5rem}
#cmp summary{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#777;cursor:pointer}
table.cmp{border-collapse:collapse;margin:.45rem 0 .3rem;font-size:12px}
table.cmp th{font-weight:600;color:#666;text-align:right;padding:.15rem .7rem;border-bottom:1px solid #e3e7ea}
table.cmp th:first-child,table.cmp td:first-child{text-align:left;font-family:ui-monospace,monospace}
table.cmp td{text-align:right;padding:.15rem .7rem;font-variant-numeric:tabular-nums}
.cmpnote{font-size:11px;color:#888;max-width:52rem;line-height:1.4}
#matchinfo{max-width:64rem;margin:.3rem auto 0;padding:0 1.5rem;font-size:11px;color:#555;font-family:ui-monospace,monospace}
#help{max-width:64rem;margin:.35rem auto 0;padding:0 1.5rem;font-size:11px;color:#777;line-height:1.4}
main{max-width:64rem;margin:0 auto;padding:0 1.5rem 4rem}
.thead{display:flex;position:sticky;background:#fff;border-bottom:2px solid #ccc;z-index:6;align-items:flex-end}
.thsc{flex:0 0 3rem;writing-mode:vertical-rl;transform:rotate(180deg);height:15rem;
  padding:.5rem .1rem .35rem;font:11px ui-monospace,monospace;color:#555;cursor:pointer;white-space:nowrap}
.thsc.ctrl{color:#0a52cc;font-weight:700;background:#eef4fe}
.thsc:hover{background:#f2f5f9}
.thtext{flex:1;padding:.3rem .55rem .4rem;font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:#999}
.sec{font-size:12px;color:#06c;font-family:ui-monospace,monospace;border-top:1px solid #eee;
  padding:.6rem .55rem .15rem;margin-top:.5rem;scroll-margin-top:6rem}
.trow{display:flex;align-items:flex-start;border-top:1px solid #f4f4f4}
.tsc{flex:0 0 3rem;text-align:right;padding:.35rem .3rem;font:11px ui-monospace,monospace;color:#666}
.tsc.ctrl{color:#111;font-weight:700}
.tsc.off{text-decoration:line-through;color:#b6bcc6}
.ttext{flex:1;padding:.35rem .55rem;white-space:pre-wrap}
.ttext.off{color:#98a0ab}
.note{color:#a00;padding:2rem 0}
#ruler{position:fixed;right:0;width:13px;z-index:6;border-left:1px solid #e6e6e6;background:#fff}
#rulercv{display:block;cursor:pointer}
#rulervp{position:absolute;left:0;width:100%;background:rgba(47,111,224,.13);
  border-top:1px solid rgba(47,111,224,.45);border-bottom:1px solid rgba(47,111,224,.45);pointer-events:none}
</style>
<header><div class=row>
  <label>Spec<select id=spec></select></label>
  <label>Behaviour<select id=beh></select></label>
  <label>Chunk<select id=chunk></select></label>
  <label>Threshold <b id=tv>0.50</b><input id=th type=range min=0 max=1 step=.01 value=.5></label>
  <label>Match others<select id=match><option value=overlap>overlap (F1)</option><option value=count>count</option><option value=none>none</option></select></label>
  <span class=hcap>distribution<svg id=hist width=220 height=44></svg></span>
  <span id=stats></span>
</div></header>
<div id=help>Slider = the <b>reference</b> column's cutoff for "relevant". <b>Match others</b> = how each other column's threshold is chosen to reproduce that selection (overlap = best F1 vs the reference; count = same number of passages). Click any score-column header to make it the reference.</div>
<details id=dir open><summary>Direction vector (exact text embedded)</summary><div id=dirbody></div></details>
<details id=cmp open><summary>How each column maps to Kimi-K3 (the LLM judge)</summary><div id=cmpbody></div></details>
<div id=matchinfo></div>
<main id=out></main>
<div id=ruler><canvas id=rulercv></canvas><div id=rulervp></div></div>
<script>
var BLOCKS=__BLOCKS__, CONFIGS=__CONFIGS__, COMPARE=__COMPARE__, SPEC_LABEL=__SPEC_LABEL__;
var REFMODEL="moonshotai/Kimi-K3";   // the reference column the others are compared against

function uniq(a){var s=[],seen={};a.forEach(function(x){if(!seen[x]){seen[x]=1;s.push(x);}});return s;}
function opt(sel,val,txt){var o=document.createElement('option');o.value=val;o.textContent=txt;sel.appendChild(o);}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');}
function shortModel(m){return m.indexOf('/')>=0?m.split('/').pop():m;}

var specs=uniq(BLOCKS.map(function(b){return b.spec;}));
var behs=[],bseen={},blabel={},models=[],mseen={},chunks=[],cseen={};
Object.keys(CONFIGS).forEach(function(k){var c=CONFIGS[k];
  if(!bseen[c.behaviour]){bseen[c.behaviour]=1;behs.push(c.behaviour);blabel[c.behaviour]=c.label;}
  if(!mseen[c.model]){mseen[c.model]=1;models.push(c.model);}
  if(!cseen[c.chunk]){cseen[c.chunk]=1;chunks.push(c.chunk);}});
chunks.sort();  // paragraph before sentence

var $spec=document.getElementById('spec'),$beh=document.getElementById('beh'),$chunk=document.getElementById('chunk'),$th=document.getElementById('th'),$match=document.getElementById('match');
specs.forEach(function(s){opt($spec,s,SPEC_LABEL[s]||s);});
behs.forEach(function(b){opt($beh,b,blabel[b]);});
chunks.forEach(function(c){opt($chunk,c,c);});

var ctrl=null;                       // which model column controls the highlighting
function sourcesFor(beh,chunk){var o=[];models.forEach(function(m){if(CONFIGS[beh+'|'+m+'|'+chunk])o.push(m);});return o;}
function col(n){var r=Math.round(255+(13-255)*n),g=Math.round(255+(84-255)*n),b=Math.round(255+(199-255)*n);return 'rgb('+r+','+g+','+b+')';}
function cellcol(n){var r=Math.round(255+(205-255)*n),g=Math.round(255+(223-255)*n),b=Math.round(255+(247-255)*n);return 'rgb('+r+','+g+','+b+')';}

function drawHist(vals,th){
  var bins=22,h=[],i;for(i=0;i<bins;i++)h.push(0);
  vals.forEach(function(n){var b=Math.floor(n*bins);if(b>=bins)b=bins-1;if(b<0)b=0;h[b]++;});
  var mx=Math.max.apply(null,h)||1,W=220,H=44,bw=W/bins,svg='';
  for(i=0;i<bins;i++){var bh=Math.round((H-2)*h[i]/mx),above=(i+0.5)/bins>=th;
    svg+='<rect x="'+(i*bw).toFixed(1)+'" y="'+(H-bh)+'" width="'+(bw-1).toFixed(1)+'" height="'+bh+'" fill="'+(above?'#2f6fe0':'#d3d9e0')+'"/>';}
  var tx=(th*W).toFixed(1);
  svg+='<line x1="'+tx+'" y1="0" x2="'+tx+'" y2="'+H+'" stroke="#e11" stroke-width="1"/>';
  document.getElementById('hist').innerHTML=svg;
}

// overview ruler: one tick per row (heat if above threshold, faint if below), a viewport box, click-to-jump
var lastNorms=[],lastTh=0;
function layoutRuler(){
  var hd=document.querySelector('header').offsetHeight,r=document.getElementById('ruler');
  var h=Math.max(0,window.innerHeight-hd);r.style.top=hd+'px';r.style.height=h+'px';
  var cv=document.getElementById('rulercv');cv.width=13;cv.height=h;
}
function drawRuler(norms,th){
  var cv=document.getElementById('rulercv'),ctx=cv.getContext('2d');
  ctx.clearRect(0,0,cv.width,cv.height);
  var rows=document.getElementById('out').querySelectorAll('.trow');
  var total=document.body.scrollHeight||1,rh=cv.height,w=cv.width,i,y;
  for(i=0;i<rows.length;i++){if(norms[i]>=th)continue;
    y=Math.round((rows[i].offsetTop/total)*rh);ctx.fillStyle='#e9edf1';ctx.fillRect(0,y,w,2);}
  for(i=0;i<rows.length;i++){if(norms[i]<th)continue;
    y=Math.round((rows[i].offsetTop/total)*rh);ctx.fillStyle=col(norms[i]);ctx.fillRect(0,y,w,2);}
}
function drawViewport(){
  var total=document.body.scrollHeight||1,rh=document.getElementById('rulercv').height;
  var vp=document.getElementById('rulervp');
  vp.style.top=((window.scrollY/total)*rh)+'px';
  vp.style.height=Math.max(10,(window.innerHeight/total)*rh)+'px';
}
function layoutThead(){var t=document.getElementById('thead');if(t)t.style.top=document.querySelector('header').offsetHeight+'px';}
function refreshRuler(){layoutRuler();drawRuler(lastNorms,lastTh);drawViewport();}

function render(){
  var spec=$spec.value, beh=$beh.value, chunk=$chunk.value, th=+$th.value;
  document.getElementById('tv').textContent=th.toFixed(2);
  var out=document.getElementById('out'), srcs=sourcesFor(beh,chunk);
  if(!srcs.length){out.innerHTML='<p class=note>No scores for this behaviour at '+esc(chunk)+' granularity yet.</p>';
    document.getElementById('stats').textContent='';document.getElementById('dirbody').innerHTML='';
    document.getElementById('cmpbody').innerHTML='';
    document.getElementById('hist').innerHTML='';lastNorms=[];lastTh=0;refreshRuler();return;}
  if(srcs.indexOf(ctrl)<0)ctrl=(srcs.indexOf(REFMODEL)>=0?REFMODEL:srcs[0]);
  var rows=BLOCKS.filter(function(b){return b.spec===spec&&b.chunk===chunk;});
  var st={};                                         // per-source min/max for normalization
  srcs.forEach(function(m){
    var sc=CONFIGS[beh+'|'+m+'|'+chunk].scores,vals=[];
    rows.forEach(function(b){var v=sc[b.loc];if(v!=null)vals.push(v);});
    var mn=Math.min.apply(null,vals),mx=Math.max.apply(null,vals);
    st[m]={mn:mn,mx:mx,span:(mx-mn)||1,sc:sc};
  });
  var ccfg=CONFIGS[beh+'|'+ctrl+'|'+chunk];
  var qhtml, mech='';
  if(ctrl.indexOf('+')>=0){                 // an annotation variant (e.g. model+expand)
    var kind=ctrl.split('+')[1], baseM=ctrl.split('+')[0];
    var bcfg=CONFIGS[beh+'|'+baseM+'|'+chunk], bq=bcfg?bcfg.query:'';
    var added=(bq&&ccfg.query.indexOf(bq)===0)?ccfg.query.slice(bq.length):'';
    qhtml=added?('<div class=q>'+esc(bq)+'<mark class=exp>'+esc(added)+'</mark></div>')
               :('<div class=q>'+esc(ccfg.query)+'</div>');
    mech='<div class=mech><b>Mechanism ('+esc(kind)+' = query expansion):</b> the highlighted text is what an LLM '+
      'appended to the base definition — concrete synonyms and phrasings the spec actually uses (e.g. “agree with,” '+
      '“to be polite”). That pulls the embedded direction toward the passages worded that way, so more of them rank high. '+
      'Switch the reference to <b>'+esc(shortModel(baseM))+'</b> and watch which passages lose their highlight — those are the ones expansion rescued.</div>';
  } else { qhtml='<div class=q>'+esc(ccfg.query)+'</div>'; }
  document.getElementById('dirbody').innerHTML='<div class=box>'+qhtml+
    (ccfg.source?'<div class=src>source: '+esc(ccfg.source)+'</div>':'')+mech+'</div>';
  var cmpRows='';
  srcs.forEach(function(m){
    if(m===REFMODEL)return;
    var c=COMPARE[beh+'|'+m+'|'+chunk];if(!c)return;
    cmpRows+='<tr><td>'+esc(shortModel(m))+'</td><td>'+c.spearman.toFixed(2)+'</td><td>'+c.auc.toFixed(2)+
      '</td><td>'+c.iso_rmse.toFixed(2)+' / '+c.kstd.toFixed(2)+'</td><td>'+c.f1.toFixed(2)+' @ '+c.thr.toFixed(2)+'</td></tr>';
  });
  document.getElementById('cmpbody').innerHTML = cmpRows
    ? '<table class=cmp><tr><th>column</th><th>Spearman</th><th>AUC</th><th>iso-RMSE / K3σ</th><th>best F1 @thr</th></tr>'+cmpRows+'</table>'+
      '<div class=cmpnote>vs Kimi-K3 (relevant = K3≥0.5). Spearman = rank agreement (the ceiling for any monotonic mapping); AUC = threshold-free ranking of K3-relevant chunks; iso-RMSE / K3σ = residual after the best monotonic fit vs. just predicting the mean; F1 @thr = the best single threshold on this column.</div>'
    : '<div class=cmpnote>No Kimi-K3 reference at '+esc(chunk)+' granularity — no comparison.</div>';
  // per-column selected sets: reference = controlling column (slider threshold); other
  // columns get a matched threshold -- count = same N as reference, overlap = best F1 vs it.
  var matchMode=$match.value;
  var refset={},Nref=0;
  rows.forEach(function(b){var cv=st[ctrl].sc[b.loc];if(cv==null)return;var cn=(cv-st[ctrl].mn)/st[ctrl].span;if(cn>=th){refset[b.loc]=1;Nref++;}});
  var colOn={},colThr={},colHit={};
  srcs.forEach(function(m){
    if(m===ctrl||matchMode==='none'){colOn[m]=refset;return;}
    var arr=[];rows.forEach(function(b){var v=st[m].sc[b.loc];if(v!=null)arr.push([b.loc,v]);});
    arr.sort(function(a,b){return b[1]-a[1];});
    var K,k;
    if(matchMode==='count'){K=Math.min(Nref,arr.length);}
    else{var tp=0,bf=-1,bk=0;for(k=1;k<=arr.length;k++){if(refset[arr[k-1][0]])tp++;var pr=tp/k,rc=Nref?tp/Nref:0,f1=(pr+rc)?2*pr*rc/(pr+rc):0;if(f1>bf){bf=f1;bk=k;}}K=bk;}
    var on={},hit=0,i;for(i=0;i<K;i++){on[arr[i][0]]=1;if(refset[arr[i][0]])hit++;}
    colOn[m]=on;colThr[m]=K>0?arr[K-1][1]:null;colHit[m]=hit;
  });
  var mi=[];
  if(matchMode!=='none'){srcs.forEach(function(m){if(m===ctrl||colThr[m]==null)return;
    mi.push(esc(shortModel(m))+' ≥'+colThr[m].toFixed(3)+' → '+colHit[m]+'/'+Nref+' overlap');});}
  document.getElementById('matchinfo').innerHTML = mi.length
    ? 'columns matched to '+esc(shortModel(ctrl))+' top-'+Nref+' ['+matchMode+']:   '+mi.join('     ')
    : '';
  var thead='<div class=thead id=thead>';
  srcs.forEach(function(m){thead+='<span class="thsc'+(m===ctrl?' ctrl':'')+'" data-m="'+esc(m)+'" title="'+esc(m)+'">'+esc(shortModel(m))+'</span>';});
  thead+='<span class=thtext>text &mdash; highlighted by '+esc(shortModel(ctrl))+' (click a score column to switch)</span></div>';
  var parts=[thead],curSec=null,ctrlNorms=[],shown=Nref;
  rows.forEach(function(b){
    if(b.section!==curSec){curSec=b.section;parts.push('<div class=sec>'+esc(b.section)+'</div>');}
    var cv=st[ctrl].sc[b.loc],cn=cv==null?0:(cv-st[ctrl].mn)/st[ctrl].span;ctrlNorms.push(cn);
    var refon=!!refset[b.loc];
    var cells='';
    srcs.forEach(function(m){
      var v=st[m].sc[b.loc], mon=!!(colOn[m]&&colOn[m][b.loc]);
      if(v==null){cells+='<span class="tsc'+(mon?'':' off')+'"></span>';return;}
      var n=(v-st[m].mn)/st[m].span;
      cells+='<span class="tsc'+(m===ctrl?' ctrl':'')+(mon?'':' off')+'" style="background:'+(mon?cellcol(n):'#fff')+'">'+v.toFixed(3)+'</span>';
    });
    parts.push('<div class=trow>'+cells+'<span class="ttext'+(refon?'':' off')+'" style="background:'+(refon?col(cn):'#fff')+
      '" title="'+esc(shortModel(ctrl))+' '+(cv==null?'n/a':cv.toFixed(3))+' | normalized '+cn.toFixed(2)+'">'+esc(b.text)+'</span></div>');
  });
  out.innerHTML=parts.join('');
  Array.prototype.forEach.call(out.querySelectorAll('.thsc'),function(el){
    el.addEventListener('click',function(){ctrl=el.getAttribute('data-m');render();});});
  layoutThead();drawHist(ctrlNorms,th);
  lastNorms=ctrlNorms;lastTh=th;refreshRuler();
  var s=st[ctrl];
  document.getElementById('stats').textContent=
    shortModel(ctrl)+'  ·  '+shown+' / '+rows.length+' highlighted  ·  cosine '+s.mn.toFixed(2)+'–'+s.mx.toFixed(2);
}
[$spec,$beh,$chunk,$th,$match].forEach(function(e){e.addEventListener('input',render);});
window.addEventListener('scroll',drawViewport,{passive:true});
window.addEventListener('resize',function(){layoutThead();refreshRuler();});
document.getElementById('rulercv').addEventListener('click',function(e){
  var total=document.body.scrollHeight;window.scrollTo(0,(e.offsetY/this.height)*total-window.innerHeight*0.3);});
render();
</script>"""


def main():
    bl = blocks()
    cf = configs()
    if not cf:
        sys.exit("no scores-*.json found -- run score.py first")
    html_out = (TEMPLATE
                .replace("__BLOCKS__", json.dumps(bl))
                .replace("__CONFIGS__", json.dumps(cf))
                .replace("__COMPARE__", json.dumps(comparisons()))
                .replace("__SPEC_LABEL__", json.dumps(SPEC_LABEL)))
    (HERE / "demo.html").write_text(html_out)
    print(f"demo.html <- {len(bl)} blocks, {len(cf)} configs: {', '.join(cf)}")


if __name__ == "__main__":
    main()
