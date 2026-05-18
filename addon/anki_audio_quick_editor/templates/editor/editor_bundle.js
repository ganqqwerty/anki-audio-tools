var Zd=Object.defineProperty;var Fi=B=>{throw TypeError(B)};var Jd=(B,G,z)=>G in B?Zd(B,G,{enumerable:!0,configurable:!0,writable:!0,value:z}):B[G]=z;var Ke=(B,G,z)=>Jd(B,typeof G!="symbol"?G+"":G,z),Ia=(B,G,z)=>G.has(B)||Fi("Cannot "+z);var d=(B,G,z)=>(Ia(B,G,"read from private field"),z?z.call(B):G.get(B)),R=(B,G,z)=>G.has(B)?Fi("Cannot add the same private member more than once"):G instanceof WeakSet?G.add(B):G.set(B,z),F=(B,G,z,Zn)=>(Ia(B,G,"write to private field"),Zn?Zn.call(B,z):G.set(B,z),z),ae=(B,G,z)=>(Ia(B,G,"access private method"),z);(function(){"use strict";var li,ui,ci,an,on,Tt,sn,Bn,Gn,Dt,nt,ln,ge,Ba,Ga,Va,Ci,Ee,Oa,Ve,Ot,_e,He,ye,Oe,rt,$t,gt,un,cn,fn,We,qr,ee,zd,eh,th,Ha,Cr,Rr,Wa,fi,$e,je,be,Lt,Vn,Hn,Mr,di;const B=[{activeIcon:"pause",command:"aqe:play",icon:"play",iconOnly:!0,label:"Play",title:"Play or pause current audio"},{activeIcon:"audio-lines",command:"aqe:analyze",icon:"audio-lines",iconOnly:!0,label:"Graph",title:"Analyze and show pitch/intensity graph"},{command:"aqe:show-file",icon:"folder-open",label:"Folder",title:"Show current audio file in folder"},{command:"aqe:trim-left",icon:"scissors",label:"-L",title:"Trim 100 ms from left"},{command:"aqe:trim-right",icon:"scissors",label:"-R",title:"Trim 100 ms from right"},{command:"aqe:remove-pauses",icon:"timer-reset",label:"Shorten Pauses",title:"Speed up long internal pauses"},{command:"aqe:slower",icon:"rewind",label:"Slower",title:"Decrease speed"},{command:"aqe:faster",icon:"fast-forward",label:"Faster",title:"Increase speed"},{command:"aqe:volume-down",icon:"volume-1",iconOnly:!0,label:"Volume -",title:"Decrease volume"},{command:"aqe:volume-up",icon:"volume-2",iconOnly:!0,label:"Volume +",title:"Increase volume"},{command:"aqe:undo",icon:"undo-2",iconOnly:!0,label:"Undo",title:"Restore the previous generated audio reference"},{command:"aqe:redo",icon:"redo-2",iconOnly:!0,label:"Redo",title:"Restore the most recently undone audio reference"},{command:"aqe:settings",icon:"settings",iconOnly:!0,label:"Settings",title:"Open Audio Quick Editor settings"}],G=[{command:"aqe:denoise-standard",icon:"volume-x",label:"Standard",title:"Denoise speech with DeepFilterNet"},{command:"aqe:rnnoise",icon:"waves",label:"RNNoise",title:"Denoise speech with RNNoise"}],z=new Set(["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:remove-pauses","aqe:denoise-standard","aqe:rnnoise","aqe:volume-down","aqe:volume-up"]),Zn={"aqe:play":"play","aqe:analyze":"graph","aqe:show-file":"show-file","aqe:delete-selection":"delete-selection","aqe:trim-left":"trim-left","aqe:trim-right":"trim-right","aqe:remove-pauses":"remove-pauses","aqe:denoise-standard":"denoise-standard","aqe:rnnoise":"rnnoise","aqe:slower":"slower","aqe:faster":"faster","aqe:volume-down":"volume-down","aqe:volume-up":"volume-up","aqe:undo":"undo","aqe:redo":"redo","aqe:settings":"settings"};function xr(e,t){return`aqe-button-${e}-${Zn[t]}`}function ja(e){return e==="aqe:denoise-standard"?"Denoising with Standard...":e==="aqe:rnnoise"?"Denoising with RNNoise...":e==="aqe:delete-selection"?"Deleting region...":"Processing..."}function Xe(e){return document.querySelector(`.aqe-controls[data-aqe-field-ord="${e}"]`)}function $(e){return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${e}"]`)}function Ua(e,t){const n=Xe(e);return(n==null?void 0:n.querySelector(`[data-aqe-command="${t}"]`))??null}function Ka(e){return Ua(e,"aqe:analyze")}function Xa(e){return Ua(e,"aqe:play")}function Ya(e){const t=Xe(e);return(t==null?void 0:t.querySelector(".aqe-repeat-button"))??null}function Jn(){return Array.from(document.querySelectorAll(".aqe-button"))}function Tr(){return Array.from(document.querySelectorAll(".aqe-visualizer"))}const Qa=[];let zn=null,er=null;function tr(e){globalThis.pycmd!==void 0&&globalThis.pycmd(e)}function Bt(e,t){tr(`focus:${e}`),tr(t)}function Ri(e){zn=e,tr("aqe:analyze-field")}function xi(e){Qa.push(e),tr("aqe:frontend-log")}function Ti(){return Qa.shift()??null}function Di(e){window.__aqePendingPlaybackRequest=e,window.__aqeLastPlaybackRequest=e}function Oi(){if(!window.__aqePendingPlaybackRequest)return null;const e=window.__aqePendingPlaybackRequest;return window.__aqePendingPlaybackRequest=null,e}function $i(){if(!zn)return null;const e=zn;return zn=null,e}function Li(e){er=e}function Ii(){if(!er)return null;const e=er;return er=null,e}function Bi(e){window.__aqeLastCursorIntent=e}function Gi(e){return encodeURIComponent(e||"").replaceAll("%2F","/")}function Pe(e){return(e==null?void 0:e.querySelector(".aqe-audio-clock"))??null}function Dr(e){e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!1,e.__aqeAudioClockLastSeekedMs=0,e.dataset.progressClockMode="stopped"}function pn(e){const t=Pe(e);if(!(!t||typeof t.pause!="function"))try{t.pause()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Or(e){const t=Pe(e);if(Dr(e),!!t){pn(e),t.removeAttribute("src"),t.src="";try{t.load()}catch{e.__aqeAudioClockFallback=!0}}}function Vi(e,t){const n=Pe(e);if(Dr(e),!n){e.__aqeAudioClockFallback=!0;return}if(pn(e),!t){Or(e);return}n.setAttribute("src",Gi(t));try{n.load()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Hi(e,t={}){const n=Pe(e);!n||n.__aqeClockHandlersInstalled||(n.__aqeClockHandlersInstalled=!0,n.addEventListener("loadedmetadata",()=>{n.getAttribute("src")&&(e.__aqeAudioClockAvailable=!0,e.__aqeAudioClockFallback=!1)}),n.addEventListener("error",()=>{var r;e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,e.dataset.playbackState==="playing"&&e.dataset.progressClockMode==="audio"&&((r=t.onErrorDuringPlayback)==null||r.call(t))}),n.addEventListener("ended",()=>{var r;e.dataset.playbackState==="playing"&&((r=t.onEndedDuringPlayback)==null||r.call(t))}),n.addEventListener("seeked",()=>{e.__aqeAudioClockLastSeekedMs=Math.round((Number(n.currentTime)||0)*1e3)}))}function nr(e){const t=Pe(e);return!t||!(e!=null&&e.__aqeAudioClockAvailable)||!t.getAttribute("src")?!1:t.readyState===void 0||t.readyState>=1}function rr(e,t,n){const r=Pe(e);if(!r)return!1;const a=Math.max(0,Math.min(Number(t)||0,n||0));try{return r.currentTime=a/1e3,e.__aqeAudioClockLastSeekedMs=Math.round(a),!0}catch{return e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,!1}}var _n=(e=>(e.Debug="debug",e.Error="error",e.Info="info",e.Unknown="unknown",e.Warn="warn",e))(_n||{});function Wi(e){return e==="error"?console.error:console.warn}function ji(e){return e==="debug"?_n.Debug:e==="warn"?_n.Warn:e==="error"?_n.Error:_n.Info}function $r(e,t=0){const n=Ui(e);return n!==void 0?n:Array.isArray(e)?Ki(e,t):e!==null&&typeof e=="object"?Xi(e,t):Yi(e)}function Ui(e){if(e===void 0)return"[undefined]";if(e===null)return null;if(typeof e=="boolean"||typeof e=="number"||typeof e=="string")return e}function Ki(e,t){return t>=4?"[array]":e.map(n=>$r(n,t+1))}function Xi(e,t){if(t>=4)return"[object]";const n={};for(const[r,a]of Object.entries(e))n[r]=$r(a,t+1);return n}function Yi(e){return typeof e=="bigint"?e.toString():typeof e=="symbol"?e.description?`Symbol(${e.description})`:"Symbol()":typeof e=="function"?`[function ${e.name||"anonymous"}]`:"[unserializable]"}function Qi(e,t,n){const r={level:ji(e),message:t};return n!==void 0&&(r.context=$r(n)),r}function Zi(e,t){function n(r,a,o){const s=Wi(r);o===void 0?s(`[${e}] ${a}`):s(`[${e}] ${a}`,o);try{t(Qi(r,a,o))}catch{}}return{debug:(r,a)=>n("debug",r,a),error:(r,a)=>n("error",r,a),info:(r,a)=>n("info",r,a),warn:(r,a)=>n("warn",r,a)}}const ce=Zi("editor",xi),mn=[],ar=new Set;let or=null,sr=null,ir=!1;function Ji(){mn.length=0,ar.clear(),or=null,sr=null,ir=!1}function zi(e,t){for(const n of e){if(!n.sourceFilename)continue;const r=el(n);if(ar.has(r))continue;const a=$(n.ord);if((a==null?void 0:a.dataset.hasTrack)==="true"&&a.dataset.sourceFilename===n.sourceFilename){ar.add(r);continue}ar.add(r),mn.push({key:r,ord:n.ord,sourceFilename:n.sourceFilename})}lr(t)}function lr(e){if(!(or!==null||e.anyBusy()))for(;mn.length;){const t=mn.shift();if(!t)return;const n=$(t.ord);if(!n){Ja(t,e);return}const r=Xe(t.ord);if(!r){Ja(t,e);return}if((r.dataset.aqeSourceFilename||t.sourceFilename)===t.sourceFilename&&!(n.dataset.hasTrack==="true"&&n.dataset.sourceFilename===t.sourceFilename)){or=t.key,sr=t.ord,e.requestDefaultGraph({ord:t.ord,sourceFilename:t.sourceFilename});return}}}function Za(e,t){sr===e&&(or=null,sr=null,queueMicrotask(()=>lr(t)))}function el(e){return`${e.ord}\0${e.sourceFilename}`}function Ja(e,t){mn.unshift(e),!ir&&(ir=!0,window.setTimeout(()=>{ir=!1,lr(t)},0))}function tl(e,t){return Math.max(t.startMs,Math.min(Number(e)||0,t.endMs))}function nl(e){let t="start";e.playbackState==="playing"&&(t="pause"),e.playbackState==="paused"&&(t=e.resumeRequiresRestart?"start":"resume");let n=e.anchorMs;return t==="start"&&e.region.mode==="selection"&&(n=e.region.startMs),t==="pause"&&(n=za(e.currentProgressMs,e.cursorMs,n)),t==="resume"&&(n=za(e.currentProgressMs,e.cursorMs,n),e.region.mode==="selection"&&(n<e.region.startMs||n>e.region.endMs)&&(t="start",n=e.region.startMs)),{action:t,cursorMs:Math.round(n),endMs:Math.round(e.region.endMs),engine:e.engine,loop:e.repeat,ord:e.ord,regionMode:e.region.mode}}function za(e,t,n){return Number(e||t||n||0)}function rl(e){return{analyzerName:e.analyzerName,durationMs:Number(e.durationMs)||0,pitchMaxHz:e.pitchMaxHz,pitchMinHz:e.pitchMinHz,points:e.points.map(al),sourceFilename:e.sourceFilename}}function al(e){const t=typeof e[0]=="number"?e[0]:0,n=typeof e[1]=="number"?e[1]:null,r=typeof e[2]=="number"?e[2]:null,a=typeof e[3]=="boolean"?e[3]:!1;return[t,n,r,a]}function Lr(e){return e==="playing"||e==="paused"||e==="stopped"}const eo=50,ol=4;function to(){return{active:!1,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:null,startMs:null}}function no(e,t){return Math.max(0,Math.min(Number(e)||0,Math.max(0,Number(t)||0)))}function ur(e,t,n,r=eo){const a=no(Math.min(e,t),n),o=no(Math.max(e,t),n);return!n||o-a<r?null:{startMs:Math.round(a),endMs:Math.round(o)}}function sl(e,t){if(!e.active||e.startMs===null||e.endMs===null)return null;const n=ur(e.startMs,e.endMs,t);return n?{...n,mode:"selection"}:null}function il(e,t){if(!e.draftActive||e.draftStartMs===null||e.draftEndMs===null)return null;const n=ur(e.draftStartMs,e.draftEndMs,t);return n?{...n,mode:"selection"}:null}function ll(e,t,n,r){const a=ur(t,n,r);return a?{...e,active:!0,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:a.endMs,startMs:a.startMs}:cl(e)}function ul(e,t,n,r){const a=ur(t,n,r);return a?{...e,draftActive:!0,draftEndMs:a.endMs,draftStartMs:a.startMs}:ro(e)}function cl(e){return{...ro(e),active:!1,endMs:null,startMs:null}}function ro(e){return{...e,draftActive:!1,draftEndMs:null,draftStartMs:null}}function ao(e,t,n,r){return Math.abs(t.clientX-e.clientX)<ol||Math.abs(r-n)<eo}const q={width:620,height:150,left:44,right:10,top:10,bottom:34};function oo(){return q.width-q.left-q.right}function so(){return q.height-q.top-q.bottom}function ot(e,t){return t?q.left+Math.max(0,Math.min(1,e/t))*oo():q.left}function fl(e,t,n){if(!e||!t||!n||n<=t)return q.height-q.bottom;const r=Math.max(0,Math.min(1,(e-t)/(n-t)));return q.top+(1-r)*so()}function io(e,t){return t&&t<2e3?`${Math.round(e)} ms`:`${(e/1e3).toFixed(2)}s`}function dl(e,t){if(!e.length||!t)return"";const n=q.height-q.bottom,r=e[0];if(!r)return"";const a=`M ${ot(r[0],t).toFixed(2)} ${n.toFixed(2)}`,o=e.map(l=>{const c=ot(l[0],t).toFixed(2),f=Math.max(0,Math.min(1,l[2]??0)),u=(n-f*so()).toFixed(2);return`L ${c} ${u}`}).join(" "),s=e.at(-1)??r,i=`L ${ot(s[0],t).toFixed(2)} ${n.toFixed(2)} Z`;return`${a} ${o} ${i}`}function hl(e,t,n,r){const a=[];let o=[];for(const s of e){const i=s[1];if(!(s[3]===!0&&i!==null&&i!==void 0)){o.length&&a.push(o),o=[];continue}o.push([ot(s[0],t),fl(i,n,r)])}return o.length&&a.push(o),a}function pl(e,t){const n=e.querySelector(".aqe-pitch");if(n){n.textContent="";for(const r of hl(t.points,t.durationMs,t.pitchMinHz,t.pitchMaxHz)){if(r.length<2)continue;const a=document.createElementNS("http://www.w3.org/2000/svg","path");a.setAttribute("class","aqe-pitch-path"),a.setAttribute("d",r.map((o,s)=>{const i=o[0]??0,l=o[1]??0;return`${s?"L":"M"} ${i.toFixed(2)} ${l.toFixed(2)}`}).join(" ")),n.appendChild(a)}}}function _l(e,t){const n=e.querySelector(".aqe-labels");if(!n)return;n.textContent="";const r=t.pitchMaxHz||500,a=t.pitchMinHz||75;for(const o of[[r,q.top+10],[a,q.height-q.bottom]]){const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","aqe-hz-label"),s.setAttribute("x","2"),s.setAttribute("y",String(o[1])),s.textContent=`${Math.round(o[0])} Hz`,n.appendChild(s)}}function ml(e,t){const n=e.querySelector(".aqe-x-axis");if(!n)return;n.textContent="";const r=[0,t/2,t].filter((a,o,s)=>o===0||a!==s[o-1]);for(const a of r){const o=ot(a,t),s=document.createElementNS("http://www.w3.org/2000/svg","line");s.setAttribute("class","aqe-x-tick"),s.setAttribute("x1",o.toFixed(2)),s.setAttribute("x2",o.toFixed(2)),s.setAttribute("y1",String(q.height-q.bottom)),s.setAttribute("y2",String(q.height-q.bottom+4));const i=document.createElementNS("http://www.w3.org/2000/svg","text");i.setAttribute("class","aqe-x-label"),i.setAttribute("x",o.toFixed(2)),i.setAttribute("y",String(q.height-8)),i.textContent=io(a,t),n.append(s,i)}}function lo(e){const t=e.getBoundingClientRect(),n=Number(t.width)||q.width,r=Number(t.height)||q.height,a=Math.min(n/q.width,r/q.height)||1;return{left:t.left+q.left*a,width:oo()*a}}function vn(e,t,n){const r=lo(t);return Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*n}function vl(e){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="true",e.dataset.hasTrack="false",e.dataset.durationMs="0",e.dataset.sourceFilename="",e.dataset.anchorMs="0",e.dataset.cursorMs="0",e.dataset.progressMs="0",e.dataset.resumeRequiresRestart="false",e.dataset.playbackEngine="",e.dataset.playbackStartMs="0",e.dataset.playbackEndMs="0",e.dataset.playbackRegionMode="full",uo(e)}function gl(e,t){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="false",e.dataset.hasTrack="true",e.dataset.durationMs=String(t.durationMs||0),e.dataset.analyzerName=t.analyzerName||"",e.dataset.sourceFilename=t.sourceFilename||"";const n=e.querySelector(".aqe-intensity");n&&n.setAttribute("d",dl(t.points,t.durationMs)),pl(e,t),_l(e,t),ml(e,t.durationMs||0)}function yl(e,t,n="info"){const r=e.querySelector(".aqe-visualizer-status"),a=e.querySelector(".aqe-spinner"),o=n==="processing";e.dataset.graphBusy=o?"true":"false",a&&(a.hidden=!o),r&&(r.textContent=t||"",r.dataset.kind=n||"info")}function bl(e,t,n){const r=e.querySelector(".aqe-selection"),a=e.querySelector(".aqe-selection-start"),o=e.querySelector(".aqe-selection-end"),s=n??t,i=Number(e.dataset.durationMs||"0");if(!r||!a||!o||!s||!i){r==null||r.setAttribute("width","0"),r==null||r.setAttribute("visibility","hidden"),r==null||r.classList.remove("aqe-selection-draft"),a==null||a.setAttribute("visibility","hidden"),o==null||o.setAttribute("visibility","hidden");return}const l=ot(s.startMs,i),c=ot(s.endMs,i);r.setAttribute("visibility","visible"),r.classList.toggle("aqe-selection-draft",n!==null),r.setAttribute("x",l.toFixed(2)),r.setAttribute("y",String(q.top)),r.setAttribute("width",Math.max(0,c-l).toFixed(2)),r.setAttribute("height",String(q.height-q.top-q.bottom)),a.setAttribute("visibility","visible"),o.setAttribute("visibility","visible");for(const[f,u]of[[a,l],[o,c]])f.setAttribute("x1",u.toFixed(2)),f.setAttribute("x2",u.toFixed(2)),f.setAttribute("y1",String(q.top)),f.setAttribute("y2",String(q.height-q.bottom))}function wl(e,t,n){const r=ot(t,n),a=e.querySelector(".aqe-cursor");a&&(a.setAttribute("x1",r.toFixed(2)),a.setAttribute("x2",r.toFixed(2)));const o=e.querySelector(".aqe-cursor-label");o&&(o.textContent=io(t,n))}function uo(e){var t;(t=e.querySelector(".aqe-intensity"))==null||t.setAttribute("d",""),Ir(e,".aqe-pitch"),Ir(e,".aqe-labels"),Ir(e,".aqe-x-axis")}function ql(e){const t=e.querySelector(".aqe-cursor");t&&(t.setAttribute("x1",String(q.left)),t.setAttribute("x2",String(q.left)));const n=e.querySelector(".aqe-cursor-label");n&&(n.textContent="0 ms")}function Ml(e,t){return{analyzerName:t.analyzerName,durationMs:t.durationMs,ord:e,points:t.points.length,sourceFilename:t.sourceFilename}}function Ir(e,t){const n=e.querySelector(t);n&&(n.textContent="")}function gn(e){return!e||e.dataset.selectionActive!=="true"?null:sl({active:e.dataset.selectionActive==="true",startMs:Number(e.dataset.selectionStartMs||"0"),endMs:Number(e.dataset.selectionEndMs||"0")},Number(e.dataset.durationMs||"0"))}function Br(e){return!e||e.dataset.selectionDraftActive!=="true"?null:il({draftActive:e.dataset.selectionDraftActive==="true",draftStartMs:Number(e.dataset.selectionDraftStartMs||"0"),draftEndMs:Number(e.dataset.selectionDraftEndMs||"0")},Number(e.dataset.durationMs||"0"))}function co(e){const t=gn(e);return t||{startMs:0,endMs:Number(e.dataset.durationMs||"0")||0,mode:"full"}}function Gt(e,t={}){e.dataset.selectionDraftActive="false",e.dataset.selectionDraftStartMs="",e.dataset.selectionDraftEndMs="",t.redraw!==!1&&cr(e)}function Sl(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=ul(to(),t,n,a);return!o.draftActive||o.draftStartMs===null||o.draftEndMs===null?(Gt(e,r),!1):(e.dataset.selectionDraftActive="true",e.dataset.selectionDraftStartMs=String(o.draftStartMs),e.dataset.selectionDraftEndMs=String(o.draftEndMs),r.redraw!==!1&&cr(e),!0)}function kl(e,t,n={}){const r=Br(e);return r?(Gt(e,{redraw:!1}),Al(e,r.startMs,r.endMs,t,n)):(Gt(e),!1)}function fo(e,t={}){if(e.dataset.selectionActive="false",e.dataset.selectionStartMs="",e.dataset.selectionEndMs="",Gt(e,{redraw:!1}),cr(e),t.resetPlaybackRegion!==!1){const n=co(e);e.dataset.playbackStartMs=String(Math.round(n.startMs)),e.dataset.playbackEndMs=String(Math.round(n.endMs)),e.dataset.playbackRegionMode=n.mode}}function Al(e,t,n,r,a={}){const o=Number(e.dataset.durationMs||"0"),s=ll(to(),t,n,o);return!s.active||s.startMs===null||s.endMs===null?(fo(e),!1):(Gt(e,{redraw:!1}),e.dataset.selectionActive="true",e.dataset.selectionStartMs=String(s.startMs),e.dataset.selectionEndMs=String(s.endMs),e.dataset.playbackStartMs=String(s.startMs),e.dataset.playbackEndMs=String(s.endMs),e.dataset.playbackRegionMode="selection",cr(e),a.updateCursor!==!1&&r.setCursor(e,s.startMs,!1),!0)}function cr(e){const t=Br(e),n=t??gn(e);bl(e,n,t)}function El(){return document.body.dataset.aqeBusy==="true"}function Pl(e){var t;return((t=Xe(e))==null?void 0:t.querySelector(".aqe-delete-region-button"))??null}function ho(e,t){return e.startMs<=0&&e.endMs>=t}function po(e,t){return!!e&&e.endMs>e.startMs&&!ho(e,t)}function yn(e){const t=Number(e.dataset.aqeFieldOrd||"0"),n=Pl(t);if(!n)return;const r=gn(e),a=Number(e.dataset.durationMs||"0"),o=r!==null,s=po(r,a);n.hidden=!o,n.disabled=El()||!s,n.dataset.aqeButtonState=s?"default":"unavailable",n.title=s?"Delete selected region":"Cannot delete the whole audio clip",n.setAttribute("aria-disabled",n.disabled?"true":"false")}function Nl(){Tr().forEach(yn)}function _o(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=Number(e.dataset.durationMs||"0")||0,a=gn(e);if(!a||!po(a,r))return a&&ho(a,r)&&ce.warn("region delete rejected whole clip",{ord:n,sourceFilename:e.dataset.sourceFilename||"",selectionStartMs:a.startMs,selectionEndMs:a.endMs,durationMs:r,trigger:t}),null;const o=e.dataset.sourceFilename||"";if(!o)return null;const s=e.dataset.playbackState;return{ord:n,sourceFilename:o,selectionStartMs:Math.round(a.startMs),selectionEndMs:Math.round(a.endMs),cursorMs:Math.round(Number(e.dataset.cursorMs||"0")||0),durationMs:Math.round(r),trigger:t,playbackActive:Lr(s)&&s!=="stopped"}}function Fl(e,t,n,r,a){e.preventDefault();const o=a.playbackStateFor(t),s=t.querySelector(".aqe-visualizer-svg"),i=Number(t.dataset.durationMs||"0");if(!s||!i)return;o==="playing"&&a.stopProgressClock(t);const l=f=>{a.setCursor(t,mo(f,s,i,t,a),!1)},c=f=>{window.removeEventListener("pointermove",l),window.removeEventListener("pointerup",c);const u=o==="playing";o==="paused"&&(t.dataset.resumeRequiresRestart="true");const h=mo(f,s,i,t,a),m=u&&a.audioClockReady(t)?"html":"";a.setCursor(t,h,r,{previousPlaybackState:o,restartPlayback:u,engine:m}),a.audioClockReady(t)&&a.seekAudioClock(t,h),u&&m==="html"&&a.startEditorHtmlPlayback(t,a.playbackRequestForStart(t,n,h,"html"))};l(e),window.addEventListener("pointermove",l),window.addEventListener("pointerup",c)}function Cl(e,t,n,r){e.preventDefault();const a=t.querySelector(".aqe-visualizer-svg"),o=Number(t.dataset.durationMs||"0");if(!a||!o)return;const s=r.playbackStateFor(t),i=r.currentProgressMs(t)??Number(t.dataset.cursorMs||"0"),l={clientX:e.clientX},c=vn(e,a,o);let f=!1,u=A=>{},h=A=>{},m=()=>{},_=A=>{};const w=()=>{window.removeEventListener("pointermove",u),window.removeEventListener("pointerup",h),window.removeEventListener("pointercancel",m),window.removeEventListener("keydown",_),window.removeEventListener("blur",m),a.removeEventListener("lostpointercapture",m)},p=()=>{f||s!=="playing"||(f=!0,r.stopProgressClock(t,{clearEngine:!1}),r.setCursor(t,i,!1,{updateAnchor:!1}))},v=()=>{s==="playing"&&f&&r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,i,"html"))};u=A=>{const b=vn(A,a,o);if(ao(l,A,c,b)){r.clearSelectionDraft(t);return}p(),r.setSelectionDraft(t,c,b)},h=A=>{w();const b=vn(A,a,o);if(ao(l,A,c,b)){r.clearSelection(t),v();return}p(),r.draftSelectionForVisualizer(t)||r.setSelectionDraft(t,c,b,{redraw:!1});const S=r.commitSelectionDraft(t);if(s==="paused"&&(t.dataset.resumeRequiresRestart="true"),S&&s==="playing"){const E=r.selectionForVisualizer(t);r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,(E==null?void 0:E.startMs)??c,"html"))}},m=()=>{w(),r.clearSelectionDraft(t),v()},_=A=>{A.key==="Escape"&&m()},window.addEventListener("pointermove",u),window.addEventListener("pointerup",h),window.addEventListener("pointercancel",m),window.addEventListener("keydown",_),window.addEventListener("blur",m),a.addEventListener("lostpointercapture",m)}function Rl(e,t,n){const r=n.visualizerForOrd(t);if(r){if(e.shiftKey){Cl(e,r,t,n);return}Fl(e,r,t,!0,n)}}function mo(e,t,n,r,a){const o=vn(e,t,n),s=a.selectionForVisualizer(r);return s&&r.dataset.repeatEnabled==="true"?tl(o,s):o}function wt(e){e.__aqePlaybackTimer&&(window.cancelAnimationFrame(e.__aqePlaybackTimer),e.__aqePlaybackTimer=null)}function vo(e){const t=Number(e.dataset.durationMs||"0"),n=performance.now()-Number(e.dataset.playStartedAt||"0");return Math.min(t,Number(e.dataset.playStartMs||"0")+n)}function go(e){const t=Pe(e);if(!t)return null;const n=Number(e.dataset.durationMs||"0");return Math.min(n,(Number(t.currentTime)||0)*1e3)}function yo(e){return e.dataset.progressClockMode==="audio"?go(e):e.dataset.progressClockMode==="manual"?vo(e):Number(e.dataset.progressMs||e.dataset.cursorMs||"0")}function Gr(e,t,n,r={}){return t<$l(e,n)?!1:n.repeatEnabledFor(e)?(Ll(e,n,r),!0):(xl(e,n),!0)}function xl(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=t.effectivePlaybackRegion(e),a=e.dataset.playbackRegionMode==="selection"?r.startMs:Number(e.dataset.anchorMs||"0");Hr(e,t),t.setCursor(e,a,!1,{updateAnchor:!1}),nr(e)&&rr(e,a,Number(e.dataset.durationMs||"0")),t.clearStatus(n),window.__aqeActiveField=n,t.focusAndSendCommand(n,"aqe:play-ended")}function Vr(e,t){const n=()=>{if(e.dataset.playbackState!=="playing")return;const r=go(e);if(r===null){Ye(e,Number(e.dataset.cursorMs||"0"),t);return}t.setCursor(e,r,!1,{updateAnchor:!1}),!Gr(e,r,t)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(n))};e.__aqePlaybackTimer=window.requestAnimationFrame(n)}function Ye(e,t,n){if(wt(e),pn(e),!Number(e.dataset.durationMs||"0"))return;const a=bo(e,t);e.__aqeAudioClockFallback=!0,e.dataset.playbackState="playing",e.dataset.progressClockMode="manual",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),Wr(e,a,n),n.setPlaybackButtonLabel(e,"Pause");const o=()=>{if(e.dataset.playbackState!=="playing")return;const s=vo(e);n.setCursor(e,s,!1,{updateAnchor:!1}),!Gr(e,s,n)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(o))};e.__aqePlaybackTimer=window.requestAnimationFrame(o)}function Tl(e,t,n,r={}){var i;const a=Pe(e);if(!a||!rr(e,t,Number(e.dataset.durationMs||"0"))||typeof a.play!="function"){if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}Ye(e,t,n);return}e.dataset.progressClockMode="audio",e.__aqeAudioClockFallback=!1;const o=()=>{var l;if(r.manualFallback===!1){(l=r.onAudioPlayFailed)==null||l.call(r);return}Ye(e,t,n)},s=()=>{var l;e.dataset.playbackState==="playing"&&(wt(e),e.dataset.progressClockMode="audio",ce.info("html audio playback started",{ord:e.dataset.aqeFieldOrd}),Vr(e,n),(l=r.onAudioStarted)==null||l.call(r))};Promise.resolve(a.play()).then(s).catch(()=>{e.dataset.playbackState==="playing"&&(ce.warn("html audio play rejected; using manual clock",{ord:e.dataset.aqeFieldOrd}),o())})}function Dl(e,t,n,r={}){var i;const a=r.engine||e.dataset.playbackEngine||"";if(Hr(e,n,{clearEngine:!1}),n.stopOtherPlayback(e),!Number(e.dataset.durationMs||"0"))return;const s=bo(e,t);if(e.dataset.playbackEngine=a,e.dataset.playbackState="playing",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(s),Wr(e,s,n),n.setCursor(e,s,!1,{updateAnchor:!1}),n.setPlaybackButtonLabel(e,"Pause"),ce.info("playback clock selected",{engine:a||"auto",startMs:s}),a==="native"){Ye(e,s,n);return}if(nr(e)){Tl(e,s,n,r);return}if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}Ye(e,s,n)}function Ol(e,t){const n=yo(e);n!==null&&t.setCursor(e,n,!1,{updateAnchor:!1}),wt(e),pn(e),e.dataset.playbackState="paused",e.dataset.progressClockMode="stopped",t.setPlaybackButtonLabel(e,"Play")}function Hr(e,t,n={}){wt(e),pn(e),e.dataset.playbackState="stopped",e.dataset.progressClockMode="stopped",e.dataset.resumeRequiresRestart="false",n.clearEngine!==!1&&(e.dataset.playbackEngine=""),n.clearAudio&&Or(e),t.setPlaybackButtonLabel(e,"Play")}function Wr(e,t,n,r=n.effectivePlaybackRegion(e)){e.dataset.playbackStartMs=String(Math.round(t)),e.dataset.playbackEndMs=String(Math.round(r.endMs)),e.dataset.playbackRegionMode=r.mode}function $l(e,t){const n=t.effectivePlaybackRegion(e),r=Number(e.dataset.playbackEndMs||"0")||n.endMs;return Math.max(n.startMs,Math.min(r,Number(e.dataset.durationMs||"0")||0))}function Ll(e,t,n={}){const r=t.effectivePlaybackRegion(e),a=r.startMs;if(Wr(e,a,t,r),e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),t.setCursor(e,a,!1,{updateAnchor:!1}),e.dataset.progressClockMode!=="audio"||!nr(e)){Ye(e,a,t);return}if(!rr(e,a,Number(e.dataset.durationMs||"0"))){Ye(e,a,t);return}if(!n.forceAudioPlay){wt(e),Vr(e,t);return}const o=Pe(e);!o||typeof o.play!="function"||(wt(e),Promise.resolve(o.play()).then(()=>{e.dataset.playbackState==="playing"&&Vr(e,t)}).catch(()=>{e.dataset.playbackState==="playing"&&Ye(e,a,t)}))}function bo(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function wo(){return document.body.dataset.aqeBusy==="true"}function qo(){var e;return((e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.repeatPlaybackByDefault)===!0}function Il(e){for(const t of Tr())t!==e&&Wt(t)!=="stopped"&&st(t)}function Bl(){for(const e of Tr())Wt(e)!=="stopped"&&st(e)}function Vt(e,t,n="",r=""){document.body.dataset.aqeBusy=t?"true":"false",document.querySelectorAll(".aqe-controls").forEach(s=>{s.dataset.busy=t?"true":"false"}),Jn().forEach(s=>{s.disabled=!!t}),Nl(),t||queueMicrotask(()=>lr(Zr()));const a=Xe(e),o=a==null?void 0:a.querySelector(".aqe-status");o&&(o.textContent=n||"",o.dataset.kind=t?"processing":"info",o.title=r||"")}function Mo(e,t="info"){const n=Number(window.__aqeActiveField??0),r=Xe(n),a=r==null?void 0:r.querySelector(".aqe-status");a&&(a.textContent=e||"",a.dataset.kind=t||"info")}function Gl(e){const t=Xe(e),n=t==null?void 0:t.querySelector(".aqe-status");n&&(n.textContent="",n.dataset.kind="info",n.title="")}function Ht(e,t,n){var o;const r=t==="aqe:play"?Xa(e):t==="aqe:analyze"?Ka(e):((o=Xe(e))==null?void 0:o.querySelector(`[data-aqe-command="${t}"]`))??null;if(!r)return;const a=r.querySelector(".aqe-button-label");if(a?a.textContent=n:r.textContent=n,t==="aqe:play"&&(r.dataset.aqeButtonState=n==="Pause"?"pause":"play"),t==="aqe:analyze"){r.dataset.aqeButtonState=n==="Redraw"?"redraw":"graph";const s=n==="Redraw"?"Redraw the pitch graph":"Analyze and show pitch/intensity graph";r.title=s,r.setAttribute("aria-label",s)}}function So(e,t,n){if(!wo()){if(typeof t.focus=="function"&&t.focus(),window.__aqeActiveField=n,ce.info("command dispatched",{command:e,ord:n}),e==="aqe:analyze"){Po(n,!0);return}e==="aqe:play"&&uu(n)||(z.has(e)&&(Bl(),Vt(n,!0,ja(e))),Bt(n,e))}}function Vl(e){Dr(e)}function Hl(e){wt(e)}function Wl(e){Or(e)}function jl(e,t){Vi(e,t)}function Ul(e){Hi(e,{onErrorDuringPlayback(){ce.warn("audio clock failed during playback",{ord:e.dataset.aqeFieldOrd}),lu(e,Number(e.dataset.cursorMs||"0"))},onEndedDuringPlayback(){iu(e,Number(e.dataset.durationMs||"0"),{forceAudioPlay:!0})}})}function jr(e){return nr(e)}function Kl(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function ko(e){return gn(e)}function Ao(e){return Br(e)}function Ur(e){return co(e)}function Kr(e,t){e.dataset.repeatEnabled=t?"true":"false";const n=Number(e.dataset.aqeFieldOrd||"0"),r=Ya(n);r&&(r.ariaPressed=t?"true":"false",r.dataset.aqeButtonState=t?"active":"default")}function Xl(e,t){const n=$(e);return n?(Kr(n,t),!0):!1}function Yl(e,t={}){Gt(e,t)}function Ql(e,t,n,r={}){return Sl(e,t,n,r)}function Zl(e,t={}){const n=kl(e,eu(),t);return yn(e),n}function bn(e,t={}){fo(e,t),yn(e)}function Jl(e){e.dataset.playbackStartMs="0",e.dataset.playbackEndMs=String(Number(e.dataset.durationMs||"0")||0),e.dataset.playbackRegionMode="full",Kr(e,qo()),bn(e,{resetPlaybackRegion:!1})}function zl(){return{audioClockReady:jr,clearSelection:bn,clearSelectionDraft:Yl,commitSelectionDraft:Zl,currentProgressMs:Ro,draftSelectionForVisualizer:Ao,playbackRequestForStart:tu,playbackStateFor:Wt,seekAudioClock:Eo,selectionForVisualizer:ko,setCursor:qt,setSelectionDraft:Ql,startEditorHtmlPlayback:Oo,stopProgressClock:st,visualizerForOrd:$}}function eu(){return{setCursor:qt}}function Xr(e){return e.dataset.repeatEnabled==="true"}function wn(){return{clearStatus:Gl,effectivePlaybackRegion:Ur,focusAndSendCommand:Bt,playbackEngineFor:qn,repeatEnabledFor:Xr,setCursor:qt,setPlaybackButtonLabel:su,stopOtherPlayback:Il}}function tu(e,t,n,r=qn(e)){const a=Ur(e);return{ord:t,action:"start",cursorMs:Math.round(Kl(e,n)),endMs:Math.round(a.endMs),engine:r,loop:Xr(e),regionMode:a.mode}}function Eo(e,t){return rr(e,t,Number(e.dataset.durationMs||"0"))}function qt(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Math.max(0,Math.min(Number(t)||0,a||0));if(e.dataset.cursorMs=String(Math.round(o)),e.dataset.progressMs=String(Math.round(o)),r.updateAnchor!==!1&&(e.dataset.anchorMs=String(Math.round(o))),wl(e,o,a),n){window.__aqeActiveField=Number(e.dataset.aqeFieldOrd||"0");const s={cursorMs:Math.round(o),previousPlaybackState:r.previousPlaybackState||Wt(e),restartPlayback:!!r.restartPlayback};r.engine&&(s.engine=r.engine),Bi(s),ce.info("cursor committed",s),Bt(window.__aqeActiveField,"aqe:set-cursor")}}function nu(e,t){var n;(n=$(t))==null||n.focus(),Rl(e,t,zl())}function Po(e,t){Fo(e)&&(window.__aqeActiveField=e,ce.info("graph requested",{notifyPython:t,ord:e}),Vt(e,!0,"Analyzing...",""),Bt(e,"aqe:analyze"))}function No(e){Fo(e.ord)&&(ce.info("default graph requested",e),Vt(e.ord,!0,"Analyzing...",""),Ri(e))}function Fo(e){const t=$(e);return t?(st(t,{clearAudio:!0}),vl(t),bn(t),qt(t,0,!1),Ht(e,"aqe:analyze","Redraw"),Qr(e,"Analyzing...","processing"),!0):!1}function ru(e){return window.__aqePendingGraphRedrawField=e,Yr()}function Yr(){const e=window.__aqePendingGraphRedrawField;if(typeof e!="number")return!1;const t=$(e);return t?(t.dataset.graphBusy==="true"||t.dataset.hasTrack==="true"||Po(e,!0),!0):!1}function Qr(e,t,n="info"){const r=$(e);r&&yl(r,t,n)}function au(e,t,n){const r=$(e);if(!r||!t)return;const a=rl(t);gl(r,a),r.dataset.anchorMs=String(n||0),window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null),bn(r),r.dataset.playbackStartMs="0",r.dataset.playbackEndMs=String(a.durationMs||0),r.dataset.playbackRegionMode="full",jl(r,a.sourceFilename||""),Ht(e,"aqe:analyze","Redraw"),qt(r,n||0,!1),jr(r)&&Eo(r,n||0),Qr(e,a.analyzerName||"","info"),Vt(e,!1,"",""),Za(e,Zr()),ce.info("graph rendered",Ml(e,a))}function ou(e,t,n="info"){n!=="processing"&&window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null);const r=$(e);r&&(r.hidden=!1,r.dataset.graphActive="true",n==="processing"&&(r.dataset.hasTrack="false"),Ht(e,"aqe:analyze","Redraw")),Qr(e,t,n),n!=="processing"&&Za(e,Zr())}function Zr(){return{anyBusy:wo,requestDefaultGraph:No}}function Co(){document.body.dataset.aqeBusy="false",window.__aqeActiveField=null,window.__aqeLastCursorIntent=null,document.querySelectorAll(".aqe-controls").forEach(e=>{e.dataset.busy="false",e.dataset.aqeSourceFilename="",e.querySelectorAll(".aqe-button").forEach(o=>{o.disabled=!1,o.dataset.aqeCommand==="aqe:analyze"&&Ht(Number(e.dataset.aqeFieldOrd||"0"),"aqe:analyze","Graph"),o.dataset.aqeCommand==="aqe:play"&&Ht(Number(e.dataset.aqeFieldOrd||"0"),"aqe:play","Play")});const t=e.querySelector(".aqe-status");t&&(t.textContent="",t.dataset.kind="info",t.title="");const n=e.querySelector(".aqe-visualizer");if(!n)return;Hl(n),Wl(n),n.hidden=!0,n.dataset.anchorMs="0",n.dataset.cursorMs="0",n.dataset.progressMs="0",n.dataset.graphActive="false",n.dataset.graphBusy="false",n.dataset.hasTrack="false",n.dataset.playbackState="stopped",n.dataset.playbackEngine="",n.dataset.resumeRequiresRestart="false",n.dataset.durationMs="0",n.dataset.sourceFilename="",n.dataset.analyzerName="",n.dataset.playStartedAt="0",n.dataset.playStartMs="0",n.dataset.playbackStartMs="0",n.dataset.playbackEndMs="0",n.dataset.playbackRegionMode="full",n.dataset.progressClockMode="stopped",Kr(n,qo()),bn(n),uo(n),ql(n);const r=n.querySelector(".aqe-visualizer-status");r&&(r.textContent="",r.dataset.kind="info");const a=n.querySelector(".aqe-spinner");a&&(a.hidden=!0)})}function su(e,t){const n=Number(e.dataset.aqeFieldOrd||"0");Ht(n,"aqe:play",t)}function Ro(e){return yo(e)}function iu(e,t,n={}){return Gr(e,t,wn(),n)}function lu(e,t){Ye(e,t,wn())}function xo(e,t,n={}){Dl(e,t,wn(),n)}function To(e){Ol(e,wn())}function st(e,t={}){Hr(e,wn(),t)}function Do(e){const t=$(e);return t?nl({anchorMs:Number(t.dataset.anchorMs||t.dataset.cursorMs||"0"),currentProgressMs:Ro(t),cursorMs:Number(t.dataset.cursorMs||"0"),engine:qn(t),ord:e,playbackState:Wt(t),region:Ur(t),repeat:Xr(t),resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true"}):{ord:e,action:"start",cursorMs:0}}function qn(e){if(!e||e.dataset.hasTrack!=="true")return"native";const t=e.dataset.playbackEngine||"";return e.dataset.playbackState!=="stopped"&&(t==="html"||t==="native")?t:jr(e)?"html":"native"}function Jr(e){const t=$(e.ord);t&&(t.dataset.playbackEngine=e.engine||""),Di(e),window.__aqeActiveField=e.ord,ce.info("playback request queued",e),Bt(e.ord,"aqe:play")}function Oo(e,t){return xo(e,t.cursorMs,{engine:"html",manualFallback:!1,onAudioStarted(){Jr(t)},onAudioPlayFailed(){if(ce.warn("html playback failed; falling back to native",{ord:t.ord}),st(e),t.regionMode==="selection"||t.loop){window.__aqeActiveField=t.ord,Mo("Selected repeat playback needs browser audio.","warning");return}Jr({...t,engine:"native"})}}),!0}function uu(e){const t=$(e);if(!t||qn(t)!=="html")return!1;const n={...Do(e),engine:"html"};return n.action==="pause"?(To(t),n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0"),Jr(n),!0):(n.action==="resume"&&(n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0")),Oo(t,n))}function cu(e,t,n){const r=$(e);r&&((t==="playing"||t==="paused")&&(r.dataset.resumeRequiresRestart="false"),t==="playing"?xo(r,n,{engine:r.dataset.playbackEngine==="html"||r.dataset.playbackEngine==="native"?r.dataset.playbackEngine:""}):t==="paused"?To(r):st(r))}function fu(){const e=Oi();if(e)return e;const t=Number(window.__aqeActiveField||"0"),n=Do(t),r=$(t);return r&&(r.dataset.playbackEngine=n.engine||""),n}function du(e){const t=$(e);return t?(st(t),!0):!1}function hu(){const e=Number(window.__aqeActiveField||"0"),t=$(e);return t?Number(t.dataset.cursorMs||"0"):0}function pu(){const e=Number(window.__aqeActiveField||"0"),t=$(e),n=t?Number(t.dataset.cursorMs||"0"):0;return window.__aqeLastCursorIntent||{cursorMs:n,previousPlaybackState:t?Wt(t):"stopped",restartPlayback:!1}}function Wt(e){const t=e.dataset.playbackState;return Lr(t)?t:"stopped"}const $o=(ui=(li=globalThis.process)==null?void 0:li.env)==null?void 0:ui.NODE_ENV,g=$o&&!$o.toLowerCase().startsWith("prod");var zr=Array.isArray,_u=Array.prototype.indexOf,Mt=Array.prototype.includes,fr=Array.from,St=Object.defineProperty,Qe=Object.getOwnPropertyDescriptor,mu=Object.getOwnPropertyDescriptors,vu=Object.prototype,gu=Array.prototype,Lo=Object.getPrototypeOf,Io=Object.isExtensible;function Mn(e){return typeof e=="function"}const V=()=>{};function yu(e){for(var t=0;t<e.length;t++)e[t]()}function Bo(){var e,t,n=new Promise((r,a)=>{e=r,t=a});return{promise:n,resolve:e,reject:t}}function bu(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const r of e)if(n.push(r),n.length===t)break;return n}const oe=2,Sn=4,dr=8,ea=1<<24,Ze=16,Ne=32,kt=64,ta=128,qe=512,te=1024,se=2048,Fe=4096,me=8192,Je=16384,At=32768,it=65536,hr=1<<17,Go=1<<18,jt=1<<19,wu=1<<20,ze=1<<25,lt=65536,na=1<<21,pr=1<<22,ut=1<<23,ct=Symbol("$state"),Vo=Symbol("legacy props"),qu=Symbol(""),Ho=Symbol("proxy path"),Et=new class extends Error{constructor(){super(...arguments);Ke(this,"name","StaleReactionError");Ke(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}},Wo=!!((ci=globalThis.document)!=null&&ci.contentType)&&globalThis.document.contentType.includes("xml");function jo(e){if(g){const t=new Error(`lifecycle_outside_component
\`${e}(...)\` can only be used during component initialisation
https://svelte.dev/e/lifecycle_outside_component`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/lifecycle_outside_component")}function Mu(){if(g){const e=new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/async_derived_orphan")}function Su(){if(g){const e=new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/derived_references_self")}function Uo(e,t,n){if(g){const r=new Error(`each_key_duplicate
${n?`Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}`:`Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_duplicate")}function ku(e,t,n){if(g){const r=new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_volatile")}function Au(e){if(g){const t=new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_in_teardown")}function Eu(){if(g){const e=new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Pu(e){if(g){const t=new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_orphan")}function Nu(){if(g){const e=new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Fu(){if(g){const e=new Error("invalid_snippet\nCould not `{@render}` snippet due to the expression being `null` or `undefined`. Consider using optional chaining `{@render snippet?.()}`\nhttps://svelte.dev/e/invalid_snippet");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/invalid_snippet")}function Cu(e){if(g){const t=new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_invalid_value")}function Ru(e){if(g){const t=new Error(`props_rest_readonly
Rest element properties of \`$props()\` such as \`${e}\` are readonly
https://svelte.dev/e/props_rest_readonly`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_rest_readonly")}function xu(e){if(g){const t=new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/rune_outside_svelte")}function Tu(){if(g){const e=new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function Du(){if(g){const e=new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Ou(){if(g){const e=new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function $u(){if(g){const e=new Error("svelte_boundary_reset_onerror\nA `<svelte:boundary>` `reset` function cannot be called while an error is still being handled\nhttps://svelte.dev/e/svelte_boundary_reset_onerror");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Lu=1,Iu=2,Ko=4,Bu=8,Gu=16,Vu=1,Hu=4,Wu=8,ju=16,Uu=1,Ku=2,ne=Symbol(),Xu=Symbol("filename"),Xo="http://www.w3.org/1999/xhtml",Yu="http://www.w3.org/2000/svg",Qu="@attach";var kn="font-weight: bold",An="font-weight: normal";function Zu(){g?console.warn(`%c[svelte] lifecycle_double_unmount
%cTried to unmount a component that was not mounted
https://svelte.dev/e/lifecycle_double_unmount`,kn,An):console.warn("https://svelte.dev/e/lifecycle_double_unmount")}function Ju(){g?console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value",kn,An):console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function ra(e){g?console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`,kn,An):console.warn("https://svelte.dev/e/state_proxy_equality_mismatch")}function zu(){g?console.warn(`%c[svelte] state_proxy_unmount
%cTried to unmount a state proxy, rather than a component
https://svelte.dev/e/state_proxy_unmount`,kn,An):console.warn("https://svelte.dev/e/state_proxy_unmount")}function ec(){g?console.warn("%c[svelte] svelte_boundary_reset_noop\n%cA `<svelte:boundary>` `reset` function only resets the boundary the first time it is called\nhttps://svelte.dev/e/svelte_boundary_reset_noop",kn,An):console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Yo(e){return e===this.v}function tc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Qo(e){return!tc(e,this.v)}let nc=!1;function Be(e,t){return e.label=t,Zo(e.v,t),e}function Zo(e,t){var n;return(n=e==null?void 0:e[Ho])==null||n.call(e,t),e}function rc(e){const t=new Error,n=ac();return n.length===0?null:(n.unshift(`
`),St(t,"stack",{value:n.join(`
`)}),St(t,"name",{value:e}),t)}function ac(){const e=Error.stackTraceLimit;Error.stackTraceLimit=1/0;const t=new Error().stack;if(Error.stackTraceLimit=e,!t)return[];const n=t.split(`
`),r=[];for(let a=0;a<n.length;a++){const o=n[a],s=o.replaceAll("\\","/");if(o.trim()!=="Error"){if(o.includes("validate_each_keys"))return[];s.includes("svelte/src/internal")||s.includes("node_modules/.vite")||r.push(o)}}return r}let K=null;function Ut(e){K=e}let Kt=null;function _r(e){Kt=e}let En=null;function Jo(e){En=e}function oc(e){return sc("getContext").get(e)}function L(e,t=!1,n){K={p:K,i:!1,c:null,e:null,s:e,x:null,l:null},g&&(K.function=n,En=n)}function I(e){var t=K,n=t.e;if(n!==null){t.e=null;for(var r of n)ws(r)}return t.i=!0,K=t.p,g&&(En=(K==null?void 0:K.function)??null),{}}function zo(){return!0}function sc(e){return K===null&&jo(e),K.c??(K.c=new Map(ic(K)||void 0))}function ic(e){let t=e.p;for(;t!==null;){const n=t.c;if(n!==null)return n;t=t.p}return null}let Xt=[];function lc(){var e=Xt;Xt=[],yu(e)}function et(e){if(Xt.length===0){var t=Xt;queueMicrotask(()=>{t===Xt&&lc()})}Xt.push(e)}const aa=new WeakMap;function es(e){var t=x;if(t===null)return C.f|=ut,e;if(g&&e instanceof Error&&!aa.has(e)&&aa.set(e,uc(e,t)),(t.f&At)===0&&(t.f&Sn)===0)throw g&&!t.parent&&e instanceof Error&&ts(e),e;ft(e,t)}function ft(e,t){for(;t!==null;){if((t.f&ta)!==0){if((t.f&At)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw g&&e instanceof Error&&ts(e),e}function uc(e,t){var s,i,l;const n=Qe(e,"message");if(!(n&&!n.configurable)){for(var r=ha?"  ":"	",a=`
${r}in ${((s=t.fn)==null?void 0:s.name)||"<unknown>"}`,o=t.ctx;o!==null;)a+=`
${r}in ${(i=o.function)==null?void 0:i[Xu].split("/").pop()}`,o=o.p;return{message:e.message+`
${a}
`,stack:(l=e.stack)==null?void 0:l.split(`
`).filter(c=>!c.includes("svelte/src/internal")).join(`
`)}}}function ts(e){const t=aa.get(e);t&&(St(e,"message",{value:t.message}),St(e,"stack",{value:t.stack}))}const cc=-7169;function J(e,t){e.f=e.f&cc|t}function oa(e){(e.f&qe)!==0||e.deps===null?J(e,te):J(e,Fe)}function ns(e){if(e!==null)for(const t of e)(t.f&oe)===0||(t.f&lt)===0||(t.f^=lt,ns(t.deps))}function rs(e,t,n){(e.f&se)!==0?t.add(e):(e.f&Fe)!==0&&n.add(e),ns(e.deps),J(e,te)}const mr=new Set;let D=null,ie=null,Me=[],sa=null,ia=!1;const Da=class Da{constructor(){R(this,ge);Ke(this,"current",new Map);Ke(this,"previous",new Map);R(this,an,new Set);R(this,on,new Set);R(this,Tt,0);R(this,sn,0);R(this,Bn,null);R(this,Gn,new Set);R(this,Dt,new Set);R(this,nt,new Map);Ke(this,"is_fork",!1);R(this,ln,!1)}skip_effect(t){d(this,nt).has(t)||d(this,nt).set(t,{d:[],m:[]})}unskip_effect(t){var n=d(this,nt).get(t);if(n){d(this,nt).delete(t);for(var r of n.d)J(r,se),Re(r);for(r of n.m)J(r,Fe),Re(r)}}process(t){var a;Me=[],this.apply();var n=[],r=[];for(const o of t)ae(this,ge,Ga).call(this,o,n,r);if(ae(this,ge,Ba).call(this)){ae(this,ge,Va).call(this,r),ae(this,ge,Va).call(this,n);for(const[o,s]of d(this,nt))is(o,s)}else{for(const o of d(this,an))o();d(this,an).clear(),d(this,Tt)===0&&ae(this,ge,Ci).call(this),D=null,as(r),as(n),(a=d(this,Bn))==null||a.resolve()}ie=null}capture(t,n){n!==ne&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&ut)===0&&(this.current.set(t,t.v),ie==null||ie.set(t,t.v))}activate(){D=this,this.apply()}deactivate(){D===this&&(D=null,ie=null)}flush(){if(this.activate(),Me.length>0){if(fc(),D!==null&&D!==this)return}else d(this,Tt)===0&&this.process([]);this.deactivate()}discard(){for(const t of d(this,on))t(this);d(this,on).clear()}increment(t){F(this,Tt,d(this,Tt)+1),t&&F(this,sn,d(this,sn)+1)}decrement(t){F(this,Tt,d(this,Tt)-1),t&&F(this,sn,d(this,sn)-1),!d(this,ln)&&(F(this,ln,!0),et(()=>{F(this,ln,!1),ae(this,ge,Ba).call(this)?Me.length>0&&this.flush():this.revive()}))}revive(){for(const t of d(this,Gn))d(this,Dt).delete(t),J(t,se),Re(t);for(const t of d(this,Dt))J(t,Fe),Re(t);this.flush()}oncommit(t){d(this,an).add(t)}ondiscard(t){d(this,on).add(t)}settled(){return(d(this,Bn)??F(this,Bn,Bo())).promise}static ensure(){if(D===null){const t=D=new Da;mr.add(D),et(()=>{D===t&&t.flush()})}return D}apply(){}};an=new WeakMap,on=new WeakMap,Tt=new WeakMap,sn=new WeakMap,Bn=new WeakMap,Gn=new WeakMap,Dt=new WeakMap,nt=new WeakMap,ln=new WeakMap,ge=new WeakSet,Ba=function(){return this.is_fork||d(this,sn)>0},Ga=function(t,n,r){t.f^=te;for(var a=t.first;a!==null;){var o=a.f,s=(o&(Ne|kt))!==0,i=s&&(o&te)!==0,l=i||(o&me)!==0||d(this,nt).has(a);if(!l&&a.fn!==null){s?a.f^=te:(o&Sn)!==0?n.push(a):Rn(a)&&((o&Ze)!==0&&d(this,Dt).add(a),en(a));var c=a.first;if(c!==null){a=c;continue}}for(;a!==null;){var f=a.next;if(f!==null){a=f;break}a=a.parent}}},Va=function(t){for(var n=0;n<t.length;n+=1)rs(t[n],d(this,Gn),d(this,Dt))},Ci=function(){var a;if(mr.size>1){this.previous.clear();var t=ie,n=!0;for(const o of mr){if(o===this){n=!1;continue}const s=[];for(const[l,c]of this.current){if(o.current.has(l))if(n&&c!==o.current.get(l))o.current.set(l,c);else continue;s.push(l)}if(s.length===0)continue;const i=[...o.current.keys()].filter(l=>!this.current.has(l));if(i.length>0){var r=Me;Me=[];const l=new Set,c=new Map;for(const f of s)os(f,i,l,c);if(Me.length>0){D=o,o.apply();for(const f of Me)ae(a=o,ge,Ga).call(a,f,[],[]);o.deactivate()}Me=r}}D=null,ie=t}mr.delete(this)};let dt=Da;function fc(){ia=!0;var e=g?new Set:null;try{for(var t=0;Me.length>0;){var n=dt.ensure();if(t++>1e3){if(g){var r=new Map;for(const o of n.current.keys())for(const[s,i]of o.updated??[]){var a=r.get(s);a||(a={error:i.error,count:0},r.set(s,a)),a.count+=i.count}for(const o of r.values())o.error&&console.error(o.error)}dc()}if(n.process(Me),ht.clear(),g)for(const o of n.current.keys())e.add(o)}}finally{if(Me=[],ia=!1,sa=null,g)for(const o of e)o.updated=null}}function dc(){try{Nu()}catch(e){g&&St(e,"stack",{value:""}),ft(e,sa)}}let Ce=null;function as(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var r=e[n++];if((r.f&(Je|me))===0&&Rn(r)&&(Ce=new Set,en(r),r.deps===null&&r.first===null&&r.nodes===null&&r.teardown===null&&r.ac===null&&ks(r),(Ce==null?void 0:Ce.size)>0)){ht.clear();for(const a of Ce){if((a.f&(Je|me))!==0)continue;const o=[a];let s=a.parent;for(;s!==null;)Ce.has(s)&&(Ce.delete(s),o.push(s)),s=s.parent;for(let i=o.length-1;i>=0;i--){const l=o[i];(l.f&(Je|me))===0&&en(l)}}Ce.clear()}}Ce=null}}function os(e,t,n,r){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const a of e.reactions){const o=a.f;(o&oe)!==0?os(a,t,n,r):(o&(pr|Ze))!==0&&(o&se)===0&&ss(a,t,r)&&(J(a,se),Re(a))}}function ss(e,t,n){const r=n.get(e);if(r!==void 0)return r;if(e.deps!==null)for(const a of e.deps){if(Mt.call(t,a))return!0;if((a.f&oe)!==0&&ss(a,t,n))return n.set(a,!0),!0}return n.set(e,!1),!1}function Re(e){var t=sa=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(Sn|dr|ea))!==0&&(e.f&At)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var r=t.f;if(ia&&t===x&&(r&Ze)!==0&&(r&Go)===0&&(r&At)!==0)return;if((r&(kt|Ne))!==0){if((r&te)===0)return;t.f^=te}}Me.push(t)}function is(e,t){if(!((e.f&Ne)!==0&&(e.f&te)!==0)){(e.f&se)!==0?t.d.push(e):(e.f&Fe)!==0&&t.m.push(e),J(e,te);for(var n=e.first;n!==null;)is(n,t),n=n.next}}function hc(e){let t=0,n=Pt(0),r;return g&&Be(n,"createSubscriber version"),()=>{_a()&&(P(n),Lc(()=>(t===0&&(r=ba(()=>e(()=>Pn(n)))),t+=1,()=>{et(()=>{t-=1,t===0&&(r==null||r(),r=void 0,Pn(n))})})))}}var pc=it|jt;function _c(e,t,n,r){new mc(e,t,n,r)}class mc{constructor(t,n,r,a){R(this,ee);Ke(this,"parent");Ke(this,"is_pending",!1);Ke(this,"transform_error");R(this,Ee);R(this,Oa,null);R(this,Ve);R(this,Ot);R(this,_e);R(this,He,null);R(this,ye,null);R(this,Oe,null);R(this,rt,null);R(this,$t,0);R(this,gt,0);R(this,un,!1);R(this,cn,new Set);R(this,fn,new Set);R(this,We,null);R(this,qr,hc(()=>(F(this,We,Pt(d(this,$t))),g&&Be(d(this,We),"$effect.pending()"),()=>{F(this,We,null)})));var o;F(this,Ee,t),F(this,Ve,n),F(this,Ot,s=>{var i=x;i.b=this,i.f|=ta,r(s)}),this.parent=x.b,this.transform_error=a??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),F(this,_e,Cn(()=>{ae(this,ee,Ha).call(this)},pc))}defer_effect(t){rs(t,d(this,cn),d(this,fn))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!d(this,Ve).pending}update_pending_count(t){ae(this,ee,Wa).call(this,t),F(this,$t,d(this,$t)+t),!(!d(this,We)||d(this,un))&&(F(this,un,!0),et(()=>{F(this,un,!1),d(this,We)&&Qt(d(this,We),d(this,$t))}))}get_effect_pending(){return d(this,qr).call(this),P(d(this,We))}error(t){var n=d(this,Ve).onerror;let r=d(this,Ve).failed;if(!n&&!r)throw t;d(this,He)&&(le(d(this,He)),F(this,He,null)),d(this,ye)&&(le(d(this,ye)),F(this,ye,null)),d(this,Oe)&&(le(d(this,Oe)),F(this,Oe,null));var a=!1,o=!1;const s=()=>{if(a){ec();return}a=!0,o&&$u(),d(this,Oe)!==null&&Ft(d(this,Oe),()=>{F(this,Oe,null)}),ae(this,ee,Rr).call(this,()=>{dt.ensure(),ae(this,ee,Ha).call(this)})},i=l=>{try{o=!0,n==null||n(l,s),o=!1}catch(c){ft(c,d(this,_e)&&d(this,_e).parent)}r&&F(this,Oe,ae(this,ee,Rr).call(this,()=>{dt.ensure();try{return he(()=>{var c=x;c.b=this,c.f|=ta,r(d(this,Ee),()=>l,()=>s)})}catch(c){return ft(c,d(this,_e).parent),null}}))};et(()=>{var l;try{l=this.transform_error(t)}catch(c){ft(c,d(this,_e)&&d(this,_e).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,c=>ft(c,d(this,_e)&&d(this,_e).parent)):i(l)})}}Ee=new WeakMap,Oa=new WeakMap,Ve=new WeakMap,Ot=new WeakMap,_e=new WeakMap,He=new WeakMap,ye=new WeakMap,Oe=new WeakMap,rt=new WeakMap,$t=new WeakMap,gt=new WeakMap,un=new WeakMap,cn=new WeakMap,fn=new WeakMap,We=new WeakMap,qr=new WeakMap,ee=new WeakSet,zd=function(){try{F(this,He,he(()=>d(this,Ot).call(this,d(this,Ee))))}catch(t){this.error(t)}},eh=function(t){const n=d(this,Ve).failed;n&&F(this,Oe,he(()=>{n(d(this,Ee),()=>t,()=>()=>{})}))},th=function(){const t=d(this,Ve).pending;t&&(this.is_pending=!0,F(this,ye,he(()=>t(d(this,Ee)))),et(()=>{var n=F(this,rt,document.createDocumentFragment()),r=tt();n.append(r),F(this,He,ae(this,ee,Rr).call(this,()=>(dt.ensure(),he(()=>d(this,Ot).call(this,r))))),d(this,gt)===0&&(d(this,Ee).before(n),F(this,rt,null),Ft(d(this,ye),()=>{F(this,ye,null)}),ae(this,ee,Cr).call(this))}))},Ha=function(){try{if(this.is_pending=this.has_pending_snippet(),F(this,gt,0),F(this,$t,0),F(this,He,he(()=>{d(this,Ot).call(this,d(this,Ee))})),d(this,gt)>0){var t=F(this,rt,document.createDocumentFragment());Ps(d(this,He),t);const n=d(this,Ve).pending;F(this,ye,he(()=>n(d(this,Ee))))}else ae(this,ee,Cr).call(this)}catch(n){this.error(n)}},Cr=function(){this.is_pending=!1;for(const t of d(this,cn))J(t,se),Re(t);for(const t of d(this,fn))J(t,Fe),Re(t);d(this,cn).clear(),d(this,fn).clear()},Rr=function(t){var n=x,r=C,a=K;Te(d(this,_e)),Se(d(this,_e)),Ut(d(this,_e).ctx);try{return t()}catch(o){return es(o),null}finally{Te(n),Se(r),Ut(a)}},Wa=function(t){var n;if(!this.has_pending_snippet()){this.parent&&ae(n=this.parent,ee,Wa).call(n,t);return}F(this,gt,d(this,gt)+t),d(this,gt)===0&&(ae(this,ee,Cr).call(this),d(this,ye)&&Ft(d(this,ye),()=>{F(this,ye,null)}),d(this,rt)&&(d(this,Ee).before(d(this,rt)),F(this,rt,null)))};function ls(e,t,n,r){const a=vr;var o=e.filter(u=>!u.settled);if(n.length===0&&o.length===0){r(t.map(a));return}var s=x,i=vc(),l=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(u=>u.promise)):null;function c(u){i();try{r(u)}catch(h){(s.f&Je)===0&&ft(h,s)}la()}if(n.length===0){l.then(()=>c(t.map(a)));return}function f(){i(),Promise.all(n.map(u=>bc(u))).then(u=>c([...t.map(a),...u])).catch(u=>ft(u,s))}l?l.then(f):f()}function vc(){var e=x,t=C,n=K,r=D;if(g)var a=Kt;return function(s=!0){Te(e),Se(t),Ut(n),s&&(r==null||r.activate()),g&&_r(a)}}function la(e=!0){Te(null),Se(null),Ut(null),e&&(D==null||D.deactivate()),g&&_r(null)}function gc(){var e=x.b,t=D,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}const yc=new Set;function vr(e){var t=oe|se,n=C!==null&&(C.f&oe)!==0?C:null;return x!==null&&(x.f|=jt),{ctx:K,deps:null,effects:null,equals:Yo,f:t,fn:e,reactions:null,rv:0,v:ne,wv:0,parent:n??x,ac:null}}function bc(e,t,n){x===null&&Mu();var a=void 0,o=Pt(ne);g&&(o.label=t);var s=!C,i=new Map;return $c(()=>{var h;var l=Bo();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(la)}catch(m){l.reject(m),la()}var c=D;if(s){var f=gc();(h=i.get(c))==null||h.reject(Et),i.delete(c),i.set(c,l)}const u=(m,_=void 0)=>{if(c.activate(),_)_!==Et&&(o.f|=ut,Qt(o,_));else{(o.f&ut)!==0&&(o.f^=ut),Qt(o,m);for(const[w,p]of i){if(i.delete(w),w===c)break;p.reject(Et)}}f&&f()};l.promise.then(u,m=>u(null,m||"unknown"))}),ma(()=>{for(const l of i.values())l.reject(Et)}),g&&(o.f|=pr),new Promise(l=>{function c(f){function u(){f===a?l(o):c(a)}f.then(u,u)}c(a)})}function ua(e){const t=vr(e);return Fs(t),t}function us(e){const t=vr(e);return t.equals=Qo,t}function cs(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)le(t[n])}}let ca=[];function wc(e){for(var t=e.parent;t!==null;){if((t.f&oe)===0)return(t.f&Je)===0?t:null;t=t.parent}return null}function fa(e){var t,n=x;if(Te(wc(e)),g){let r=Yt;hs(new Set);try{Mt.call(ca,e)&&Su(),ca.push(e),e.f&=~lt,cs(e),t=ya(e)}finally{Te(n),hs(r),ca.pop()}}else try{e.f&=~lt,cs(e),t=ya(e)}finally{Te(n)}return t}function fs(e){var t=fa(e);if(!e.equals(t)&&(e.wv=xs(),(!(D!=null&&D.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){J(e,te);return}mt||(ie!==null?(_a()||D!=null&&D.is_fork)&&ie.set(e,t):oa(e))}function qc(e){var t,n;if(e.effects!==null)for(const r of e.effects)(r.teardown||r.ac)&&((t=r.teardown)==null||t.call(r),(n=r.ac)==null||n.abort(Et),r.teardown=V,r.ac=null,xn(r,0),va(r))}function ds(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&en(t)}let Yt=new Set;const ht=new Map;function hs(e){Yt=e}let da=!1;function Mc(){da=!0}function Pt(e,t){var n={f:0,v:e,reactions:null,equals:Yo,rv:0,wv:0};return n}function pt(e,t){const n=Pt(e);return Fs(n),n}function Sc(e,t=!1,n=!0){const r=Pt(e);return t||(r.equals=Qo),r}function _t(e,t,n=!1){C!==null&&(!xe||(C.f&hr)!==0)&&zo()&&(C.f&(oe|Ze|pr|hr))!==0&&(ke===null||!Mt.call(ke,e))&&Ou();let r=n?Zt(t):t;return g&&Zo(r,e.label),Qt(e,r)}function Qt(e,t){var a;if(!e.equals(t)){var n=e.v;mt?ht.set(e,t):ht.set(e,n),e.v=t;var r=dt.ensure();if(r.capture(e,n),g){if(x!==null){e.updated??(e.updated=new Map);const o=(((a=e.updated.get(""))==null?void 0:a.count)??0)+1;if(e.updated.set("",{error:null,count:o}),o>5){const s=rc("updated at");if(s!==null){let i=e.updated.get(s.stack);i||(i={error:s,count:0},e.updated.set(s.stack,i)),i.count++}}}x!==null&&(e.set_during_effect=!0)}if((e.f&oe)!==0){const o=e;(e.f&se)!==0&&fa(o),oa(o)}e.wv=xs(),_s(e,se),x!==null&&(x.f&te)!==0&&(x.f&(Ne|kt))===0&&(Ae===null?Gc([e]):Ae.push(e)),!r.is_fork&&Yt.size>0&&!da&&ps()}return t}function ps(){da=!1;for(const e of Yt)(e.f&te)!==0&&J(e,Fe),Rn(e)&&en(e);Yt.clear()}function Pn(e){_t(e,e.v+1)}function _s(e,t){var n=e.reactions;if(n!==null)for(var r=n.length,a=0;a<r;a++){var o=n[a],s=o.f;if(g&&(s&hr)!==0){Yt.add(o);continue}var i=(s&se)===0;if(i&&J(o,t),(s&oe)!==0){var l=o;ie==null||ie.delete(l),(s&lt)===0&&(s&qe&&(o.f|=lt),_s(l,Fe))}else i&&((s&Ze)!==0&&Ce!==null&&Ce.add(o),Re(o))}}const kc=/^[a-zA-Z_$][a-zA-Z_$0-9]*$/;function Zt(e){if(typeof e!="object"||e===null||ct in e)return e;const t=Lo(e);if(t!==vu&&t!==gu)return e;var n=new Map,r=zr(e),a=pt(0),o=Rt,s=f=>{if(Rt===o)return f();var u=C,h=Rt;Se(null),Rs(o);var m=f();return Se(u),Rs(h),m};r&&(n.set("length",pt(e.length)),g&&(e=Pc(e)));var i="";let l=!1;function c(f){if(!l){l=!0,i=f,Be(a,`${i} version`);for(const[u,h]of n)Be(h,Nt(i,u));l=!1}}return new Proxy(e,{defineProperty(f,u,h){(!("value"in h)||h.configurable===!1||h.enumerable===!1||h.writable===!1)&&Tu();var m=n.get(u);return m===void 0?s(()=>{var _=pt(h.value);return n.set(u,_),g&&typeof u=="string"&&Be(_,Nt(i,u)),_}):_t(m,h.value,!0),!0},deleteProperty(f,u){var h=n.get(u);if(h===void 0){if(u in f){const m=s(()=>pt(ne));n.set(u,m),Pn(a),g&&Be(m,Nt(i,u))}}else _t(h,ne),Pn(a);return!0},get(f,u,h){var p;if(u===ct)return e;if(g&&u===Ho)return c;var m=n.get(u),_=u in f;if(m===void 0&&(!_||(p=Qe(f,u))!=null&&p.writable)&&(m=s(()=>{var v=Zt(_?f[u]:ne),A=pt(v);return g&&Be(A,Nt(i,u)),A}),n.set(u,m)),m!==void 0){var w=P(m);return w===ne?void 0:w}return Reflect.get(f,u,h)},getOwnPropertyDescriptor(f,u){var h=Reflect.getOwnPropertyDescriptor(f,u);if(h&&"value"in h){var m=n.get(u);m&&(h.value=P(m))}else if(h===void 0){var _=n.get(u),w=_==null?void 0:_.v;if(_!==void 0&&w!==ne)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return h},has(f,u){var w;if(u===ct)return!0;var h=n.get(u),m=h!==void 0&&h.v!==ne||Reflect.has(f,u);if(h!==void 0||x!==null&&(!m||(w=Qe(f,u))!=null&&w.writable)){h===void 0&&(h=s(()=>{var p=m?Zt(f[u]):ne,v=pt(p);return g&&Be(v,Nt(i,u)),v}),n.set(u,h));var _=P(h);if(_===ne)return!1}return m},set(f,u,h,m){var Z;var _=n.get(u),w=u in f;if(r&&u==="length")for(var p=h;p<_.v;p+=1){var v=n.get(p+"");v!==void 0?_t(v,ne):p in f&&(v=s(()=>pt(ne)),n.set(p+"",v),g&&Be(v,Nt(i,p)))}if(_===void 0)(!w||(Z=Qe(f,u))!=null&&Z.writable)&&(_=s(()=>pt(void 0)),g&&Be(_,Nt(i,u)),_t(_,Zt(h)),n.set(u,_));else{w=_.v!==ne;var A=s(()=>Zt(h));_t(_,A)}var b=Reflect.getOwnPropertyDescriptor(f,u);if(b!=null&&b.set&&b.set.call(m,h),!w){if(r&&typeof u=="string"){var S=n.get("length"),E=Number(u);Number.isInteger(E)&&E>=S.v&&_t(S,E+1)}Pn(a)}return!0},ownKeys(f){P(a);var u=Reflect.ownKeys(f).filter(_=>{var w=n.get(_);return w===void 0||w.v!==ne});for(var[h,m]of n)m.v!==ne&&!(h in f)&&u.push(h);return u},setPrototypeOf(){Du()}})}function Nt(e,t){return typeof t=="symbol"?`${e}[Symbol(${t.description??""})]`:kc.test(t)?`${e}.${t}`:/^\d+$/.test(t)?`${e}[${t}]`:`${e}['${t}']`}function Nn(e){try{if(e!==null&&typeof e=="object"&&ct in e)return e[ct]}catch{}return e}function Ac(e,t){return Object.is(Nn(e),Nn(t))}const Ec=new Set(["copyWithin","fill","pop","push","reverse","shift","sort","splice","unshift"]);function Pc(e){return new Proxy(e,{get(t,n,r){var a=Reflect.get(t,n,r);return Ec.has(n)?function(...o){Mc();var s=a.apply(this,o);return ps(),s}:a}})}function Nc(){const e=Array.prototype,t=Array.__svelte_cleanup;t&&t();const{indexOf:n,lastIndexOf:r,includes:a}=e;e.indexOf=function(o,s){const i=n.call(this,o,s);if(i===-1){for(let l=s??0;l<this.length;l+=1)if(Nn(this[l])===o){ra("array.indexOf(...)");break}}return i},e.lastIndexOf=function(o,s){const i=r.call(this,o,s??this.length-1);if(i===-1){for(let l=0;l<=(s??this.length-1);l+=1)if(Nn(this[l])===o){ra("array.lastIndexOf(...)");break}}return i},e.includes=function(o,s){const i=a.call(this,o,s);if(!i){for(let l=0;l<this.length;l+=1)if(Nn(this[l])===o){ra("array.includes(...)");break}}return i},Array.__svelte_cleanup=()=>{e.indexOf=n,e.lastIndexOf=r,e.includes=a}}var ms,ha,vs,gs;function Fc(){if(ms===void 0){ms=window,ha=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;vs=Qe(t,"firstChild").get,gs=Qe(t,"nextSibling").get,Io(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Io(n)&&(n.__t=void 0),g&&(e.__svelte_meta=null,Nc())}}function tt(e=""){return document.createTextNode(e)}function Jt(e){return vs.call(e)}function Fn(e){return gs.call(e)}function k(e,t){return Jt(e)}function H(e,t=!1){{var n=Jt(e);return n instanceof Comment&&n.data===""?Fn(n):n}}function N(e,t=1,n=!1){let r=e;for(;t--;)r=Fn(r);return r}function Cc(e){e.textContent=""}function ys(){return!1}function bs(e,t,n){return document.createElementNS(t??Xo,e,void 0)}function Rc(e,t){if(t){const n=document.body;e.autofocus=!0,et(()=>{document.activeElement===n&&e.focus()})}}function pa(e){var t=C,n=x;Se(null),Te(null);try{return e()}finally{Se(t),Te(n)}}function xc(e){x===null&&(C===null&&Pu(e),Eu()),mt&&Au(e)}function Tc(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function Ge(e,t,n){var r=x;if(g)for(;r!==null&&(r.f&hr)!==0;)r=r.parent;r!==null&&(r.f&me)!==0&&(e|=me);var a={ctx:K,deps:null,nodes:null,f:e|se|qe,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null};if(g&&(a.component_function=En),n)try{en(a)}catch(i){throw le(a),i}else t!==null&&Re(a);var o=a;if(n&&o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&jt)===0&&(o=o.first,(e&Ze)!==0&&(e&it)!==0&&o!==null&&(o.f|=it)),o!==null&&(o.parent=r,r!==null&&Tc(o,r),C!==null&&(C.f&oe)!==0&&(e&kt)===0)){var s=C;(s.effects??(s.effects=[])).push(o)}return a}function _a(){return C!==null&&!xe}function ma(e){const t=Ge(dr,null,!1);return J(t,te),t.teardown=e,t}function Dc(e){xc("$effect"),g&&St(e,"name",{value:"$effect"});var t=x.f,n=!C&&(t&Ne)!==0&&(t&At)===0;if(n){var r=K;(r.e??(r.e=[])).push(e)}else return ws(e)}function ws(e){return Ge(Sn|wu,e,!1)}function Oc(e){dt.ensure();const t=Ge(kt|jt,e,!0);return(n={})=>new Promise(r=>{n.outro?Ft(t,()=>{le(t),r(void 0)}):(le(t),r(void 0))})}function qs(e){return Ge(Sn,e,!1)}function $c(e){return Ge(pr|jt,e,!0)}function Lc(e,t=0){return Ge(dr|t,e,!0)}function zt(e,t=[],n=[],r=[]){ls(r,t,n,a=>{Ge(dr,()=>e(...a.map(P)),!0)})}function Cn(e,t=0){var n=Ge(Ze|t,e,!0);return g&&(n.dev_stack=Kt),n}function Ms(e,t=0){var n=Ge(ea|t,e,!0);return g&&(n.dev_stack=Kt),n}function he(e){return Ge(Ne|jt,e,!0)}function Ss(e){var t=e.teardown;if(t!==null){const n=mt,r=C;Ns(!0),Se(null);try{t.call(null)}finally{Ns(n),Se(r)}}}function va(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const a=n.ac;a!==null&&pa(()=>{a.abort(Et)});var r=n.next;(n.f&kt)!==0?n.parent=null:le(n,t),n=r}}function Ic(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&Ne)===0&&le(t),t=n}}function le(e,t=!0){var n=!1;(t||(e.f&Go)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(Bc(e.nodes.start,e.nodes.end),n=!0),va(e,t&&!n),xn(e,0),J(e,Je);var r=e.nodes&&e.nodes.t;if(r!==null)for(const o of r)o.stop();Ss(e);var a=e.parent;a!==null&&a.first!==null&&ks(e),g&&(e.component_function=null),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function Bc(e,t){for(;e!==null;){var n=e===t?null:Fn(e);e.remove(),e=n}}function ks(e){var t=e.parent,n=e.prev,r=e.next;n!==null&&(n.next=r),r!==null&&(r.prev=n),t!==null&&(t.first===e&&(t.first=r),t.last===e&&(t.last=n))}function Ft(e,t,n=!0){var r=[];As(e,r,!0);var a=()=>{n&&le(e),t&&t()},o=r.length;if(o>0){var s=()=>--o||a();for(var i of r)i.out(s)}else a()}function As(e,t,n){if((e.f&me)===0){e.f^=me;var r=e.nodes&&e.nodes.t;if(r!==null)for(const i of r)(i.is_global||n)&&t.push(i);for(var a=e.first;a!==null;){var o=a.next,s=(a.f&it)!==0||(a.f&Ne)!==0&&(e.f&Ze)!==0;As(a,t,s?n:!1),a=o}}}function ga(e){Es(e,!0)}function Es(e,t){if((e.f&me)!==0){e.f^=me,(e.f&te)===0&&(J(e,se),Re(e));for(var n=e.first;n!==null;){var r=n.next,a=(n.f&it)!==0||(n.f&Ne)!==0;Es(n,a?t:!1),n=r}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function Ps(e,t){if(e.nodes)for(var n=e.nodes.start,r=e.nodes.end;n!==null;){var a=n===r?null:Fn(n);t.append(n),n=a}}let gr=!1,mt=!1;function Ns(e){mt=e}let C=null,xe=!1;function Se(e){C=e}let x=null;function Te(e){x=e}let ke=null;function Fs(e){C!==null&&(ke===null?ke=[e]:ke.push(e))}let pe=null,ve=0,Ae=null;function Gc(e){Ae=e}let Cs=1,Ct=0,Rt=Ct;function Rs(e){Rt=e}function xs(){return++Cs}function Rn(e){var t=e.f;if((t&se)!==0)return!0;if(t&oe&&(e.f&=~lt),(t&Fe)!==0){for(var n=e.deps,r=n.length,a=0;a<r;a++){var o=n[a];if(Rn(o)&&fs(o),o.wv>e.wv)return!0}(t&qe)!==0&&ie===null&&J(e,te)}return!1}function Ts(e,t,n=!0){var r=e.reactions;if(r!==null&&!(ke!==null&&Mt.call(ke,e)))for(var a=0;a<r.length;a++){var o=r[a];(o.f&oe)!==0?Ts(o,t,!1):t===o&&(n?J(o,se):(o.f&te)!==0&&J(o,Fe),Re(o))}}function ya(e){var w;var t=pe,n=ve,r=Ae,a=C,o=ke,s=K,i=xe,l=Rt,c=e.f;pe=null,ve=0,Ae=null,C=(c&(Ne|kt))===0?e:null,ke=null,Ut(e.ctx),xe=!1,Rt=++Ct,e.ac!==null&&(pa(()=>{e.ac.abort(Et)}),e.ac=null);try{e.f|=na;var f=e.fn,u=f();e.f|=At;var h=e.deps,m=D==null?void 0:D.is_fork;if(pe!==null){var _;if(m||xn(e,ve),h!==null&&ve>0)for(h.length=ve+pe.length,_=0;_<pe.length;_++)h[ve+_]=pe[_];else e.deps=h=pe;if(_a()&&(e.f&qe)!==0)for(_=ve;_<h.length;_++)((w=h[_]).reactions??(w.reactions=[])).push(e)}else!m&&h!==null&&ve<h.length&&(xn(e,ve),h.length=ve);if(zo()&&Ae!==null&&!xe&&h!==null&&(e.f&(oe|Fe|se))===0)for(_=0;_<Ae.length;_++)Ts(Ae[_],e);if(a!==null&&a!==e){if(Ct++,a.deps!==null)for(let p=0;p<n;p+=1)a.deps[p].rv=Ct;if(t!==null)for(const p of t)p.rv=Ct;Ae!==null&&(r===null?r=Ae:r.push(...Ae))}return(e.f&ut)!==0&&(e.f^=ut),u}catch(p){return es(p)}finally{e.f^=na,pe=t,ve=n,Ae=r,C=a,ke=o,Ut(s),xe=i,Rt=l}}function Vc(e,t){let n=t.reactions;if(n!==null){var r=_u.call(n,e);if(r!==-1){var a=n.length-1;a===0?n=t.reactions=null:(n[r]=n[a],n.pop())}}if(n===null&&(t.f&oe)!==0&&(pe===null||!Mt.call(pe,t))){var o=t;(o.f&qe)!==0&&(o.f^=qe,o.f&=~lt),oa(o),qc(o),xn(o,0)}}function xn(e,t){var n=e.deps;if(n!==null)for(var r=t;r<n.length;r++)Vc(e,n[r])}function en(e){var t=e.f;if((t&Je)===0){J(e,te);var n=x,r=gr;if(x=e,gr=!0,g){var a=En;Jo(e.component_function);var o=Kt;_r(e.dev_stack??Kt)}try{(t&(Ze|ea))!==0?Ic(e):va(e),Ss(e);var s=ya(e);e.teardown=typeof s=="function"?s:null,e.wv=Cs;var i;g&&nc&&(e.f&se)!==0&&e.deps}finally{gr=r,x=n,g&&(Jo(a),_r(o))}}}function P(e){var t=e.f,n=(t&oe)!==0;if(C!==null&&!xe){var r=x!==null&&(x.f&Je)!==0;if(!r&&(ke===null||!Mt.call(ke,e))){var a=C.deps;if((C.f&na)!==0)e.rv<Ct&&(e.rv=Ct,pe===null&&a!==null&&a[ve]===e?ve++:pe===null?pe=[e]:pe.push(e));else{(C.deps??(C.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[C]:Mt.call(o,C)||o.push(C)}}}if(g&&yc.delete(e),mt&&ht.has(e))return ht.get(e);if(n){var s=e;if(mt){var i=s.v;return((s.f&te)===0&&s.reactions!==null||Os(s))&&(i=fa(s)),ht.set(s,i),i}var l=(s.f&qe)===0&&!xe&&C!==null&&(gr||(C.f&qe)!==0),c=(s.f&At)===0;Rn(s)&&(l&&(s.f|=qe),fs(s)),l&&!c&&(ds(s),Ds(s))}if(ie!=null&&ie.has(e))return ie.get(e);if((e.f&ut)!==0)throw e.v;return e.v}function Ds(e){if(e.f|=qe,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&oe)!==0&&(t.f&qe)===0&&(ds(t),Ds(t))}function Os(e){if(e.v===ne)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(ht.has(t)||(t.f&oe)!==0&&Os(t))return!0;return!1}function ba(e){var t=xe;try{return xe=!0,e()}finally{xe=t}}function Hc(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const Wc=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function jc(e){return Wc.includes(e)}const Uc={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Kc(e){return e=e.toLowerCase(),Uc[e]??e}const Xc=["touchstart","touchmove"];function Yc(e){return Xc.includes(e)}const xt=Symbol("events"),$s=new Set,wa=new Set;function Qc(e,t,n,r={}){function a(o){if(r.capture||qa.call(t,o),!o.cancelBubble)return pa(()=>n==null?void 0:n.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?et(()=>{t.addEventListener(e,a,r)}):t.addEventListener(e,a,r),a}function De(e,t,n){(t[xt]??(t[xt]={}))[e]=n}function Ls(e){for(var t=0;t<e.length;t++)$s.add(e[t]);for(var n of wa)n(e)}let Is=null;function qa(e){var p,v;var t=this,n=t.ownerDocument,r=e.type,a=((p=e.composedPath)==null?void 0:p.call(e))||[],o=a[0]||e.target;Is=e;var s=0,i=Is===e&&e[xt];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[xt]=t;return}var c=a.indexOf(t);if(c===-1)return;l<=c&&(s=l)}if(o=a[s]||e.target,o!==t){St(e,"currentTarget",{configurable:!0,get(){return o||n}});var f=C,u=x;Se(null),Te(null);try{for(var h,m=[];o!==null;){var _=o.assignedSlot||o.parentNode||o.host||null;try{var w=(v=o[xt])==null?void 0:v[r];w!=null&&(!o.disabled||e.target===o)&&w.call(o,e)}catch(A){h?m.push(A):h=A}if(e.cancelBubble||_===t||_===null)break;o=_}if(h){for(let A of m)queueMicrotask(()=>{throw A});throw h}}finally{e[xt]=t,delete e.currentTarget,Se(f),Te(u)}}}const Ma=((fi=globalThis==null?void 0:globalThis.window)==null?void 0:fi.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Zc(e){return(Ma==null?void 0:Ma.createHTML(e))??e}function Bs(e){var t=bs("template");return t.innerHTML=Zc(e.replaceAll("<!>","<!---->")),t.content}function Tn(e,t){var n=x;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function tn(e,t){var n=(t&Uu)!==0,r=(t&Ku)!==0,a,o=!e.startsWith("<!>");return()=>{a===void 0&&(a=Bs(o?e:"<!>"+e),n||(a=Jt(a)));var s=r||ha?document.importNode(a,!0):a.cloneNode(!0);if(n){var i=Jt(s),l=s.lastChild;Tn(i,l)}else Tn(s,s);return s}}function Jc(e,t,n="svg"){var r=!e.startsWith("<!>"),a=`<${n}>${r?e:"<!>"+e}</${n}>`,o;return()=>{if(!o){var s=Bs(a),i=Jt(s);o=Jt(i)}var l=o.cloneNode(!0);return Tn(l,l),l}}function zc(e,t){return Jc(e,t,"svg")}function W(){var e=document.createDocumentFragment(),t=document.createComment(""),n=tt();return e.append(t,n),Tn(t,n),e}function O(e,t){e!==null&&e.before(t)}function Gs(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function ef(e,t){return tf(e,t)}const yr=new Map;function tf(e,{target:t,anchor:n,props:r={},events:a,context:o,intro:s=!0,transformError:i}){Fc();var l=void 0,c=Oc(()=>{var f=n??t.appendChild(tt());_c(f,{pending:()=>{}},m=>{L({});var _=K;o&&(_.c=o),a&&(r.$$events=a),l=e(m,r)||{},I()},i);var u=new Set,h=m=>{for(var _=0;_<m.length;_++){var w=m[_];if(!u.has(w)){u.add(w);var p=Yc(w);for(const b of[t,document]){var v=yr.get(b);v===void 0&&(v=new Map,yr.set(b,v));var A=v.get(w);A===void 0?(b.addEventListener(w,qa,{passive:p}),v.set(w,1)):v.set(w,A+1)}}}};return h(fr($s)),wa.add(h),()=>{var p;for(var m of u)for(const v of[t,document]){var _=yr.get(v),w=_.get(m);--w==0?(v.removeEventListener(m,qa),_.delete(m),_.size===0&&yr.delete(v)):_.set(m,w)}wa.delete(h),f!==n&&((p=f.parentNode)==null||p.removeChild(f))}});return Sa.set(l,c),l}let Sa=new WeakMap;function Vs(e,t){const n=Sa.get(e);return n?(Sa.delete(e),n(t)):(g&&(ct in e?zu():Zu()),Promise.resolve())}class ka{constructor(t,n=!0){Ke(this,"anchor");R(this,$e,new Map);R(this,je,new Map);R(this,be,new Map);R(this,Lt,new Set);R(this,Vn,!0);R(this,Hn,()=>{var t=D;if(d(this,$e).has(t)){var n=d(this,$e).get(t),r=d(this,je).get(n);if(r)ga(r),d(this,Lt).delete(n);else{var a=d(this,be).get(n);a&&(d(this,je).set(n,a.effect),d(this,be).delete(n),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),r=a.effect)}for(const[o,s]of d(this,$e)){if(d(this,$e).delete(o),o===t)break;const i=d(this,be).get(s);i&&(le(i.effect),d(this,be).delete(s))}for(const[o,s]of d(this,je)){if(o===n||d(this,Lt).has(o))continue;const i=()=>{if(Array.from(d(this,$e).values()).includes(o)){var c=document.createDocumentFragment();Ps(s,c),c.append(tt()),d(this,be).set(o,{effect:s,fragment:c})}else le(s);d(this,Lt).delete(o),d(this,je).delete(o)};d(this,Vn)||!r?(d(this,Lt).add(o),Ft(s,i,!1)):i()}}});R(this,Mr,t=>{d(this,$e).delete(t);const n=Array.from(d(this,$e).values());for(const[r,a]of d(this,be))n.includes(r)||(le(a.effect),d(this,be).delete(r))});this.anchor=t,F(this,Vn,n)}ensure(t,n){var r=D,a=ys();if(n&&!d(this,je).has(t)&&!d(this,be).has(t))if(a){var o=document.createDocumentFragment(),s=tt();o.append(s),d(this,be).set(t,{effect:he(()=>n(s)),fragment:o})}else d(this,je).set(t,he(()=>n(this.anchor)));if(d(this,$e).set(r,t),a){for(const[i,l]of d(this,je))i===t?r.unskip_effect(l):r.skip_effect(l);for(const[i,l]of d(this,be))i===t?r.unskip_effect(l.effect):r.skip_effect(l.effect);r.oncommit(d(this,Hn)),r.ondiscard(d(this,Mr))}else d(this,Hn).call(this)}}$e=new WeakMap,je=new WeakMap,be=new WeakMap,Lt=new WeakMap,Vn=new WeakMap,Hn=new WeakMap,Mr=new WeakMap;function br(e,t,n=!1){var r=new ka(e),a=n?it:0;function o(s,i){r.ensure(s,i)}Cn(()=>{var s=!1;t((i,l=0)=>{s=!0,o(l,i)}),s||o(!1,null)},a)}function nf(e,t){return t}function rf(e,t,n){for(var r=[],a=t.length,o,s=t.length,i=0;i<a;i++){let u=t[i];Ft(u,()=>{if(o){if(o.pending.delete(u),o.done.add(u),o.pending.size===0){var h=e.outrogroups;Aa(fr(o.done)),h.delete(o),h.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var l=r.length===0&&n!==null;if(l){var c=n,f=c.parentNode;Cc(f),f.append(c),e.items.clear()}Aa(t,!l)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function Aa(e,t=!0){for(var n=0;n<e.length;n++)le(e[n],t)}var Hs;function Ea(e,t,n,r,a,o=null){var s=e,i=new Map,l=(t&Ko)!==0;if(l){var c=e;s=c.appendChild(tt())}var f=null,u=us(()=>{var v=n();return zr(v)?v:v==null?[]:fr(v)}),h,m=!0;function _(){p.fallback=f,af(p,h,s,t,r),f!==null&&(h.length===0?(f.f&ze)===0?ga(f):(f.f^=ze,On(f,null,s)):Ft(f,()=>{f=null}))}var w=Cn(()=>{h=P(u);for(var v=h.length,A=new Set,b=D,S=ys(),E=0;E<v;E+=1){var Z=h[E],T=r(Z,E);if(g){var we=r(Z,E);T!==we&&ku(String(E),String(T),String(we))}var ue=m?null:i.get(T);ue?(ue.v&&Qt(ue.v,Z),ue.i&&Qt(ue.i,E),S&&b.unskip_effect(ue.e)):(ue=of(i,m?s:Hs??(Hs=tt()),Z,T,E,a,t,n),m||(ue.e.f|=ze),i.set(T,ue)),A.add(T)}if(v===0&&o&&!f&&(m?f=he(()=>o(s)):(f=he(()=>o(Hs??(Hs=tt()))),f.f|=ze)),v>A.size&&(g?sf(h,r):Uo("","","")),!m)if(S){for(const[yt,at]of i)A.has(yt)||b.skip_effect(at.e);b.oncommit(_),b.ondiscard(()=>{})}else _();P(u)}),p={effect:w,items:i,outrogroups:null,fallback:f};m=!1}function Dn(e){for(;e!==null&&(e.f&Ne)===0;)e=e.next;return e}function af(e,t,n,r,a){var yt,at,y,Sr,Wn,kr,Ar,jn,Er;var o=(r&Bu)!==0,s=t.length,i=e.items,l=Dn(e.effect.first),c,f=null,u,h=[],m=[],_,w,p,v;if(o)for(v=0;v<s;v+=1)_=t[v],w=a(_,v),p=i.get(w).e,(p.f&ze)===0&&((at=(yt=p.nodes)==null?void 0:yt.a)==null||at.measure(),(u??(u=new Set)).add(p));for(v=0;v<s;v+=1){if(_=t[v],w=a(_,v),p=i.get(w).e,e.outrogroups!==null)for(const Le of e.outrogroups)Le.pending.delete(p),Le.done.delete(p);if((p.f&ze)!==0)if(p.f^=ze,p===l)On(p,null,n);else{var A=f?f.next:l;p===e.effect.last&&(e.effect.last=p.prev),p.prev&&(p.prev.next=p.next),p.next&&(p.next.prev=p.prev),vt(e,f,p),vt(e,p,A),On(p,A,n),f=p,h=[],m=[],l=Dn(f.next);continue}if((p.f&me)!==0&&(ga(p),o&&((Sr=(y=p.nodes)==null?void 0:y.a)==null||Sr.unfix(),(u??(u=new Set)).delete(p))),p!==l){if(c!==void 0&&c.has(p)){if(h.length<m.length){var b=m[0],S;f=b.prev;var E=h[0],Z=h[h.length-1];for(S=0;S<h.length;S+=1)On(h[S],b,n);for(S=0;S<m.length;S+=1)c.delete(m[S]);vt(e,E.prev,Z.next),vt(e,f,E),vt(e,Z,b),l=b,f=Z,v-=1,h=[],m=[]}else c.delete(p),On(p,l,n),vt(e,p.prev,p.next),vt(e,p,f===null?e.effect.first:f.next),vt(e,f,p),f=p;continue}for(h=[],m=[];l!==null&&l!==p;)(c??(c=new Set)).add(l),m.push(l),l=Dn(l.next);if(l===null)continue}(p.f&ze)===0&&h.push(p),f=p,l=Dn(p.next)}if(e.outrogroups!==null){for(const Le of e.outrogroups)Le.pending.size===0&&(Aa(fr(Le.done)),(Wn=e.outrogroups)==null||Wn.delete(Le));e.outrogroups.size===0&&(e.outrogroups=null)}if(l!==null||c!==void 0){var T=[];if(c!==void 0)for(p of c)(p.f&me)===0&&T.push(p);for(;l!==null;)(l.f&me)===0&&l!==e.fallback&&T.push(l),l=Dn(l.next);var we=T.length;if(we>0){var ue=(r&Ko)!==0&&s===0?n:null;if(o){for(v=0;v<we;v+=1)(Ar=(kr=T[v].nodes)==null?void 0:kr.a)==null||Ar.measure();for(v=0;v<we;v+=1)(Er=(jn=T[v].nodes)==null?void 0:jn.a)==null||Er.fix()}rf(e,T,ue)}}o&&et(()=>{var Le,Un;if(u!==void 0)for(p of u)(Un=(Le=p.nodes)==null?void 0:Le.a)==null||Un.apply()})}function of(e,t,n,r,a,o,s,i){var l=(s&Lu)!==0?(s&Gu)===0?Sc(n,!1,!1):Pt(n):null,c=(s&Iu)!==0?Pt(a):null;return g&&l&&(l.trace=()=>{i()[(c==null?void 0:c.v)??a]}),{v:l,i:c,e:he(()=>(o(t,l??n,c??a,i),()=>{e.delete(r)}))}}function On(e,t,n){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end,o=t&&(t.f&ze)===0?t.nodes.start:n;r!==null;){var s=Fn(r);if(o.before(r),r===a)return;r=s}}function vt(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function sf(e,t){const n=new Map,r=e.length;for(let a=0;a<r;a++){const o=t(e[a],a);if(n.has(o)){const s=String(n.get(o)),i=String(a);let l=String(o);l.startsWith("[object ")&&(l=null),Uo(s,i,l)}n.set(o,a)}}function j(e,t,...n){var r=new ka(e);Cn(()=>{const a=t()??null;g&&a==null&&Fu(),r.ensure(a,a&&(o=>a(o,...n)))},it)}function lf(e,t,n,r,a,o){var s=null,i=e,l=new ka(i,!1);Cn(()=>{const c=t()||null;var f=Yu;if(c===null){l.ensure(null,null);return}return l.ensure(c,u=>{if(c){if(s=bs(c,f),Tn(s,s),r){var h=s.appendChild(tt());r(s,h)}x.nodes.end=s,u.before(s)}}),()=>{}},it),ma(()=>{})}function uf(e,t){var n=void 0,r;Ms(()=>{n!==(n=t())&&(r&&(le(r),r=null),n&&(r=he(()=>{qs(()=>n(e))})))})}function Ws(e){var t,n,r="";if(typeof e=="string"||typeof e=="number")r+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(n=Ws(e[t]))&&(r&&(r+=" "),r+=n)}else for(n in e)e[n]&&(r&&(r+=" "),r+=n);return r}function cf(){for(var e,t,n=0,r="",a=arguments.length;n<a;n++)(e=arguments[n])&&(t=Ws(e))&&(r&&(r+=" "),r+=t);return r}function js(e){return typeof e=="object"?cf(e):e??""}const Us=[...` 	
\r\f \v\uFEFF`];function ff(e,t,n){var r=e==null?"":""+e;if(t&&(r=r?r+" "+t:t),n){for(var a of Object.keys(n))if(n[a])r=r?r+" "+a:a;else if(r.length)for(var o=a.length,s=0;(s=r.indexOf(a,s))>=0;){var i=s+o;(s===0||Us.includes(r[s-1]))&&(i===r.length||Us.includes(r[i]))?r=(s===0?"":r.substring(0,s))+r.substring(i+1):s=i}}return r===""?null:r}function Ks(e,t=!1){var n=t?" !important;":";",r="";for(var a of Object.keys(e)){var o=e[a];o!=null&&o!==""&&(r+=" "+a+": "+o+n)}return r}function Pa(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function df(e,t){if(t){var n="",r,a;if(Array.isArray(t)?(r=t[0],a=t[1]):r=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,i=!1,l=[];r&&l.push(...Object.keys(r).map(Pa)),a&&l.push(...Object.keys(a).map(Pa));var c=0,f=-1;const w=e.length;for(var u=0;u<w;u++){var h=e[u];if(i?h==="/"&&e[u-1]==="*"&&(i=!1):o?o===h&&(o=!1):h==="/"&&e[u+1]==="*"?i=!0:h==='"'||h==="'"?o=h:h==="("?s++:h===")"&&s--,!i&&o===!1&&s===0){if(h===":"&&f===-1)f=u;else if(h===";"||u===w-1){if(f!==-1){var m=Pa(e.substring(c,f).trim());if(!l.includes(m)){h!==";"&&u++;var _=e.substring(c,u).trim();n+=" "+_+";"}}c=u+1,f=-1}}}}return r&&(n+=Ks(r)),a&&(n+=Ks(a,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function Na(e,t,n,r,a,o){var s=e.__className;if(s!==n||s===void 0){var i=ff(n,r,o);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=n}else if(o&&a!==o)for(var l in o){var c=!!o[l];(a==null||c!==!!a[l])&&e.classList.toggle(l,c)}return o}function Fa(e,t={},n,r){for(var a in n){var o=n[a];t[a]!==o&&(n[a]==null?e.style.removeProperty(a):e.style.setProperty(a,o,r))}}function hf(e,t,n,r){var a=e.__style;if(a!==t){var o=df(t,r);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else r&&(Array.isArray(r)?(Fa(e,n==null?void 0:n[0],r[0]),Fa(e,n==null?void 0:n[1],r[1],"important")):Fa(e,n,r));return r}function Ca(e,t,n=!1){if(e.multiple){if(t==null)return;if(!zr(t))return Ju();for(var r of e.options)r.selected=t.includes(Xs(r));return}for(r of e.options){var a=Xs(r);if(Ac(a,t)){r.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function pf(e){var t=new MutationObserver(()=>{Ca(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),ma(()=>{t.disconnect()})}function Xs(e){return"__value"in e?e.__value:e.value}const $n=Symbol("class"),Ln=Symbol("style"),Ys=Symbol("is custom element"),Qs=Symbol("is html"),_f=Wo?"option":"OPTION",mf=Wo?"select":"SELECT";function vf(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function M(e,t,n,r){var a=Js(e);a[t]!==(a[t]=n)&&(t==="loading"&&(e[qu]=n),n==null?e.removeAttribute(t):typeof n!="string"&&ei(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function gf(e,t,n,r,a=!1,o=!1){var s=Js(e),i=s[Ys],l=!s[Qs],c=t||{},f=e.nodeName===_f;for(var u in t)u in n||(n[u]=null);n.class?n.class=js(n.class):n[$n]&&(n.class=null),n[Ln]&&(n.style??(n.style=null));var h=ei(e);for(const b in n){let S=n[b];if(f&&b==="value"&&S==null){e.value=e.__value="",c[b]=S;continue}if(b==="class"){var m=e.namespaceURI==="http://www.w3.org/1999/xhtml";Na(e,m,S,r,t==null?void 0:t[$n],n[$n]),c[b]=S,c[$n]=n[$n];continue}if(b==="style"){hf(e,S,t==null?void 0:t[Ln],n[Ln]),c[b]=S,c[Ln]=n[Ln];continue}var _=c[b];if(!(S===_&&!(S===void 0&&e.hasAttribute(b)))){c[b]=S;var w=b[0]+b[1];if(w!=="$$")if(w==="on"){const E={},Z="$$"+b;let T=b.slice(2);var p=jc(T);if(Hc(T)&&(T=T.slice(0,-7),E.capture=!0),!p&&_){if(S!=null)continue;e.removeEventListener(T,c[Z],E),c[Z]=null}if(p)De(T,e,S),Ls([T]);else if(S!=null){let we=function(ue){c[b].call(this,ue)};c[Z]=Qc(T,e,we,E)}}else if(b==="style")M(e,b,S);else if(b==="autofocus")Rc(e,!!S);else if(!i&&(b==="__value"||b==="value"&&S!=null))e.value=e.__value=S;else if(b==="selected"&&f)vf(e,S);else{var v=b;l||(v=Kc(v));var A=v==="defaultValue"||v==="defaultChecked";if(S==null&&!i&&!A)if(s[b]=null,v==="value"||v==="checked"){let E=e;const Z=t===void 0;if(v==="value"){let T=E.defaultValue;E.removeAttribute(v),E.defaultValue=T,E.value=E.__value=Z?T:null}else{let T=E.defaultChecked;E.removeAttribute(v),E.defaultChecked=T,E.checked=Z?T:!1}}else e.removeAttribute(b);else A||h.includes(v)&&(i||typeof S!="string")?(e[v]=S,v in s&&(s[v]=ne)):typeof S!="function"&&M(e,v,S)}}}return c}function Zs(e,t,n=[],r=[],a=[],o,s=!1,i=!1){ls(a,n,r,l=>{var c=void 0,f={},u=e.nodeName===mf,h=!1;if(Ms(()=>{var _=t(...l.map(P)),w=gf(e,c,_,o,s,i);h&&u&&"value"in _&&Ca(e,_.value);for(let v of Object.getOwnPropertySymbols(f))_[v]||le(f[v]);for(let v of Object.getOwnPropertySymbols(_)){var p=_[v];v.description===Qu&&(!c||p!==c[v])&&(f[v]&&le(f[v]),f[v]=he(()=>uf(e,()=>p))),w[v]=p}c=w}),u){var m=e;qs(()=>{Ca(m,c.value,!0),pf(m)})}h=!0})}function Js(e){return e.__attributes??(e.__attributes={[Ys]:e.nodeName.includes("-"),[Qs]:e.namespaceURI===Xo})}var zs=new Map;function ei(e){var t=e.getAttribute("is")||e.nodeName,n=zs.get(t);if(n)return n;zs.set(t,n=[]);for(var r,a=e,o=Element.prototype;o!==a;){r=mu(a);for(var s in r)r[s].set&&n.push(s);a=Lo(a)}return n}let wr=!1;function yf(e){var t=wr;try{return wr=!1,[e(),wr]}finally{wr=t}}const bf={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return g&&Ru(`${e.name}.${String(t)}`),!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function U(e,t,n){return new Proxy(g?{props:e,exclude:t,name:n,other:{},to_proxy:[]}:{props:e,exclude:t},bf)}const wf={get(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(Mn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r)return r[t]}},set(e,t,n){let r=e.props.length;for(;r--;){let a=e.props[r];Mn(a)&&(a=a());const o=Qe(a,t);if(o&&o.set)return o.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(Mn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r){const a=Qe(r,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===ct||t===Vo)return!1;for(let n of e.props)if(Mn(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(Mn(n)&&(n=n()),!!n){for(const r in n)t.includes(r)||t.push(r);for(const r of Object.getOwnPropertySymbols(n))t.includes(r)||t.push(r)}return t}};function X(...e){return new Proxy({props:e},wf)}function nn(e,t,n,r){var A;var a=(n&Wu)!==0,o=(n&ju)!==0,s=r,i=!0,l=()=>(i&&(i=!1,s=o?ba(r):r),s),c;if(a){var f=ct in e||Vo in e;c=((A=Qe(e,t))==null?void 0:A.set)??(f&&t in e?b=>e[t]=b:void 0)}var u,h=!1;a?[u,h]=yf(()=>e[t]):u=e[t],u===void 0&&r!==void 0&&(u=l(),c&&(Cu(t),c(u)));var m;if(m=()=>{var b=e[t];return b===void 0?l():(i=!0,b)},(n&Hu)===0)return m;if(c){var _=e.$$legacy;return(function(b,S){return arguments.length>0?((!S||_||h)&&c(S?m():b),b):m()})}var w=!1,p=((n&Vu)!==0?vr:us)(()=>(w=!1,m()));g&&(p.label=t),a&&P(p);var v=x;return(function(b,S){if(arguments.length>0){const E=S?P(p):a?Zt(b):b;return _t(p,E),w=!0,s!==void 0&&(s=E),b}return mt&&w||(v.f&Je)!==0?p.v:P(p)})}if(g){let e=function(t){if(!(t in globalThis)){let n;Object.defineProperty(globalThis,t,{configurable:!0,get:()=>{if(n!==void 0)return n;xu(t)},set:r=>{n=r}})}};e("$state"),e("$effect"),e("$derived"),e("$inspect"),e("$props"),e("$bindable")}function qf(e){K===null&&jo("onMount"),Dc(()=>{const t=ba(e);if(typeof t=="function")return t})}const Mf="5";typeof window<"u"&&((di=window.__svelte??(window.__svelte={})).v??(di.v=new Set)).add(Mf);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Sf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const kf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Af=Symbol("lucide-context"),Ef=()=>oc(Af);var Pf=zc("<svg><!><!></svg>");function Y(e,t){L(t,!0);const n=Ef()??{},r=nn(t,"color",19,()=>n.color??"currentColor"),a=nn(t,"size",19,()=>n.size??24),o=nn(t,"strokeWidth",19,()=>n.strokeWidth??2),s=nn(t,"absoluteStrokeWidth",19,()=>n.absoluteStrokeWidth??!1),i=nn(t,"iconNode",19,()=>[]),l=U(t,["$$slots","$$events","$$legacy","name","color","size","strokeWidth","absoluteStrokeWidth","iconNode","children"]),c=ua(()=>s()?Number(o())*24/Number(a()):o());var f=Pf();Zs(f,m=>({...Sf,...m,...l,width:a(),height:a(),stroke:r(),"stroke-width":P(c),class:["lucide-icon lucide",n.class,t.name&&`lucide-${t.name}`,t.class]}),[()=>!t.children&&!kf(l)&&{"aria-hidden":"true"}]);var u=k(f);Ea(u,17,i,nf,(m,_)=>{var w=ua(()=>bu(P(_),2));let p=()=>P(w)[0],v=()=>P(w)[1];var A=W(),b=H(A);lf(b,p,!0,(S,E)=>{Zs(S,()=>({...v()}))}),O(m,A)});var h=N(u);j(h,()=>t.children??V),O(e,f),I()}function Nf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M2 10v3"}],["path",{d:"M6 6v11"}],["path",{d:"M10 3v18"}],["path",{d:"M14 8v7"}],["path",{d:"M18 5v13"}],["path",{d:"M22 10v3"}]];Y(e,X({name:"audio-lines"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Ff(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];Y(e,X({name:"chart-line"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Cf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 9 6 6 6-6"}]];Y(e,X({name:"chevron-down"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Rf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"}],["path",{d:"M12 17h.01"}]];Y(e,X({name:"circle-question-mark"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function xf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 12 18z"}],["path",{d:"M2 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 2 18z"}]];Y(e,X({name:"fast-forward"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Tf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]];Y(e,X({name:"folder-open"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Df(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["rect",{x:"14",y:"3",width:"5",height:"18",rx:"1"}],["rect",{x:"5",y:"3",width:"5",height:"18",rx:"1"}]];Y(e,X({name:"pause"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Of(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"}]];Y(e,X({name:"play"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function $f(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m15 14 5-5-5-5"}],["path",{d:"M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13"}]];Y(e,X({name:"redo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Lf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Y(e,X({name:"refresh-cw"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function If(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m2 9 3-3 3 3"}],["path",{d:"M13 18H7a2 2 0 0 1-2-2V6"}],["path",{d:"m22 15-3 3-3-3"}],["path",{d:"M11 6h6a2 2 0 0 1 2 2v10"}]];Y(e,X({name:"repeat-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Bf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 12 18z"}],["path",{d:"M22 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 22 18z"}]];Y(e,X({name:"rewind"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Gf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]];Y(e,X({name:"scissors"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Vf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Y(e,X({name:"settings"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Hf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];Y(e,X({name:"sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Wf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]];Y(e,X({name:"timer-reset"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function jf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Y(e,X({name:"trash-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Uf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"}]];Y(e,X({name:"undo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Kf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}]];Y(e,X({name:"volume-1"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Xf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}],["path",{d:"M19.364 18.364a9 9 0 0 0 0-12.728"}]];Y(e,X({name:"volume-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Yf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]];Y(e,X({name:"volume-x"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}function Qf(e,t){L(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}]];Y(e,X({name:"waves"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=H(s);j(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),I()}var Zf=tn('<span aria-hidden="true"><!></span>');function Q(e,t){L(t,!0);const n=nn(t,"className",3,""),r=ua(()=>["aqe-button-icon",n()].filter(Boolean).join(" "));var a=Zf(),o=k(a);{var s=y=>{Nf(y,{size:14,strokeWidth:2})},i=y=>{Ff(y,{size:14,strokeWidth:2})},l=y=>{Cf(y,{size:14,strokeWidth:2})},c=y=>{Rf(y,{size:14,strokeWidth:2})},f=y=>{xf(y,{size:14,strokeWidth:2})},u=y=>{Tf(y,{size:14,strokeWidth:2})},h=y=>{Df(y,{size:14,strokeWidth:2})},m=y=>{Of(y,{size:14,strokeWidth:2})},_=y=>{$f(y,{size:14,strokeWidth:2})},w=y=>{Lf(y,{size:14,strokeWidth:2})},p=y=>{If(y,{size:14,strokeWidth:2})},v=y=>{Bf(y,{size:14,strokeWidth:2})},A=y=>{Gf(y,{size:14,strokeWidth:2})},b=y=>{Vf(y,{size:14,strokeWidth:2})},S=y=>{Hf(y,{size:14,strokeWidth:2})},E=y=>{Wf(y,{size:14,strokeWidth:2})},Z=y=>{jf(y,{size:14,strokeWidth:2})},T=y=>{Uf(y,{size:14,strokeWidth:2})},we=y=>{Kf(y,{size:14,strokeWidth:2})},ue=y=>{Xf(y,{size:14,strokeWidth:2})},yt=y=>{Yf(y,{size:14,strokeWidth:2})},at=y=>{Qf(y,{size:14,strokeWidth:2})};br(o,y=>{t.icon==="audio-lines"?y(s):t.icon==="chart-line"?y(i,1):t.icon==="chevron-down"?y(l,2):t.icon==="circle-help"?y(c,3):t.icon==="fast-forward"?y(f,4):t.icon==="folder-open"?y(u,5):t.icon==="pause"?y(h,6):t.icon==="play"?y(m,7):t.icon==="redo-2"?y(_,8):t.icon==="refresh-cw"?y(w,9):t.icon==="repeat-2"?y(p,10):t.icon==="rewind"?y(v,11):t.icon==="scissors"?y(A,12):t.icon==="settings"?y(b,13):t.icon==="sparkles"?y(S,14):t.icon==="timer-reset"?y(E,15):t.icon==="trash-2"?y(Z,16):t.icon==="undo-2"?y(T,17):t.icon==="volume-1"?y(we,18):t.icon==="volume-2"?y(ue,19):t.icon==="volume-x"?y(yt,20):t.icon==="waves"&&y(at,21)})}zt(()=>Na(a,1,js(P(r)))),O(e,a),I()}function ti(){return document.body.dataset.aqeBusy==="true"}function ni(e,t,n){if(ti())return;const r=$(n);if(!r)return;const a=_o(r,e);yn(r),a&&(typeof t.focus=="function"&&t.focus(),st(r,{clearAudio:!0}),Li(a),window.__aqeActiveField=n,ce.info("region delete request queued",{ord:n,sourceFilename:a.sourceFilename,selectionStartMs:a.selectionStartMs,selectionEndMs:a.selectionEndMs,durationMs:a.durationMs,trigger:e,playbackActive:a.playbackActive}),Vt(n,!0,ja("aqe:delete-selection")),Bt(n,"aqe:delete-selection"))}function Jf(e,t){if(e.key!=="Backspace")return;const n=$(t);if(!(!n||document.activeElement!==n||ti())){if(!_o(n,"backspace")){yn(n);return}e.preventDefault(),ni("backspace",n,t)}}var zf=tn('<button type="button" class="aqe-button aqe-icon-only aqe-repeat-button" title="Repeat selected region, or the whole graph when no region is selected." aria-label="Repeat playback"><!> <span class="aqe-button-label">Repeat</span></button>'),ed=tn('<button type="button" class="aqe-button aqe-menu-item" data-aqe-button-state="default" role="menuitem"><!> <span class="aqe-button-label"> </span></button>'),td=tn('<details class="aqe-menu"><summary class="aqe-button aqe-menu-summary" title="Denoise audio" aria-label="Denoise audio"><!> <span class="aqe-button-label">Denoise</span> <!></summary> <div class="aqe-menu-items" role="menu"></div></details>'),nd=tn('<button type="button"><!> <!> <span class="aqe-button-label"> </span></button> <!> <!>',1),rd=tn('<div class="aqe-controls"><!> <button type="button" class="aqe-button aqe-delete-region-button" data-aqe-command="aqe:delete-selection" data-aqe-button-state="default" title="Delete selected region" aria-label="Delete selected region" hidden=""><!> <span class="aqe-button-label">Delete Region</span></button> <span class="aqe-status"></span> <details class="aqe-help"><summary class="aqe-help-summary" title="Show editor help"><!> <span>Help</span></summary> <div class="aqe-help-body"><section class="aqe-help-section"><h4 class="aqe-help-title">Graph and regions</h4> <ul class="aqe-help-list"><li><kbd>Shift</kbd>-drag on the graph to select a region.</li> <li>Play uses the selected region when one is active; Repeat loops the selected region, or the full graph otherwise.</li> <li>Delete Region removes only the selected region. Backspace does the same when the graph is focused.</li> <li>In the graph, grey is loudness and lines are pitch of the voice.</li></ul></section> <section class="aqe-help-section"><h4 class="aqe-help-title">Buttons</h4> <div class="aqe-help-grid"><span class="aqe-help-item"><span class="aqe-help-command"><!><span>Play</span></span> <span>Start or pause audio.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Graph</span></span> <span>Show pitch and loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Folder</span></span> <span>Open the current audio file.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-L</span></span> <span>Trim 100 ms from the left.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-R</span></span> <span>Trim 100 ms from the right.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Shorten Pauses</span></span> <span>Speed up long internal pauses.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Denoise</span></span> <span>Use Standard or RNNoise cleanup.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Slower</span></span> <span>Decrease speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Faster</span></span> <span>Increase speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume -</span></span> <span>Decrease loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume +</span></span> <span>Increase loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Undo</span></span> <span>Restore the previous edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Redo</span></span> <span>Restore the undone edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Delete Region</span></span> <span>Remove the selected graph region.</span></span></div></section> <p class="aqe-help-note">Every edit creates a new media file and updates the field to point at it. The original file remains in your media collection.</p></div></details> <div class="aqe-visualizer" data-anchor-ms="0" data-cursor-ms="0" data-progress-ms="0" data-graph-active="false" data-graph-busy="false" data-has-track="false" data-playback-state="stopped" data-playback-engine="" data-playback-start-ms="0" data-playback-end-ms="0" data-playback-region-mode="full" data-resume-requires-restart="false" data-selection-active="false" data-selection-start-ms="" data-selection-end-ms="" data-selection-draft-active="false" data-selection-draft-start-ms="" data-selection-draft-end-ms="" role="button" aria-label="Audio graph" tabindex="0" hidden=""><audio class="aqe-audio-clock" preload="metadata" hidden=""></audio> <svg class="aqe-visualizer-svg" preserveAspectRatio="xMinYMin meet" role="img" aria-label="Audio pitch and intensity visualization"><rect class="aqe-selection" width="0" visibility="hidden"></rect><path class="aqe-intensity" d=""></path><g class="aqe-pitch"></g><g class="aqe-labels"></g><g class="aqe-x-axis"></g><line class="aqe-selection-edge aqe-selection-start" visibility="hidden"></line><line class="aqe-selection-edge aqe-selection-end" visibility="hidden"></line><line class="aqe-cursor"></line></svg> <div class="aqe-visualizer-meta"><span class="aqe-spinner" hidden="" aria-hidden="true"></span> <span class="aqe-cursor-label">0 ms</span> <span class="aqe-visualizer-status"></span></div></div></div>');function ad(e,t){var Si;L(t,!0);const n=((Si=window.__AQE_EDITOR_CONFIG__)==null?void 0:Si.repeatPlaybackByDefault)===!0;function r(re){const Pr=re.currentTarget.ariaPressed!=="true";Xl(t.target.ord,Pr)}qf(()=>{const re=$(t.target.ord);re&&(Vl(re),Jl(re),Ul(re))});var a=rd(),o=k(a);Ea(o,17,()=>B,re=>re.command,(re,fe)=>{var Pr=nd(),Ue=H(Pr);let ki;var Ai=k(Ue);Q(Ai,{className:"aqe-button-icon-default",get icon(){return P(fe).icon}});var Ei=N(Ai,2);{var Gd=de=>{Q(de,{className:"aqe-button-icon-active",get icon(){return P(fe).activeIcon}})};br(Ei,de=>{P(fe).activeIcon&&de(Gd)})}var Vd=N(Ei,2),Hd=k(Vd),Pi=N(Ue,2);{var Wd=de=>{var Ie=zf(),Nr=k(Ie);Q(Nr,{icon:"repeat-2"}),zt(()=>{M(Ie,"data-aqe-button-state",n?"active":"default"),M(Ie,"data-testid",`aqe-repeat-${t.target.ord}`),M(Ie,"aria-pressed",n?"true":"false")}),De("mousedown",Ie,Fr=>Fr.preventDefault()),De("click",Ie,r),O(de,Ie)};br(Pi,de=>{P(fe).command==="aqe:play"&&de(Wd)})}var jd=N(Pi,2);{var Ud=de=>{var Ie=td(),Nr=k(Ie),Fr=k(Nr);Q(Fr,{icon:"sparkles"});var Kd=N(Fr,4);Q(Kd,{className:"aqe-menu-chevron",icon:"chevron-down"});var Xd=N(Nr,2);Ea(Xd,21,()=>G,$a=>$a.command,($a,It)=>{var bt=ed(),Ni=k(bt);Q(Ni,{get icon(){return P(It).icon}});var Yd=N(Ni,2),Qd=k(Yd);zt(La=>{M(bt,"data-aqe-command",P(It).command),M(bt,"data-testid",La),M(bt,"title",P(It).title),M(bt,"aria-label",P(It).title),Gs(Qd,P(It).label)},[()=>xr(t.target.ord,P(It).command)]),De("mousedown",bt,La=>La.preventDefault()),De("click",bt,()=>So(P(It).command,t.target.node,t.target.ord)),O($a,bt)}),zt(()=>M(Ie,"data-testid",`aqe-denoise-menu-${t.target.ord}`)),O(de,Ie)};br(jd,de=>{P(fe).command==="aqe:remove-pauses"&&de(Ud)})}zt(de=>{ki=Na(Ue,1,"aqe-button",null,ki,{"aqe-icon-only":P(fe).iconOnly===!0}),M(Ue,"data-aqe-command",P(fe).command),M(Ue,"data-aqe-button-state",P(fe).command==="aqe:play"?"play":P(fe).command==="aqe:analyze"?"graph":"default"),M(Ue,"data-testid",de),M(Ue,"title",P(fe).title),M(Ue,"aria-label",P(fe).title),Gs(Hd,P(fe).label)},[()=>xr(t.target.ord,P(fe).command)]),De("mousedown",Ue,de=>de.preventDefault()),De("click",Ue,()=>So(P(fe).command,t.target.node,t.target.ord)),O(re,Pr)});var s=N(o,2),i=k(s);Q(i,{icon:"trash-2"});var l=N(s,2),c=N(l,2),f=k(c),u=k(f);Q(u,{icon:"circle-help"});var h=N(f,2),m=N(k(h),2),_=N(k(m),2),w=k(_),p=k(w),v=k(p);Q(v,{icon:"play"});var A=N(w,2),b=k(A),S=k(b);Q(S,{icon:"audio-lines"});var E=N(A,2),Z=k(E),T=k(Z);Q(T,{icon:"folder-open"});var we=N(E,2),ue=k(we),yt=k(ue);Q(yt,{icon:"scissors"});var at=N(we,2),y=k(at),Sr=k(y);Q(Sr,{icon:"scissors"});var Wn=N(at,2),kr=k(Wn),Ar=k(kr);Q(Ar,{icon:"timer-reset"});var jn=N(Wn,2),Er=k(jn),Le=k(Er);Q(Le,{icon:"sparkles"});var Un=N(jn,2),Sd=k(Un),kd=k(Sd);Q(kd,{icon:"rewind"});var hi=N(Un,2),Ad=k(hi),Ed=k(Ad);Q(Ed,{icon:"fast-forward"});var pi=N(hi,2),Pd=k(pi),Nd=k(Pd);Q(Nd,{icon:"volume-1"});var _i=N(pi,2),Fd=k(_i),Cd=k(Fd);Q(Cd,{icon:"volume-2"});var mi=N(_i,2),Rd=k(mi),xd=k(Rd);Q(xd,{icon:"undo-2"});var vi=N(mi,2),Td=k(vi),Dd=k(Td);Q(Dd,{icon:"redo-2"});var Od=N(vi,2),$d=k(Od),Ld=k($d);Q(Ld,{icon:"trash-2"});var Kn=N(c,2),gi=k(Kn),Xn=N(gi,2),Yn=k(Xn),yi=N(Yn),bi=N(yi),wi=N(bi,2),dn=N(wi),hn=N(dn),Qn=N(hn),Id=N(Xn,2),qi=k(Id),Mi=N(qi,2),Bd=N(Mi,2);zt(re=>{M(a,"data-aqe-field-ord",t.target.ord),M(a,"data-aqe-source-filename",t.target.sourceFilename),M(a,"data-testid",`aqe-controls-${t.target.ord}`),M(s,"data-testid",re),M(l,"data-testid",`aqe-status-${t.target.ord}`),M(c,"data-testid",`aqe-help-${t.target.ord}`),M(Kn,"data-aqe-field-ord",t.target.ord),M(Kn,"data-repeat-enabled",n?"true":"false"),M(Kn,"data-testid",`aqe-graph-${t.target.ord}`),M(gi,"data-testid",`aqe-audio-clock-${t.target.ord}`),M(Xn,"data-testid",`aqe-graph-svg-${t.target.ord}`),M(Xn,"viewBox",`0 0 ${q.width} ${q.height}`),M(Yn,"data-testid",`aqe-selection-${t.target.ord}`),M(Yn,"x",q.left),M(Yn,"y",q.top),M(Yn,"height",q.height-q.top-q.bottom),M(yi,"data-testid",`aqe-intensity-${t.target.ord}`),M(bi,"data-testid",`aqe-pitch-${t.target.ord}`),M(wi,"data-testid",`aqe-x-axis-${t.target.ord}`),M(dn,"data-testid",`aqe-selection-start-${t.target.ord}`),M(dn,"x1",q.left),M(dn,"x2",q.left),M(dn,"y1",q.top),M(dn,"y2",q.height-q.bottom),M(hn,"data-testid",`aqe-selection-end-${t.target.ord}`),M(hn,"x1",q.left),M(hn,"x2",q.left),M(hn,"y1",q.top),M(hn,"y2",q.height-q.bottom),M(Qn,"data-testid",`aqe-cursor-${t.target.ord}`),M(Qn,"x1",q.left),M(Qn,"x2",q.left),M(Qn,"y1",q.top),M(Qn,"y2",q.height-q.bottom),M(qi,"data-testid",`aqe-graph-spinner-${t.target.ord}`),M(Mi,"data-testid",`aqe-progress-label-${t.target.ord}`),M(Bd,"data-testid",`aqe-graph-status-${t.target.ord}`)},[()=>xr(t.target.ord,"aqe:delete-selection")]),De("mousedown",s,re=>re.preventDefault()),De("click",s,()=>ni("button",t.target.node,t.target.ord)),De("keydown",Kn,re=>Jf(re,t.target.ord)),De("pointerdown",Xn,re=>nu(re,t.target.ord)),O(e,a),I()}Ls(["mousedown","click","keydown","pointerdown"]);const rn=new Map;function od(e){const t=rn.get(e.ord);if(t){if(document.body.contains(t.host)||ri(e,t.host),Ra(e.ord,t.host),!e.sourceFilename||t.sourceFilename===e.sourceFilename)return t;const o=$(e.ord);if((o==null?void 0:o.dataset.graphBusy)==="true"||(o==null?void 0:o.dataset.hasTrack)==="true"){const s=o.dataset.sourceFilename||e.sourceFilename;t.sourceFilename=s;const i=document.querySelector(`.aqe-controls[data-aqe-field-ord="${e.ord}"]`);return i&&(i.dataset.aqeSourceFilename=s),Ra(e.ord,t.host),t}}sd(e.ord);const n=document.createElement("div");n.className="aqe-mount-host",ri(e,n);const a={component:ef(ad,{target:n,props:{target:e}}),host:n,ord:e.ord,sourceFilename:e.sourceFilename};return rn.set(e.ord,a),Ra(e.ord,n),a}function sd(e){const t=rn.get(e);t&&(Vs(t.component),t.host.remove(),rn.delete(e)),document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>n.remove())}function id(){for(const e of rn.values())Vs(e.component),e.host.remove();rn.clear(),ld()}function ri(e,t){const n=e.node.closest(".field-container")||e.node.closest(".field")||e.node.parentElement||e.node;n.parentElement?n.after(t):e.node.after(t)}function Ra(e,t){document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>{t.contains(n)||n.remove()}),document.querySelectorAll(".aqe-mount-host").forEach(n=>{n!==t&&!n.querySelector(".aqe-controls")&&n.remove()})}function ld(){document.querySelectorAll(".aqe-mount-host").forEach(e=>e.remove()),document.querySelectorAll(".aqe-controls").forEach(e=>e.remove())}function ud(){window.__aqeGraphStateForTest=hd,window.__aqeInstallAudioPlaybackTestDriverForTest=cd,window.__aqeSetCursorByClientXForTest=dd,window.__aqeSetCursorForTest=fd}function cd(e){const t=$(e),n=Pe(t);return!t||!n?!1:(n.__aqeTestDriverInstalled=!0,n.pause=function(){n.__aqeTestPlaying=!1,n.__aqeTestFrame&&(window.cancelAnimationFrame(n.__aqeTestFrame),n.__aqeTestFrame=null)},n.play=function(){n.__aqeTestPlaying=!0,n.__aqeTestLastNow=performance.now();const a=()=>{if(!n.__aqeTestPlaying)return;const o=performance.now(),s=Number(t.dataset.durationMs||"0")/1e3,i=Math.max(0,(o-Number(n.__aqeTestLastNow||o))/1e3);if(n.__aqeTestLastNow=o,n.currentTime=Math.min(s,(Number(n.currentTime)||0)+i),s&&n.currentTime>=s){n.__aqeTestPlaying=!1,n.dispatchEvent(new Event("ended"));return}n.__aqeTestFrame=window.requestAnimationFrame(a)};return n.__aqeTestFrame=window.requestAnimationFrame(a),Promise.resolve()},!0)}function fd(e,t,n){const r=$(e);return r?(r.hidden=!1,r.dataset.graphActive="true",qt(r,t,!!n),!0):!1}function dd(e,t,n){var i;const r=$(e),a=(r==null?void 0:r.querySelector(".aqe-visualizer-svg"))??null;if(!r||!a)return null;const o=Number(r.dataset.durationMs||"0"),s=vn({clientX:t},a,o);return qt(r,s,!!n),{cursorMs:Number(r.dataset.cursorMs||"0"),cursorX:Number(((i=r.querySelector(".aqe-cursor"))==null?void 0:i.getAttribute("x1"))||"0"),bounds:lo(a)}}function hd(e){var c,f,u,h,m;const t=$(e),n=Ka(e),r=Xa(e),a=((c=Xe(e))==null?void 0:c.querySelector(".aqe-delete-region-button"))??null;if(!t)return null;const o=Jn().flatMap(_=>Array.from(_.querySelectorAll(".aqe-button-icon svg"))),s=Pe(t),i=ko(t),l=Ao(t);return{active:t.dataset.graphActive==="true",busy:t.dataset.graphBusy==="true",hidden:!!t.hidden,hasTrack:t.dataset.hasTrack==="true",durationMs:Number(t.dataset.durationMs||"0"),anchorMs:Number(t.dataset.anchorMs||"0"),cursorMs:Number(t.dataset.cursorMs||"0"),progressMs:Number(t.dataset.progressMs||"0"),sourceFilename:t.dataset.sourceFilename||"",graphButtonLabel:ai(n),graphButtonState:(n==null?void 0:n.dataset.aqeButtonState)||"",graphButtonTitle:(n==null?void 0:n.title)||"",playButtonLabel:ai(r),playButtonState:(r==null?void 0:r.dataset.aqeButtonState)||"",playbackState:pd(t),selectionActive:i!==null,selectionStartMs:(i==null?void 0:i.startMs)??null,selectionEndMs:(i==null?void 0:i.endMs)??null,selectionDraftActive:l!==null,selectionDraftStartMs:(l==null?void 0:l.startMs)??null,selectionDraftEndMs:(l==null?void 0:l.endMs)??null,repeatEnabled:t.dataset.repeatEnabled==="true",repeatControlDisabled:!!((f=Ya(e))!=null&&f.disabled),regionDeleteButtonDisabled:!!(a!=null&&a.disabled),regionDeleteButtonHidden:a?!!a.hidden:!0,playbackStartMs:Number(t.dataset.playbackStartMs||"0"),playbackEndMs:Number(t.dataset.playbackEndMs||"0"),playbackRegionMode:t.dataset.playbackRegionMode==="selection"?"selection":"full",resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true",audioClockSrc:s&&s.getAttribute("src")||"",audioClockCurrentMs:s?Math.round((Number(s.currentTime)||0)*1e3):0,audioClockReady:!!(s&&t.__aqeAudioClockAvailable),audioClockFallback:!!t.__aqeAudioClockFallback,audioClockMuted:!!(s&&s.muted),audioPlaybackTestDriver:!!(s&&s.__aqeTestDriverInstalled),playbackEngine:qn(t),progressClockMode:_d(t),xAxisLabels:Array.from(t.querySelectorAll(".aqe-x-label")).map(_=>_.textContent||""),pitchPaths:t.querySelectorAll(".aqe-pitch-path").length,intensity:((u=t.querySelector(".aqe-intensity"))==null?void 0:u.getAttribute("d"))||"",cursorX:Number(((h=t.querySelector(".aqe-cursor"))==null?void 0:h.getAttribute("x1"))||"0"),spinnerVisible:t.querySelector(".aqe-spinner")?!((m=t.querySelector(".aqe-spinner"))!=null&&m.hidden):!1,allButtonsDisabled:Jn().every(_=>_.disabled),anyButtonDisabled:Jn().some(_=>_.disabled),buttonIconCount:o.length,buttonIconStrokeValues:o.map(_=>_.getAttribute("stroke")||getComputedStyle(_).stroke||"")}}function pd(e){const t=e.dataset.playbackState;return Lr(t)?t:"stopped"}function _d(e){const t=e.dataset.progressClockMode;return t==="audio"||t==="manual"||t==="stopped"?t:"stopped"}function ai(e){var t;return((t=e==null?void 0:e.querySelector(".aqe-button-label"))==null?void 0:t.textContent)||(e==null?void 0:e.textContent)||""}function md(){window.__aqeSetBusy=Vt,window.__aqeSetStatus=Mo,window.__aqeSetVisualizer=au,window.__aqeSetVisualizerStatus=ou,window.__aqeResetGraphAfterEdit=ru,window.__aqeSetPlaybackState=cu,window.__aqeGetPlaybackRequest=fu,window.__aqeStopEditorPlayback=du,window.__aqeGetCursorMs=hu,window.__aqeGetCursorIntent=pu,window.__aqePrepareForNewNote=Co,window.__aqePopFrontendLog=Ti,window.__aqePopPendingGraphAnalysisRequest=$i,window.__aqePopPendingRegionDeleteRequest=Ii,ud()}const vd=/\[sound:([^\]]+)\]/i,gd=/\.(aac|flac|m4a|mp3|oga|ogg|opus|wav|webm)$/i;let In=[];function yd(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){oi(),window.__AQE_EDITOR_CONFIG__=e,md(),Co(),Ji(),window.__aqeEditorDispose=oi,ce.info("editor runtime initialized",{audioFieldIndices:e.audioFieldIndices,showGraphByDefault:e.showGraphByDefault===!0});const t=()=>bd(e);window.__aqeScan=t,Ta(t,0),Ta(t,250),Ta(t,1e3)}function oi(){In.forEach(e=>window.clearTimeout(e)),In=[],id()}function bd(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){if(e.audioFieldIndices.length){const r=qd(e.audioFieldIndices,e.audioFieldSources);r.forEach(a=>si(a)),ce.debug("scan mounted explicit fields",{count:r.length}),Yr(),ii(e,r);return}const t=[];let n=0;wd().forEach((r,a)=>{const o=xa(r);if(!o)return;const s={node:r,ord:Md(r,a),sourceFilename:o};si(s),t.push(s),n+=1}),ce.debug("scan mounted detected fields",{count:n}),Yr(),ii(e,t)}function wd(){const e=Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]')),t=new Set;return e.filter(n=>t.has(n)?!1:(t.add(n),!!(n.textContent||n.innerHTML)))}function qd(e,t={}){return e.map(n=>{const r=document.querySelector(`.field-container[data-index="${n}"]`);if(!r)return null;const a=r.querySelector('[contenteditable="true"]')||r,o=xa(a)||xa(r)||t[n]||"";return{ord:n,node:a,sourceFilename:o}}).filter(n=>n!==null)}function Md(e,t){const n=["data-field-ord","data-ord","data-index"];for(const a of n){const o=e.getAttribute(a);if(o!==null&&/^\d+$/.test(o))return Number(o)}const r=/(\d+)/.exec(String(e.id||""));return r?Number(r[1]):t}function xa(e){const t=e.innerHTML||e.textContent||"",n=vd.exec(t),r=n==null?void 0:n[1];return r&&gd.test(r)?r:""}function si(e){od(e)}function ii(e,t){e.showGraphByDefault&&zi(t.map(({ord:n,sourceFilename:r})=>({ord:n,sourceFilename:r})),{anyBusy:()=>document.body.dataset.aqeBusy==="true",requestDefaultGraph:No})}function Ta(e,t){const n=window.setTimeout(()=>{In=In.filter(r=>r!==n),e()},t);In.push(n)}yd()})();
