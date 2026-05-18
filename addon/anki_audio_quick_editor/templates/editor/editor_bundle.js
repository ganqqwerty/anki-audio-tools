var kp=Object.defineProperty;var Ji=W=>{throw TypeError(W)};var Ep=(W,j,re)=>j in W?kp(W,j,{enumerable:!0,configurable:!0,writable:!0,value:re}):W[j]=re;var nt=(W,j,re)=>Ep(W,typeof j!="symbol"?j+"":j,re),po=(W,j,re)=>j.has(W)||Ji("Cannot "+re);var p=(W,j,re)=>(po(W,j,"read from private field"),re?re.call(W):j.get(W)),T=(W,j,re)=>j.has(W)?Ji("Cannot add the same private member more than once"):j instanceof WeakSet?j.add(W):j.set(W,re),C=(W,j,re,Cn)=>(po(W,j,"write to private field"),Cn?Cn.call(W,re):j.set(W,re),re),ie=(W,j,re)=>(po(W,j,"access private method"),re);(function(){"use strict";var Oi,Li,Ii,bn,yn,Wt,wn,ar,or,jt,dt,qn,Me,ho,mo,_o,zi,Re,ao,Ye,$t,be,Qe,ke,We,pt,Ut,At,Sn,Mn,kn,Ze,Hr,ae,Ap,Pp,Fp,vo,Kr,Yr,go,Bi,je,Je,Ee,Xt,sr,ir,Wr,Vi;const W=[{activeIcon:"pause",command:"aqe:play",icon:"play",iconOnly:!0,label:"Play",title:"Play or pause current audio"},{activeIcon:"refresh-cw",command:"aqe:analyze",icon:"chart-line",iconOnly:!0,label:"Graph",title:"Analyze and show pitch/intensity graph"},{command:"aqe:show-file",icon:"folder-open",label:"Folder",title:"Show current audio file in folder"},{command:"aqe:trim-left",icon:"scissors",label:"-L",title:"Trim 100 ms from left"},{command:"aqe:trim-right",icon:"scissors",label:"-R",title:"Trim 100 ms from right"},{command:"aqe:remove-pauses",icon:"timer-reset",label:"Shorten Pauses",title:"Speed up long internal pauses"},{command:"aqe:slower",icon:"rewind",label:"Slower",title:"Decrease speed"},{command:"aqe:faster",icon:"fast-forward",label:"Faster",title:"Increase speed"},{command:"aqe:volume-down",icon:"volume-1",iconOnly:!0,label:"Volume -",title:"Decrease volume"},{command:"aqe:volume-up",icon:"volume-2",iconOnly:!0,label:"Volume +",title:"Increase volume"},{command:"aqe:undo",icon:"undo-2",iconOnly:!0,label:"Undo",title:"Restore the previous generated audio reference"},{command:"aqe:redo",icon:"redo-2",iconOnly:!0,label:"Redo",title:"Restore the most recently undone audio reference"},{command:"aqe:settings",icon:"settings",iconOnly:!0,label:"Settings",title:"Open Audio Quick Editor settings"}],j=[{command:"aqe:denoise-standard",icon:"volume-x",label:"Standard",title:"Denoise speech with DeepFilterNet"},{command:"aqe:rnnoise",icon:"waves",label:"RNNoise",title:"Denoise speech with RNNoise"}],re=new Set(["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:remove-pauses","aqe:denoise-standard","aqe:rnnoise","aqe:volume-down","aqe:volume-up"]),Cn={"aqe:play":"play","aqe:analyze":"graph","aqe:show-file":"show-file","aqe:delete-selection":"delete-selection","aqe:trim-left":"trim-left","aqe:trim-right":"trim-right","aqe:remove-pauses":"remove-pauses","aqe:denoise-standard":"denoise-standard","aqe:rnnoise":"rnnoise","aqe:slower":"slower","aqe:faster":"faster","aqe:volume-down":"volume-down","aqe:volume-up":"volume-up","aqe:undo":"undo","aqe:redo":"redo","aqe:settings":"settings"};function Qr(e,t){return`aqe-button-${e}-${Cn[t]}`}function bo(e){return e==="aqe:denoise-standard"?"Denoising with Standard...":e==="aqe:rnnoise"?"Denoising with RNNoise...":e==="aqe:delete-selection"?"Deleting region...":"Processing..."}function rt(e){return document.querySelector(`.aqe-controls[data-aqe-field-ord="${e}"]`)}function B(e){return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${e}"]`)}function yo(e,t){const n=rt(e);return(n==null?void 0:n.querySelector(`[data-aqe-command="${t}"]`))??null}function wo(e){return yo(e,"aqe:analyze")}function qo(e){return yo(e,"aqe:play")}function So(e){const t=rt(e);return(t==null?void 0:t.querySelector(".aqe-repeat-button"))??null}function _r(){return Array.from(document.querySelectorAll(".aqe-button"))}function Zr(){return Array.from(document.querySelectorAll(".aqe-visualizer"))}const Mo=[];let vr=null,gr=null;function zt(e){globalThis.pycmd!==void 0&&globalThis.pycmd(e)}function en(e,t){zt(`focus:${e}`),zt(t)}function el(e,t){zt(`focus:${e}`),window.__aqePendingCommandPayload=t,zt("aqe:command-payload")}function tl(e){vr=e,zt("aqe:analyze-field")}function nl(e){Mo.push(e),zt("aqe:frontend-log")}function rl(){return Mo.shift()??null}function al(e){window.__aqePendingPlaybackRequest=e,window.__aqeLastPlaybackRequest=e}function ol(){if(!window.__aqePendingPlaybackRequest)return null;const e=window.__aqePendingPlaybackRequest;return window.__aqePendingPlaybackRequest=null,e}function sl(){if(!vr)return null;const e=vr;return vr=null,e}function il(e){gr=e}function ll(){if(!gr)return null;const e=gr;return gr=null,e}function ul(e){window.__aqeLastCursorIntent=e}function cl(e){return encodeURIComponent(e||"").replaceAll("%2F","/")}function Oe(e){return(e==null?void 0:e.querySelector(".aqe-audio-clock"))??null}function Jr(e){e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!1,e.__aqeAudioClockLastSeekedMs=0,e.dataset.progressClockMode="stopped"}function xn(e){const t=Oe(e);if(!(!t||typeof t.pause!="function"))try{t.pause()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function zr(e){const t=Oe(e);if(Jr(e),!!t){xn(e),t.removeAttribute("src"),t.src="";try{t.load()}catch{e.__aqeAudioClockFallback=!0}}}function fl(e,t){const n=Oe(e);if(Jr(e),!n){e.__aqeAudioClockFallback=!0;return}if(xn(e),!t){zr(e);return}n.setAttribute("src",cl(t));try{n.load()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function dl(e,t={}){const n=Oe(e);!n||n.__aqeClockHandlersInstalled||(n.__aqeClockHandlersInstalled=!0,n.addEventListener("loadedmetadata",()=>{n.getAttribute("src")&&(e.__aqeAudioClockAvailable=!0,e.__aqeAudioClockFallback=!1)}),n.addEventListener("error",()=>{var r;e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,e.dataset.playbackState==="playing"&&e.dataset.progressClockMode==="audio"&&((r=t.onErrorDuringPlayback)==null||r.call(t))}),n.addEventListener("ended",()=>{var r;e.dataset.playbackState==="playing"&&((r=t.onEndedDuringPlayback)==null||r.call(t))}),n.addEventListener("seeked",()=>{e.__aqeAudioClockLastSeekedMs=Math.round((Number(n.currentTime)||0)*1e3)}))}function br(e){const t=Oe(e);return!t||!(e!=null&&e.__aqeAudioClockAvailable)||!t.getAttribute("src")?!1:t.readyState===void 0||t.readyState>=1}function yr(e,t,n){const r=Oe(e);if(!r)return!1;const a=Math.max(0,Math.min(Number(t)||0,n||0));try{return r.currentTime=a/1e3,e.__aqeAudioClockLastSeekedMs=Math.round(a),!0}catch{return e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,!1}}var Tn=(e=>(e.Debug="debug",e.Error="error",e.Info="info",e.Unknown="unknown",e.Warn="warn",e))(Tn||{});function pl(e){return e==="error"?console.error:console.warn}function hl(e){return e==="debug"?Tn.Debug:e==="warn"?Tn.Warn:e==="error"?Tn.Error:Tn.Info}function ea(e,t=0){const n=ml(e);return n!==void 0?n:Array.isArray(e)?_l(e,t):e!==null&&typeof e=="object"?vl(e,t):gl(e)}function ml(e){if(e===void 0)return"[undefined]";if(e===null)return null;if(typeof e=="boolean"||typeof e=="number"||typeof e=="string")return e}function _l(e,t){return t>=4?"[array]":e.map(n=>ea(n,t+1))}function vl(e,t){if(t>=4)return"[object]";const n={};for(const[r,a]of Object.entries(e))n[r]=ea(a,t+1);return n}function gl(e){return typeof e=="bigint"?e.toString():typeof e=="symbol"?e.description?`Symbol(${e.description})`:"Symbol()":typeof e=="function"?`[function ${e.name||"anonymous"}]`:"[unserializable]"}function bl(e,t,n){const r={level:hl(e),message:t};return n!==void 0&&(r.context=ea(n)),r}function yl(e,t){function n(r,a,o){const s=pl(r);o===void 0?s(`[${e}] ${a}`):s(`[${e}] ${a}`,o);try{t(bl(r,a,o))}catch{}}return{debug:(r,a)=>n("debug",r,a),error:(r,a)=>n("error",r,a),info:(r,a)=>n("info",r,a),warn:(r,a)=>n("warn",r,a)}}const he=yl("editor",nl),Rn=[],wr=new Set;let qr=null,Sr=null,Mr=!1;function wl(){Rn.length=0,wr.clear(),qr=null,Sr=null,Mr=!1}function ql(e,t){for(const n of e){if(!n.sourceFilename)continue;const r=Sl(n);if(wr.has(r))continue;const a=B(n.ord);if((a==null?void 0:a.dataset.hasTrack)==="true"&&a.dataset.sourceFilename===n.sourceFilename){wr.add(r);continue}wr.add(r),Rn.push({key:r,ord:n.ord,sourceFilename:n.sourceFilename})}kr(t)}function kr(e){if(!(qr!==null||e.anyBusy()))for(;Rn.length;){const t=Rn.shift();if(!t)return;const n=B(t.ord);if(!n){Eo(t,e);return}const r=rt(t.ord);if(!r){Eo(t,e);return}if((r.dataset.aqeSourceFilename||t.sourceFilename)===t.sourceFilename&&!(n.dataset.hasTrack==="true"&&n.dataset.sourceFilename===t.sourceFilename)){qr=t.key,Sr=t.ord,e.requestDefaultGraph({ord:t.ord,sourceFilename:t.sourceFilename});return}}}function ko(e,t){Sr===e&&(qr=null,Sr=null,queueMicrotask(()=>kr(t)))}function Sl(e){return`${e.ord}\0${e.sourceFilename}`}function Eo(e,t){Rn.unshift(e),!Mr&&(Mr=!0,window.setTimeout(()=>{Mr=!1,kr(t)},0))}function Ml(e,t){return Math.max(t.startMs,Math.min(Number(e)||0,t.endMs))}function kl(e){let t="start";e.playbackState==="playing"&&(t="pause"),e.playbackState==="paused"&&(t=e.resumeRequiresRestart?"start":"resume");let n=e.anchorMs;return t==="start"&&e.region.mode==="selection"&&(n=e.region.startMs),t==="pause"&&(n=Ao(e.currentProgressMs,e.cursorMs,n)),t==="resume"&&(n=Ao(e.currentProgressMs,e.cursorMs,n),e.region.mode==="selection"&&(n<e.region.startMs||n>e.region.endMs)&&(t="start",n=e.region.startMs)),{action:t,cursorMs:Math.round(n),endMs:Math.round(e.region.endMs),engine:e.engine,loop:e.repeat,ord:e.ord,regionMode:e.region.mode}}function Ao(e,t,n){return Number(e||t||n||0)}function El(e){return{analyzerName:e.analyzerName,durationMs:Number(e.durationMs)||0,pitchMaxHz:e.pitchMaxHz,pitchMinHz:e.pitchMinHz,points:e.points.map(Al),sourceFilename:e.sourceFilename}}function Al(e){const t=typeof e[0]=="number"?e[0]:0,n=typeof e[1]=="number"?e[1]:null,r=typeof e[2]=="number"?e[2]:null,a=typeof e[3]=="boolean"?e[3]:!1;return[t,n,r,a]}function ta(e){return e==="playing"||e==="paused"||e==="stopped"}const Po=50,Pl=4;function Fo(){return{active:!1,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:null,startMs:null}}function No(e,t){return Math.max(0,Math.min(Number(e)||0,Math.max(0,Number(t)||0)))}function Er(e,t,n,r=Po){const a=No(Math.min(e,t),n),o=No(Math.max(e,t),n);return!n||o-a<r?null:{startMs:Math.round(a),endMs:Math.round(o)}}function Fl(e,t){if(!e.active||e.startMs===null||e.endMs===null)return null;const n=Er(e.startMs,e.endMs,t);return n?{...n,mode:"selection"}:null}function Nl(e,t){if(!e.draftActive||e.draftStartMs===null||e.draftEndMs===null)return null;const n=Er(e.draftStartMs,e.draftEndMs,t);return n?{...n,mode:"selection"}:null}function Cl(e,t,n,r){const a=Er(t,n,r);return a?{...e,active:!0,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:a.endMs,startMs:a.startMs}:Tl(e)}function xl(e,t,n,r){const a=Er(t,n,r);return a?{...e,draftActive:!0,draftEndMs:a.endMs,draftStartMs:a.startMs}:Co(e)}function Tl(e){return{...Co(e),active:!1,endMs:null,startMs:null}}function Co(e){return{...e,draftActive:!1,draftEndMs:null,draftStartMs:null}}function xo(e,t,n,r){return Math.abs(t.clientX-e.clientX)<Pl||Math.abs(r-n)<Po}const k={width:620,height:150,left:44,right:10,top:10,bottom:34};function To(){return k.width-k.left-k.right}function Ro(){return k.height-k.top-k.bottom}function _t(e,t){return t?k.left+Math.max(0,Math.min(1,e/t))*To():k.left}function Rl(e,t,n){if(!e||!t||!n||n<=t)return k.height-k.bottom;const r=Math.max(0,Math.min(1,(e-t)/(n-t)));return k.top+(1-r)*Ro()}function Do(e,t){return t&&t<2e3?`${Math.round(e)} ms`:`${(e/1e3).toFixed(2)}s`}function Dl(e,t){if(!e.length||!t)return"";const n=k.height-k.bottom,r=e[0];if(!r)return"";const a=`M ${_t(r[0],t).toFixed(2)} ${n.toFixed(2)}`,o=e.map(l=>{const f=_t(l[0],t).toFixed(2),c=Math.max(0,Math.min(1,l[2]??0)),u=(n-c*Ro()).toFixed(2);return`L ${f} ${u}`}).join(" "),s=e.at(-1)??r,i=`L ${_t(s[0],t).toFixed(2)} ${n.toFixed(2)} Z`;return`${a} ${o} ${i}`}function Ol(e,t,n,r){const a=[];let o=[];for(const s of e){const i=s[1];if(!(s[3]===!0&&i!==null&&i!==void 0)){o.length&&a.push(o),o=[];continue}o.push([_t(s[0],t),Rl(i,n,r)])}return o.length&&a.push(o),a}function Ll(e,t){const n=e.querySelector(".aqe-pitch");if(n){n.textContent="";for(const r of Ol(t.points,t.durationMs,t.pitchMinHz,t.pitchMaxHz)){if(r.length<2)continue;const a=document.createElementNS("http://www.w3.org/2000/svg","path");a.setAttribute("class","aqe-pitch-path"),a.setAttribute("d",r.map((o,s)=>{const i=o[0]??0,l=o[1]??0;return`${s?"L":"M"} ${i.toFixed(2)} ${l.toFixed(2)}`}).join(" ")),n.appendChild(a)}}}function Il(e,t){const n=e.querySelector(".aqe-labels");if(!n)return;n.textContent="";const r=t.pitchMaxHz||500,a=t.pitchMinHz||75;for(const o of[[r,k.top+10],[a,k.height-k.bottom]]){const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","aqe-hz-label"),s.setAttribute("x","2"),s.setAttribute("y",String(o[1])),s.textContent=`${Math.round(o[0])} Hz`,n.appendChild(s)}}function Bl(e,t){const n=e.querySelector(".aqe-x-axis");if(!n)return;n.textContent="";const r=[0,t/2,t].filter((a,o,s)=>o===0||a!==s[o-1]);for(const a of r){const o=_t(a,t),s=document.createElementNS("http://www.w3.org/2000/svg","line");s.setAttribute("class","aqe-x-tick"),s.setAttribute("x1",o.toFixed(2)),s.setAttribute("x2",o.toFixed(2)),s.setAttribute("y1",String(k.height-k.bottom)),s.setAttribute("y2",String(k.height-k.bottom+4));const i=document.createElementNS("http://www.w3.org/2000/svg","text");i.setAttribute("class","aqe-x-label"),i.setAttribute("x",o.toFixed(2)),i.setAttribute("y",String(k.height-8)),i.textContent=Do(a,t),n.append(s,i)}}function Oo(e){const t=e.getBoundingClientRect(),n=Number(t.width)||k.width,r=Number(t.height)||k.height,a=Math.min(n/k.width,r/k.height)||1;return{left:t.left+k.left*a,width:To()*a}}function Dn(e,t,n){const r=Oo(t);return Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*n}function Vl(e){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="true",e.dataset.hasTrack="false",e.dataset.durationMs="0",e.dataset.sourceFilename="",e.dataset.anchorMs="0",e.dataset.cursorMs="0",e.dataset.progressMs="0",e.dataset.resumeRequiresRestart="false",e.dataset.playbackEngine="",e.dataset.playbackStartMs="0",e.dataset.playbackEndMs="0",e.dataset.playbackRegionMode="full",Lo(e)}function Gl(e,t){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="false",e.dataset.hasTrack="true",e.dataset.durationMs=String(t.durationMs||0),e.dataset.analyzerName=t.analyzerName||"",e.dataset.sourceFilename=t.sourceFilename||"";const n=e.querySelector(".aqe-intensity");n&&n.setAttribute("d",Dl(t.points,t.durationMs)),Ll(e,t),Il(e,t),Bl(e,t.durationMs||0)}function Hl(e,t,n="info"){const r=e.querySelector(".aqe-visualizer-status"),a=e.querySelector(".aqe-spinner"),o=n==="processing";e.dataset.graphBusy=o?"true":"false",a&&(a.hidden=!o),r&&(r.textContent=t||"",r.dataset.kind=n||"info")}function Wl(e,t,n){const r=e.querySelector(".aqe-selection"),a=e.querySelector(".aqe-selection-start"),o=e.querySelector(".aqe-selection-end"),s=n??t,i=Number(e.dataset.durationMs||"0");if(!r||!a||!o||!s||!i){r==null||r.setAttribute("width","0"),r==null||r.setAttribute("visibility","hidden"),r==null||r.classList.remove("aqe-selection-draft"),a==null||a.setAttribute("visibility","hidden"),o==null||o.setAttribute("visibility","hidden");return}const l=_t(s.startMs,i),f=_t(s.endMs,i);r.setAttribute("visibility","visible"),r.classList.toggle("aqe-selection-draft",n!==null),r.setAttribute("x",l.toFixed(2)),r.setAttribute("y",String(k.top)),r.setAttribute("width",Math.max(0,f-l).toFixed(2)),r.setAttribute("height",String(k.height-k.top-k.bottom)),a.setAttribute("visibility","visible"),o.setAttribute("visibility","visible");for(const[c,u]of[[a,l],[o,f]])c.setAttribute("x1",u.toFixed(2)),c.setAttribute("x2",u.toFixed(2)),c.setAttribute("y1",String(k.top)),c.setAttribute("y2",String(k.height-k.bottom))}function jl(e,t,n){const r=_t(t,n),a=e.querySelector(".aqe-cursor");a&&(a.setAttribute("x1",r.toFixed(2)),a.setAttribute("x2",r.toFixed(2)));const o=e.querySelector(".aqe-cursor-label");o&&(o.textContent=Do(t,n))}function Lo(e){var t;(t=e.querySelector(".aqe-intensity"))==null||t.setAttribute("d",""),na(e,".aqe-pitch"),na(e,".aqe-labels"),na(e,".aqe-x-axis")}function $l(e){const t=e.querySelector(".aqe-cursor");t&&(t.setAttribute("x1",String(k.left)),t.setAttribute("x2",String(k.left)));const n=e.querySelector(".aqe-cursor-label");n&&(n.textContent="0 ms")}function Ul(e,t){return{analyzerName:t.analyzerName,durationMs:t.durationMs,ord:e,points:t.points.length,sourceFilename:t.sourceFilename}}function na(e,t){const n=e.querySelector(t);n&&(n.textContent="")}function On(e){return!e||e.dataset.selectionActive!=="true"?null:Fl({active:e.dataset.selectionActive==="true",startMs:Number(e.dataset.selectionStartMs||"0"),endMs:Number(e.dataset.selectionEndMs||"0")},Number(e.dataset.durationMs||"0"))}function ra(e){return!e||e.dataset.selectionDraftActive!=="true"?null:Nl({draftActive:e.dataset.selectionDraftActive==="true",draftStartMs:Number(e.dataset.selectionDraftStartMs||"0"),draftEndMs:Number(e.dataset.selectionDraftEndMs||"0")},Number(e.dataset.durationMs||"0"))}function Io(e){const t=On(e);return t||{startMs:0,endMs:Number(e.dataset.durationMs||"0")||0,mode:"full"}}function tn(e,t={}){e.dataset.selectionDraftActive="false",e.dataset.selectionDraftStartMs="",e.dataset.selectionDraftEndMs="",t.redraw!==!1&&Ar(e)}function Xl(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=xl(Fo(),t,n,a);return!o.draftActive||o.draftStartMs===null||o.draftEndMs===null?(tn(e,r),!1):(e.dataset.selectionDraftActive="true",e.dataset.selectionDraftStartMs=String(o.draftStartMs),e.dataset.selectionDraftEndMs=String(o.draftEndMs),r.redraw!==!1&&Ar(e),!0)}function Kl(e,t,n={}){const r=ra(e);return r?(tn(e,{redraw:!1}),Yl(e,r.startMs,r.endMs,t,n)):(tn(e),!1)}function Bo(e,t={}){if(e.dataset.selectionActive="false",e.dataset.selectionStartMs="",e.dataset.selectionEndMs="",tn(e,{redraw:!1}),Ar(e),t.resetPlaybackRegion!==!1){const n=Io(e);e.dataset.playbackStartMs=String(Math.round(n.startMs)),e.dataset.playbackEndMs=String(Math.round(n.endMs)),e.dataset.playbackRegionMode=n.mode}}function Yl(e,t,n,r,a={}){const o=Number(e.dataset.durationMs||"0"),s=Cl(Fo(),t,n,o);return!s.active||s.startMs===null||s.endMs===null?(Bo(e),!1):(tn(e,{redraw:!1}),e.dataset.selectionActive="true",e.dataset.selectionStartMs=String(s.startMs),e.dataset.selectionEndMs=String(s.endMs),e.dataset.playbackStartMs=String(s.startMs),e.dataset.playbackEndMs=String(s.endMs),e.dataset.playbackRegionMode="selection",Ar(e),a.updateCursor!==!1&&r.setCursor(e,s.startMs,!1),!0)}function Ar(e){const t=ra(e),n=t??On(e);Wl(e,n,t)}function Ql(){return document.body.dataset.aqeBusy==="true"}function Zl(e){var t;return((t=rt(e))==null?void 0:t.querySelector(".aqe-delete-region-button"))??null}function Vo(e,t){return e.startMs<=0&&e.endMs>=t}function Go(e,t){return!!e&&e.endMs>e.startMs&&!Vo(e,t)}function Ln(e){const t=Number(e.dataset.aqeFieldOrd||"0"),n=Zl(t);if(!n)return;const r=On(e),a=Number(e.dataset.durationMs||"0"),o=r!==null,s=Go(r,a);n.hidden=!o,n.disabled=Ql()||!s,n.dataset.aqeButtonState=s?"default":"unavailable",n.title=s?"Delete selected region":"Cannot delete the whole audio clip",n.setAttribute("aria-disabled",n.disabled?"true":"false")}function Jl(){Zr().forEach(Ln)}function Ho(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=Number(e.dataset.durationMs||"0")||0,a=On(e);if(!a||!Go(a,r))return a&&Vo(a,r)&&he.warn("region delete rejected whole clip",{ord:n,sourceFilename:e.dataset.sourceFilename||"",selectionStartMs:a.startMs,selectionEndMs:a.endMs,durationMs:r,trigger:t}),null;const o=e.dataset.sourceFilename||"";if(!o)return null;const s=e.dataset.playbackState;return{ord:n,sourceFilename:o,selectionStartMs:Math.round(a.startMs),selectionEndMs:Math.round(a.endMs),cursorMs:Math.round(Number(e.dataset.cursorMs||"0")||0),durationMs:Math.round(r),trigger:t,playbackActive:ta(s)&&s!=="stopped"}}function zl(e,t,n,r,a){e.preventDefault();const o=a.playbackStateFor(t),s=t.querySelector(".aqe-visualizer-svg"),i=Number(t.dataset.durationMs||"0");if(!s||!i)return;o==="playing"&&a.stopProgressClock(t);const l=c=>{a.setCursor(t,Wo(c,s,i,t,a),!1)},f=c=>{window.removeEventListener("pointermove",l),window.removeEventListener("pointerup",f);const u=o==="playing";o==="paused"&&(t.dataset.resumeRequiresRestart="true");const d=Wo(c,s,i,t,a),_=u&&a.audioClockReady(t)?"html":"";a.setCursor(t,d,r,{previousPlaybackState:o,restartPlayback:u,engine:_}),a.audioClockReady(t)&&a.seekAudioClock(t,d),u&&_==="html"&&a.startEditorHtmlPlayback(t,a.playbackRequestForStart(t,n,d,"html"))};l(e),window.addEventListener("pointermove",l),window.addEventListener("pointerup",f)}function eu(e,t,n,r){e.preventDefault();const a=t.querySelector(".aqe-visualizer-svg"),o=Number(t.dataset.durationMs||"0");if(!a||!o)return;const s=r.playbackStateFor(t),i=r.currentProgressMs(t)??Number(t.dataset.cursorMs||"0"),l={clientX:e.clientX},f=Dn(e,a,o);let c=!1,u=F=>{},d=F=>{},_=()=>{},m=F=>{};const w=()=>{window.removeEventListener("pointermove",u),window.removeEventListener("pointerup",d),window.removeEventListener("pointercancel",_),window.removeEventListener("keydown",m),window.removeEventListener("blur",_),a.removeEventListener("lostpointercapture",_)},h=()=>{c||s!=="playing"||(c=!0,r.stopProgressClock(t,{clearEngine:!1}),r.setCursor(t,i,!1,{updateAnchor:!1}))},v=()=>{s==="playing"&&c&&r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,i,"html"))};u=F=>{const y=Dn(F,a,o);if(xo(l,F,f,y)){r.clearSelectionDraft(t);return}h(),r.setSelectionDraft(t,f,y)},d=F=>{w();const y=Dn(F,a,o);if(xo(l,F,f,y)){r.clearSelection(t),v();return}h(),r.draftSelectionForVisualizer(t)||r.setSelectionDraft(t,f,y,{redraw:!1});const E=r.commitSelectionDraft(t);if(s==="paused"&&(t.dataset.resumeRequiresRestart="true"),E&&s==="playing"){const A=r.selectionForVisualizer(t);r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,(A==null?void 0:A.startMs)??f,"html"))}},_=()=>{w(),r.clearSelectionDraft(t),v()},m=F=>{F.key==="Escape"&&_()},window.addEventListener("pointermove",u),window.addEventListener("pointerup",d),window.addEventListener("pointercancel",_),window.addEventListener("keydown",m),window.addEventListener("blur",_),a.addEventListener("lostpointercapture",_)}function tu(e,t,n){const r=n.visualizerForOrd(t);if(r){if(e.shiftKey){eu(e,r,t,n);return}zl(e,r,t,!0,n)}}function Wo(e,t,n,r,a){const o=Dn(e,t,n),s=a.selectionForVisualizer(r);return s&&r.dataset.repeatEnabled==="true"?Ml(o,s):o}function Nt(e){e.__aqePlaybackTimer&&(window.cancelAnimationFrame(e.__aqePlaybackTimer),e.__aqePlaybackTimer=null)}function jo(e){const t=Number(e.dataset.durationMs||"0"),n=performance.now()-Number(e.dataset.playStartedAt||"0");return Math.min(t,Number(e.dataset.playStartMs||"0")+n)}function $o(e){const t=Oe(e);if(!t)return null;const n=Number(e.dataset.durationMs||"0");return Math.min(n,(Number(t.currentTime)||0)*1e3)}function Uo(e){return e.dataset.progressClockMode==="audio"?$o(e):e.dataset.progressClockMode==="manual"?jo(e):Number(e.dataset.progressMs||e.dataset.cursorMs||"0")}function aa(e,t,n,r={}){return t<su(e,n)?!1:n.repeatEnabledFor(e)?(iu(e,n,r),!0):(nu(e,n),!0)}function nu(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=t.effectivePlaybackRegion(e),a=e.dataset.playbackRegionMode==="selection"?r.startMs:Number(e.dataset.anchorMs||"0");sa(e,t),t.setCursor(e,a,!1,{updateAnchor:!1}),br(e)&&yr(e,a,Number(e.dataset.durationMs||"0")),t.clearStatus(n),window.__aqeActiveField=n,t.focusAndSendCommand(n,"aqe:play-ended")}function oa(e,t){const n=()=>{if(e.dataset.playbackState!=="playing")return;const r=$o(e);if(r===null){at(e,Number(e.dataset.cursorMs||"0"),t);return}t.setCursor(e,r,!1,{updateAnchor:!1}),!aa(e,r,t)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(n))};e.__aqePlaybackTimer=window.requestAnimationFrame(n)}function at(e,t,n){if(Nt(e),xn(e),!Number(e.dataset.durationMs||"0"))return;const a=Xo(e,t);e.__aqeAudioClockFallback=!0,e.dataset.playbackState="playing",e.dataset.progressClockMode="manual",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),ia(e,a,n),n.setPlaybackButtonLabel(e,"Pause");const o=()=>{if(e.dataset.playbackState!=="playing")return;const s=jo(e);n.setCursor(e,s,!1,{updateAnchor:!1}),!aa(e,s,n)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(o))};e.__aqePlaybackTimer=window.requestAnimationFrame(o)}function ru(e,t,n,r={}){var i;const a=Oe(e);if(!a||!yr(e,t,Number(e.dataset.durationMs||"0"))||typeof a.play!="function"){if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}at(e,t,n);return}e.dataset.progressClockMode="audio",e.__aqeAudioClockFallback=!1;const o=()=>{var l;if(r.manualFallback===!1){(l=r.onAudioPlayFailed)==null||l.call(r);return}at(e,t,n)},s=()=>{var l;e.dataset.playbackState==="playing"&&(Nt(e),e.dataset.progressClockMode="audio",he.info("html audio playback started",{ord:e.dataset.aqeFieldOrd}),oa(e,n),(l=r.onAudioStarted)==null||l.call(r))};Promise.resolve(a.play()).then(s).catch(()=>{e.dataset.playbackState==="playing"&&(he.warn("html audio play rejected; using manual clock",{ord:e.dataset.aqeFieldOrd}),o())})}function au(e,t,n,r={}){var i;const a=r.engine||e.dataset.playbackEngine||"";if(sa(e,n,{clearEngine:!1}),n.stopOtherPlayback(e),!Number(e.dataset.durationMs||"0"))return;const s=Xo(e,t);if(e.dataset.playbackEngine=a,e.dataset.playbackState="playing",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(s),ia(e,s,n),n.setCursor(e,s,!1,{updateAnchor:!1}),n.setPlaybackButtonLabel(e,"Pause"),he.info("playback clock selected",{engine:a||"auto",startMs:s}),a==="native"){at(e,s,n);return}if(br(e)){ru(e,s,n,r);return}if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}at(e,s,n)}function ou(e,t){const n=Uo(e);n!==null&&t.setCursor(e,n,!1,{updateAnchor:!1}),Nt(e),xn(e),e.dataset.playbackState="paused",e.dataset.progressClockMode="stopped",t.setPlaybackButtonLabel(e,"Play")}function sa(e,t,n={}){Nt(e),xn(e),e.dataset.playbackState="stopped",e.dataset.progressClockMode="stopped",e.dataset.resumeRequiresRestart="false",n.clearEngine!==!1&&(e.dataset.playbackEngine=""),n.clearAudio&&zr(e),t.setPlaybackButtonLabel(e,"Play")}function ia(e,t,n,r=n.effectivePlaybackRegion(e)){e.dataset.playbackStartMs=String(Math.round(t)),e.dataset.playbackEndMs=String(Math.round(r.endMs)),e.dataset.playbackRegionMode=r.mode}function su(e,t){const n=t.effectivePlaybackRegion(e),r=Number(e.dataset.playbackEndMs||"0")||n.endMs;return Math.max(n.startMs,Math.min(r,Number(e.dataset.durationMs||"0")||0))}function iu(e,t,n={}){const r=t.effectivePlaybackRegion(e),a=r.startMs;if(ia(e,a,t,r),e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),t.setCursor(e,a,!1,{updateAnchor:!1}),e.dataset.progressClockMode!=="audio"||!br(e)){at(e,a,t);return}if(!yr(e,a,Number(e.dataset.durationMs||"0"))){at(e,a,t);return}if(!n.forceAudioPlay){Nt(e),oa(e,t);return}const o=Oe(e);!o||typeof o.play!="function"||(Nt(e),Promise.resolve(o.play()).then(()=>{e.dataset.playbackState==="playing"&&oa(e,t)}).catch(()=>{e.dataset.playbackState==="playing"&&at(e,a,t)}))}function Xo(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function Ko(){return document.body.dataset.aqeBusy==="true"}function Yo(){var e;return((e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.repeatPlaybackByDefault)===!0}function lu(e){for(const t of Zr())t!==e&&an(t)!=="stopped"&&vt(t)}function uu(){for(const e of Zr())an(e)!=="stopped"&&vt(e)}function nn(e,t,n="",r=""){document.body.dataset.aqeBusy=t?"true":"false",document.querySelectorAll(".aqe-controls").forEach(s=>{s.dataset.busy=t?"true":"false"}),_r().forEach(s=>{s.disabled=!!t}),Jl(),t||queueMicrotask(()=>kr(ma()));const a=rt(e),o=a==null?void 0:a.querySelector(".aqe-status");o&&(o.textContent=n||"",o.dataset.kind=t?"processing":"info",o.title=r||"")}function Qo(e,t="info"){const n=Number(window.__aqeActiveField??0),r=rt(n),a=r==null?void 0:r.querySelector(".aqe-status");a&&(a.textContent=e||"",a.dataset.kind=t||"info")}function cu(e){const t=rt(e),n=t==null?void 0:t.querySelector(".aqe-status");n&&(n.textContent="",n.dataset.kind="info",n.title="")}function rn(e,t,n){var o;const r=t==="aqe:play"?qo(e):t==="aqe:analyze"?wo(e):((o=rt(e))==null?void 0:o.querySelector(`[data-aqe-command="${t}"]`))??null;if(!r)return;const a=r.querySelector(".aqe-button-label");a?a.textContent=n:r.textContent=n,t==="aqe:play"&&(r.dataset.aqeButtonState=n==="Pause"?"pause":"play"),t==="aqe:analyze"&&(r.dataset.aqeButtonState=n==="Redraw"?"redraw":"graph")}function la(e,t,n,r){if(!Ko()){if(typeof t.focus=="function"&&t.focus(),window.__aqeActiveField=n,he.info("command dispatched",{command:e,ord:n}),e==="aqe:analyze"){es(n,!0);return}if(!(e==="aqe:play"&&xu(n))){if(re.has(e)&&(uu(),nn(n,!0,bo(e))),r){el(n,r);return}en(n,e)}}}function fu(e){Jr(e)}function du(e){Nt(e)}function pu(e){zr(e)}function hu(e,t){fl(e,t)}function mu(e){dl(e,{onErrorDuringPlayback(){he.warn("audio clock failed during playback",{ord:e.dataset.aqeFieldOrd}),Cu(e,Number(e.dataset.cursorMs||"0"))},onEndedDuringPlayback(){Nu(e,Number(e.dataset.durationMs||"0"),{forceAudioPlay:!0})}})}function ua(e){return br(e)}function _u(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function Zo(e){return On(e)}function Jo(e){return ra(e)}function ca(e){return Io(e)}function fa(e,t){e.dataset.repeatEnabled=t?"true":"false";const n=Number(e.dataset.aqeFieldOrd||"0"),r=So(n);r&&(r.ariaPressed=t?"true":"false",r.dataset.aqeButtonState=t?"active":"default")}function vu(e,t){const n=B(e);return n?(fa(n,t),!0):!1}function gu(e,t={}){tn(e,t)}function bu(e,t,n,r={}){return Xl(e,t,n,r)}function yu(e,t={}){const n=Kl(e,Su(),t);return Ln(e),n}function In(e,t={}){Bo(e,t),Ln(e)}function wu(e){e.dataset.playbackStartMs="0",e.dataset.playbackEndMs=String(Number(e.dataset.durationMs||"0")||0),e.dataset.playbackRegionMode="full",fa(e,Yo()),In(e,{resetPlaybackRegion:!1})}function qu(){return{audioClockReady:ua,clearSelection:In,clearSelectionDraft:gu,commitSelectionDraft:yu,currentProgressMs:as,draftSelectionForVisualizer:Jo,playbackRequestForStart:Mu,playbackStateFor:an,seekAudioClock:zo,selectionForVisualizer:Zo,setCursor:Ct,setSelectionDraft:bu,startEditorHtmlPlayback:ls,stopProgressClock:vt,visualizerForOrd:B}}function Su(){return{setCursor:Ct}}function da(e){return e.dataset.repeatEnabled==="true"}function Bn(){return{clearStatus:cu,effectivePlaybackRegion:ca,focusAndSendCommand:en,playbackEngineFor:Vn,repeatEnabledFor:da,setCursor:Ct,setPlaybackButtonLabel:Fu,stopOtherPlayback:lu}}function Mu(e,t,n,r=Vn(e)){const a=ca(e);return{ord:t,action:"start",cursorMs:Math.round(_u(e,n)),endMs:Math.round(a.endMs),engine:r,loop:da(e),regionMode:a.mode}}function zo(e,t){return yr(e,t,Number(e.dataset.durationMs||"0"))}function Ct(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Math.max(0,Math.min(Number(t)||0,a||0));if(e.dataset.cursorMs=String(Math.round(o)),e.dataset.progressMs=String(Math.round(o)),r.updateAnchor!==!1&&(e.dataset.anchorMs=String(Math.round(o))),jl(e,o,a),n){window.__aqeActiveField=Number(e.dataset.aqeFieldOrd||"0");const s={cursorMs:Math.round(o),previousPlaybackState:r.previousPlaybackState||an(e),restartPlayback:!!r.restartPlayback};r.engine&&(s.engine=r.engine),ul(s),he.info("cursor committed",s),en(window.__aqeActiveField,"aqe:set-cursor")}}function ku(e,t){var n;(n=B(t))==null||n.focus(),tu(e,t,qu())}function es(e,t){ns(e)&&(window.__aqeActiveField=e,he.info("graph requested",{notifyPython:t,ord:e}),nn(e,!0,"Analyzing...",""),en(e,"aqe:analyze"))}function ts(e){ns(e.ord)&&(he.info("default graph requested",e),nn(e.ord,!0,"Analyzing...",""),tl(e))}function ns(e){const t=B(e);return t?(vt(t,{clearAudio:!0}),Vl(t),In(t),Ct(t,0,!1),rn(e,"aqe:analyze","Redraw"),ha(e,"Analyzing...","processing"),!0):!1}function Eu(e){return window.__aqePendingGraphRedrawField=e,pa()}function pa(){const e=window.__aqePendingGraphRedrawField;if(typeof e!="number")return!1;const t=B(e);return t?(t.dataset.graphBusy==="true"||t.dataset.hasTrack==="true"||es(e,!0),!0):!1}function ha(e,t,n="info"){const r=B(e);r&&Hl(r,t,n)}function Au(e,t,n){const r=B(e);if(!r||!t)return;const a=El(t);Gl(r,a),r.dataset.anchorMs=String(n||0),window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null),In(r),r.dataset.playbackStartMs="0",r.dataset.playbackEndMs=String(a.durationMs||0),r.dataset.playbackRegionMode="full",hu(r,a.sourceFilename||""),rn(e,"aqe:analyze","Redraw"),Ct(r,n||0,!1),ua(r)&&zo(r,n||0),ha(e,a.analyzerName||"","info"),nn(e,!1,"",""),ko(e,ma()),he.info("graph rendered",Ul(e,a))}function Pu(e,t,n="info"){n!=="processing"&&window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null);const r=B(e);r&&(r.hidden=!1,r.dataset.graphActive="true",n==="processing"&&(r.dataset.hasTrack="false"),rn(e,"aqe:analyze","Redraw")),ha(e,t,n),n!=="processing"&&ko(e,ma())}function ma(){return{anyBusy:Ko,requestDefaultGraph:ts}}function rs(){document.body.dataset.aqeBusy="false",window.__aqeActiveField=null,window.__aqeLastCursorIntent=null,document.querySelectorAll(".aqe-controls").forEach(e=>{e.dataset.busy="false",e.dataset.aqeSourceFilename="",e.querySelectorAll(".aqe-button").forEach(o=>{o.disabled=!1,o.dataset.aqeCommand==="aqe:analyze"&&rn(Number(e.dataset.aqeFieldOrd||"0"),"aqe:analyze","Graph"),o.dataset.aqeCommand==="aqe:play"&&rn(Number(e.dataset.aqeFieldOrd||"0"),"aqe:play","Play")});const t=e.querySelector(".aqe-status");t&&(t.textContent="",t.dataset.kind="info",t.title="");const n=e.querySelector(".aqe-visualizer");if(!n)return;du(n),pu(n),n.hidden=!0,n.dataset.anchorMs="0",n.dataset.cursorMs="0",n.dataset.progressMs="0",n.dataset.graphActive="false",n.dataset.graphBusy="false",n.dataset.hasTrack="false",n.dataset.playbackState="stopped",n.dataset.playbackEngine="",n.dataset.resumeRequiresRestart="false",n.dataset.durationMs="0",n.dataset.sourceFilename="",n.dataset.analyzerName="",n.dataset.playStartedAt="0",n.dataset.playStartMs="0",n.dataset.playbackStartMs="0",n.dataset.playbackEndMs="0",n.dataset.playbackRegionMode="full",n.dataset.progressClockMode="stopped",fa(n,Yo()),In(n),Lo(n),$l(n);const r=n.querySelector(".aqe-visualizer-status");r&&(r.textContent="",r.dataset.kind="info");const a=n.querySelector(".aqe-spinner");a&&(a.hidden=!0)})}function Fu(e,t){const n=Number(e.dataset.aqeFieldOrd||"0");rn(n,"aqe:play",t)}function as(e){return Uo(e)}function Nu(e,t,n={}){return aa(e,t,Bn(),n)}function Cu(e,t){at(e,t,Bn())}function os(e,t,n={}){au(e,t,Bn(),n)}function ss(e){ou(e,Bn())}function vt(e,t={}){sa(e,Bn(),t)}function is(e){const t=B(e);return t?kl({anchorMs:Number(t.dataset.anchorMs||t.dataset.cursorMs||"0"),currentProgressMs:as(t),cursorMs:Number(t.dataset.cursorMs||"0"),engine:Vn(t),ord:e,playbackState:an(t),region:ca(t),repeat:da(t),resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true"}):{ord:e,action:"start",cursorMs:0}}function Vn(e){if(!e||e.dataset.hasTrack!=="true")return"native";const t=e.dataset.playbackEngine||"";return e.dataset.playbackState!=="stopped"&&(t==="html"||t==="native")?t:ua(e)?"html":"native"}function _a(e){const t=B(e.ord);t&&(t.dataset.playbackEngine=e.engine||""),al(e),window.__aqeActiveField=e.ord,he.info("playback request queued",e),en(e.ord,"aqe:play")}function ls(e,t){return os(e,t.cursorMs,{engine:"html",manualFallback:!1,onAudioStarted(){_a(t)},onAudioPlayFailed(){if(he.warn("html playback failed; falling back to native",{ord:t.ord}),vt(e),t.regionMode==="selection"||t.loop){window.__aqeActiveField=t.ord,Qo("Selected repeat playback needs browser audio.","warning");return}_a({...t,engine:"native"})}}),!0}function xu(e){const t=B(e);if(!t||Vn(t)!=="html")return!1;const n={...is(e),engine:"html"};return n.action==="pause"?(ss(t),n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0"),_a(n),!0):(n.action==="resume"&&(n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0")),ls(t,n))}function Tu(e,t,n){const r=B(e);r&&((t==="playing"||t==="paused")&&(r.dataset.resumeRequiresRestart="false"),t==="playing"?os(r,n,{engine:r.dataset.playbackEngine==="html"||r.dataset.playbackEngine==="native"?r.dataset.playbackEngine:""}):t==="paused"?ss(r):vt(r))}function Ru(){const e=ol();if(e)return e;const t=Number(window.__aqeActiveField||"0"),n=is(t),r=B(t);return r&&(r.dataset.playbackEngine=n.engine||""),n}function Du(e){const t=B(e);return t?(vt(t),!0):!1}function Ou(){const e=Number(window.__aqeActiveField||"0"),t=B(e);return t?Number(t.dataset.cursorMs||"0"):0}function Lu(){const e=Number(window.__aqeActiveField||"0"),t=B(e),n=t?Number(t.dataset.cursorMs||"0"):0;return window.__aqeLastCursorIntent||{cursorMs:n,previousPlaybackState:t?an(t):"stopped",restartPlayback:!1}}function an(e){const t=e.dataset.playbackState;return ta(t)?t:"stopped"}const us=(Li=(Oi=globalThis.process)==null?void 0:Oi.env)==null?void 0:Li.NODE_ENV,b=us&&!us.toLowerCase().startsWith("prod");var va=Array.isArray,Iu=Array.prototype.indexOf,xt=Array.prototype.includes,Pr=Array.from,Tt=Object.defineProperty,ot=Object.getOwnPropertyDescriptor,Bu=Object.getOwnPropertyDescriptors,Vu=Object.prototype,Gu=Array.prototype,cs=Object.getPrototypeOf,fs=Object.isExtensible;function Gn(e){return typeof e=="function"}const U=()=>{};function Hu(e){for(var t=0;t<e.length;t++)e[t]()}function ds(){var e,t,n=new Promise((r,a)=>{e=r,t=a});return{promise:n,resolve:e,reject:t}}function Wu(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const r of e)if(n.push(r),n.length===t)break;return n}const le=2,Hn=4,Fr=8,ga=1<<24,st=16,Le=32,Rt=64,ba=128,Pe=512,oe=1024,ue=2048,Ie=4096,qe=8192,it=16384,Dt=32768,gt=65536,Nr=1<<17,ps=1<<18,on=1<<19,ju=1<<20,lt=1<<25,bt=65536,ya=1<<21,Cr=1<<22,yt=1<<23,ut=Symbol("$state"),hs=Symbol("legacy props"),$u=Symbol(""),ms=Symbol("proxy path"),Ot=new class extends Error{constructor(){super(...arguments);nt(this,"name","StaleReactionError");nt(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}},wa=!!((Ii=globalThis.document)!=null&&Ii.contentType)&&globalThis.document.contentType.includes("xml");function _s(e){if(b){const t=new Error(`lifecycle_outside_component
\`${e}(...)\` can only be used during component initialisation
https://svelte.dev/e/lifecycle_outside_component`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/lifecycle_outside_component")}function Uu(){if(b){const e=new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/async_derived_orphan")}function Xu(){if(b){const e=new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/derived_references_self")}function vs(e,t,n){if(b){const r=new Error(`each_key_duplicate
${n?`Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}`:`Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_duplicate")}function Ku(e,t,n){if(b){const r=new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_volatile")}function Yu(e){if(b){const t=new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_in_teardown")}function Qu(){if(b){const e=new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Zu(e){if(b){const t=new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_orphan")}function Ju(){if(b){const e=new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function zu(){if(b){const e=new Error("invalid_snippet\nCould not `{@render}` snippet due to the expression being `null` or `undefined`. Consider using optional chaining `{@render snippet?.()}`\nhttps://svelte.dev/e/invalid_snippet");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/invalid_snippet")}function ec(e){if(b){const t=new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_invalid_value")}function tc(e){if(b){const t=new Error(`props_rest_readonly
Rest element properties of \`$props()\` such as \`${e}\` are readonly
https://svelte.dev/e/props_rest_readonly`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_rest_readonly")}function nc(e){if(b){const t=new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/rune_outside_svelte")}function rc(){if(b){const e=new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function ac(){if(b){const e=new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_prototype_fixed")}function oc(){if(b){const e=new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function sc(){if(b){const e=new Error("svelte_boundary_reset_onerror\nA `<svelte:boundary>` `reset` function cannot be called while an error is still being handled\nhttps://svelte.dev/e/svelte_boundary_reset_onerror");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const ic=1,lc=2,gs=4,uc=8,cc=16,fc=1,dc=4,pc=8,hc=16,mc=1,_c=2,se=Symbol(),vc=Symbol("filename"),bs="http://www.w3.org/1999/xhtml",gc="http://www.w3.org/2000/svg",bc="@attach";var Wn="font-weight: bold",jn="font-weight: normal";function yc(){b?console.warn(`%c[svelte] lifecycle_double_unmount
%cTried to unmount a component that was not mounted
https://svelte.dev/e/lifecycle_double_unmount`,Wn,jn):console.warn("https://svelte.dev/e/lifecycle_double_unmount")}function wc(){b?console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value",Wn,jn):console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function qa(e){b?console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`,Wn,jn):console.warn("https://svelte.dev/e/state_proxy_equality_mismatch")}function qc(){b?console.warn(`%c[svelte] state_proxy_unmount
%cTried to unmount a state proxy, rather than a component
https://svelte.dev/e/state_proxy_unmount`,Wn,jn):console.warn("https://svelte.dev/e/state_proxy_unmount")}function Sc(){b?console.warn("%c[svelte] svelte_boundary_reset_noop\n%cA `<svelte:boundary>` `reset` function only resets the boundary the first time it is called\nhttps://svelte.dev/e/svelte_boundary_reset_noop",Wn,jn):console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function ys(e){return e===this.v}function Mc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function ws(e){return!Mc(e,this.v)}let kc=!1;function $e(e,t){return e.label=t,qs(e.v,t),e}function qs(e,t){var n;return(n=e==null?void 0:e[ms])==null||n.call(e,t),e}function Ec(e){const t=new Error,n=Ac();return n.length===0?null:(n.unshift(`
`),Tt(t,"stack",{value:n.join(`
`)}),Tt(t,"name",{value:e}),t)}function Ac(){const e=Error.stackTraceLimit;Error.stackTraceLimit=1/0;const t=new Error().stack;if(Error.stackTraceLimit=e,!t)return[];const n=t.split(`
`),r=[];for(let a=0;a<n.length;a++){const o=n[a],s=o.replaceAll("\\","/");if(o.trim()!=="Error"){if(o.includes("validate_each_keys"))return[];s.includes("svelte/src/internal")||s.includes("node_modules/.vite")||r.push(o)}}return r}let K=null;function sn(e){K=e}let ln=null;function xr(e){ln=e}let $n=null;function Ss(e){$n=e}function Pc(e){return Fc("getContext").get(e)}function V(e,t=!1,n){K={p:K,i:!1,c:null,e:null,s:e,x:null,l:null},b&&(K.function=n,$n=n)}function G(e){var t=K,n=t.e;if(n!==null){t.e=null;for(var r of n)Us(r)}return t.i=!0,K=t.p,b&&($n=(K==null?void 0:K.function)??null),{}}function Ms(){return!0}function Fc(e){return K===null&&_s(e),K.c??(K.c=new Map(Nc(K)||void 0))}function Nc(e){let t=e.p;for(;t!==null;){const n=t.c;if(n!==null)return n;t=t.p}return null}let un=[];function Cc(){var e=un;un=[],Hu(e)}function Ue(e){if(un.length===0){var t=un;queueMicrotask(()=>{t===un&&Cc()})}un.push(e)}const Sa=new WeakMap;function ks(e){var t=R;if(t===null)return x.f|=yt,e;if(b&&e instanceof Error&&!Sa.has(e)&&Sa.set(e,xc(e,t)),(t.f&Dt)===0&&(t.f&Hn)===0)throw b&&!t.parent&&e instanceof Error&&Es(e),e;wt(e,t)}function wt(e,t){for(;t!==null;){if((t.f&ba)!==0){if((t.f&Dt)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw b&&e instanceof Error&&Es(e),e}function xc(e,t){var s,i,l;const n=ot(e,"message");if(!(n&&!n.configurable)){for(var r=Ca?"  ":"	",a=`
${r}in ${((s=t.fn)==null?void 0:s.name)||"<unknown>"}`,o=t.ctx;o!==null;)a+=`
${r}in ${(i=o.function)==null?void 0:i[vc].split("/").pop()}`,o=o.p;return{message:e.message+`
${a}
`,stack:(l=e.stack)==null?void 0:l.split(`
`).filter(f=>!f.includes("svelte/src/internal")).join(`
`)}}}function Es(e){const t=Sa.get(e);t&&(Tt(e,"message",{value:t.message}),Tt(e,"stack",{value:t.stack}))}const Tc=-7169;function z(e,t){e.f=e.f&Tc|t}function Ma(e){(e.f&Pe)!==0||e.deps===null?z(e,oe):z(e,Ie)}function As(e){if(e!==null)for(const t of e)(t.f&le)===0||(t.f&bt)===0||(t.f^=bt,As(t.deps))}function Ps(e,t,n){(e.f&ue)!==0?t.add(e):(e.f&Ie)!==0&&n.add(e),As(e.deps),z(e,oe)}const Tr=new Set;let L=null,ce=null,Fe=[],ka=null,Ea=!1;const ro=class ro{constructor(){T(this,Me);nt(this,"current",new Map);nt(this,"previous",new Map);T(this,bn,new Set);T(this,yn,new Set);T(this,Wt,0);T(this,wn,0);T(this,ar,null);T(this,or,new Set);T(this,jt,new Set);T(this,dt,new Map);nt(this,"is_fork",!1);T(this,qn,!1)}skip_effect(t){p(this,dt).has(t)||p(this,dt).set(t,{d:[],m:[]})}unskip_effect(t){var n=p(this,dt).get(t);if(n){p(this,dt).delete(t);for(var r of n.d)z(r,ue),Ve(r);for(r of n.m)z(r,Ie),Ve(r)}}process(t){var a;Fe=[],this.apply();var n=[],r=[];for(const o of t)ie(this,Me,mo).call(this,o,n,r);if(ie(this,Me,ho).call(this)){ie(this,Me,_o).call(this,r),ie(this,Me,_o).call(this,n);for(const[o,s]of p(this,dt))xs(o,s)}else{for(const o of p(this,bn))o();p(this,bn).clear(),p(this,Wt)===0&&ie(this,Me,zi).call(this),L=null,Fs(r),Fs(n),(a=p(this,ar))==null||a.resolve()}ce=null}capture(t,n){n!==se&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&yt)===0&&(this.current.set(t,t.v),ce==null||ce.set(t,t.v))}activate(){L=this,this.apply()}deactivate(){L===this&&(L=null,ce=null)}flush(){if(this.activate(),Fe.length>0){if(Rc(),L!==null&&L!==this)return}else p(this,Wt)===0&&this.process([]);this.deactivate()}discard(){for(const t of p(this,yn))t(this);p(this,yn).clear()}increment(t){C(this,Wt,p(this,Wt)+1),t&&C(this,wn,p(this,wn)+1)}decrement(t){C(this,Wt,p(this,Wt)-1),t&&C(this,wn,p(this,wn)-1),!p(this,qn)&&(C(this,qn,!0),Ue(()=>{C(this,qn,!1),ie(this,Me,ho).call(this)?Fe.length>0&&this.flush():this.revive()}))}revive(){for(const t of p(this,or))p(this,jt).delete(t),z(t,ue),Ve(t);for(const t of p(this,jt))z(t,Ie),Ve(t);this.flush()}oncommit(t){p(this,bn).add(t)}ondiscard(t){p(this,yn).add(t)}settled(){return(p(this,ar)??C(this,ar,ds())).promise}static ensure(){if(L===null){const t=L=new ro;Tr.add(L),Ue(()=>{L===t&&t.flush()})}return L}apply(){}};bn=new WeakMap,yn=new WeakMap,Wt=new WeakMap,wn=new WeakMap,ar=new WeakMap,or=new WeakMap,jt=new WeakMap,dt=new WeakMap,qn=new WeakMap,Me=new WeakSet,ho=function(){return this.is_fork||p(this,wn)>0},mo=function(t,n,r){t.f^=oe;for(var a=t.first;a!==null;){var o=a.f,s=(o&(Le|Rt))!==0,i=s&&(o&oe)!==0,l=i||(o&qe)!==0||p(this,dt).has(a);if(!l&&a.fn!==null){s?a.f^=oe:(o&Hn)!==0?n.push(a):Qn(a)&&((o&st)!==0&&p(this,jt).add(a),hn(a));var f=a.first;if(f!==null){a=f;continue}}for(;a!==null;){var c=a.next;if(c!==null){a=c;break}a=a.parent}}},_o=function(t){for(var n=0;n<t.length;n+=1)Ps(t[n],p(this,or),p(this,jt))},zi=function(){var a;if(Tr.size>1){this.previous.clear();var t=ce,n=!0;for(const o of Tr){if(o===this){n=!1;continue}const s=[];for(const[l,f]of this.current){if(o.current.has(l))if(n&&f!==o.current.get(l))o.current.set(l,f);else continue;s.push(l)}if(s.length===0)continue;const i=[...o.current.keys()].filter(l=>!this.current.has(l));if(i.length>0){var r=Fe;Fe=[];const l=new Set,f=new Map;for(const c of s)Ns(c,i,l,f);if(Fe.length>0){L=o,o.apply();for(const c of Fe)ie(a=o,Me,mo).call(a,c,[],[]);o.deactivate()}Fe=r}}L=null,ce=t}Tr.delete(this)};let qt=ro;function Rc(){Ea=!0;var e=b?new Set:null;try{for(var t=0;Fe.length>0;){var n=qt.ensure();if(t++>1e3){if(b){var r=new Map;for(const o of n.current.keys())for(const[s,i]of o.updated??[]){var a=r.get(s);a||(a={error:i.error,count:0},r.set(s,a)),a.count+=i.count}for(const o of r.values())o.error&&console.error(o.error)}Dc()}if(n.process(Fe),St.clear(),b)for(const o of n.current.keys())e.add(o)}}finally{if(Fe=[],Ea=!1,ka=null,b)for(const o of e)o.updated=null}}function Dc(){try{Ju()}catch(e){b&&Tt(e,"stack",{value:""}),wt(e,ka)}}let Be=null;function Fs(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var r=e[n++];if((r.f&(it|qe))===0&&Qn(r)&&(Be=new Set,hn(r),r.deps===null&&r.first===null&&r.nodes===null&&r.teardown===null&&r.ac===null&&Qs(r),(Be==null?void 0:Be.size)>0)){St.clear();for(const a of Be){if((a.f&(it|qe))!==0)continue;const o=[a];let s=a.parent;for(;s!==null;)Be.has(s)&&(Be.delete(s),o.push(s)),s=s.parent;for(let i=o.length-1;i>=0;i--){const l=o[i];(l.f&(it|qe))===0&&hn(l)}}Be.clear()}}Be=null}}function Ns(e,t,n,r){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const a of e.reactions){const o=a.f;(o&le)!==0?Ns(a,t,n,r):(o&(Cr|st))!==0&&(o&ue)===0&&Cs(a,t,r)&&(z(a,ue),Ve(a))}}function Cs(e,t,n){const r=n.get(e);if(r!==void 0)return r;if(e.deps!==null)for(const a of e.deps){if(xt.call(t,a))return!0;if((a.f&le)!==0&&Cs(a,t,n))return n.set(a,!0),!0}return n.set(e,!1),!1}function Ve(e){var t=ka=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(Hn|Fr|ga))!==0&&(e.f&Dt)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var r=t.f;if(Ea&&t===R&&(r&st)!==0&&(r&ps)===0&&(r&Dt)!==0)return;if((r&(Rt|Le))!==0){if((r&oe)===0)return;t.f^=oe}}Fe.push(t)}function xs(e,t){if(!((e.f&Le)!==0&&(e.f&oe)!==0)){(e.f&ue)!==0?t.d.push(e):(e.f&Ie)!==0&&t.m.push(e),z(e,oe);for(var n=e.first;n!==null;)xs(n,t),n=n.next}}function Oc(e){let t=0,n=Lt(0),r;return b&&$e(n,"createSubscriber version"),()=>{Ta()&&(M(n),Xs(()=>(t===0&&(r=Lr(()=>e(()=>Un(n)))),t+=1,()=>{Ue(()=>{t-=1,t===0&&(r==null||r(),r=void 0,Un(n))})})))}}var Lc=gt|on;function Ic(e,t,n,r){new Bc(e,t,n,r)}class Bc{constructor(t,n,r,a){T(this,ae);nt(this,"parent");nt(this,"is_pending",!1);nt(this,"transform_error");T(this,Re);T(this,ao,null);T(this,Ye);T(this,$t);T(this,be);T(this,Qe,null);T(this,ke,null);T(this,We,null);T(this,pt,null);T(this,Ut,0);T(this,At,0);T(this,Sn,!1);T(this,Mn,new Set);T(this,kn,new Set);T(this,Ze,null);T(this,Hr,Oc(()=>(C(this,Ze,Lt(p(this,Ut))),b&&$e(p(this,Ze),"$effect.pending()"),()=>{C(this,Ze,null)})));var o;C(this,Re,t),C(this,Ye,n),C(this,$t,s=>{var i=R;i.b=this,i.f|=ba,r(s)}),this.parent=R.b,this.transform_error=a??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),C(this,be,Yn(()=>{ie(this,ae,vo).call(this)},Lc))}defer_effect(t){Ps(t,p(this,Mn),p(this,kn))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!p(this,Ye).pending}update_pending_count(t){ie(this,ae,go).call(this,t),C(this,Ut,p(this,Ut)+t),!(!p(this,Ze)||p(this,Sn))&&(C(this,Sn,!0),Ue(()=>{C(this,Sn,!1),p(this,Ze)&&fn(p(this,Ze),p(this,Ut))}))}get_effect_pending(){return p(this,Hr).call(this),M(p(this,Ze))}error(t){var n=p(this,Ye).onerror;let r=p(this,Ye).failed;if(!n&&!r)throw t;p(this,Qe)&&(fe(p(this,Qe)),C(this,Qe,null)),p(this,ke)&&(fe(p(this,ke)),C(this,ke,null)),p(this,We)&&(fe(p(this,We)),C(this,We,null));var a=!1,o=!1;const s=()=>{if(a){Sc();return}a=!0,o&&sc(),p(this,We)!==null&&Bt(p(this,We),()=>{C(this,We,null)}),ie(this,ae,Yr).call(this,()=>{qt.ensure(),ie(this,ae,vo).call(this)})},i=l=>{try{o=!0,n==null||n(l,s),o=!1}catch(f){wt(f,p(this,be)&&p(this,be).parent)}r&&C(this,We,ie(this,ae,Yr).call(this,()=>{qt.ensure();try{return ve(()=>{var f=R;f.b=this,f.f|=ba,r(p(this,Re),()=>l,()=>s)})}catch(f){return wt(f,p(this,be).parent),null}}))};Ue(()=>{var l;try{l=this.transform_error(t)}catch(f){wt(f,p(this,be)&&p(this,be).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,f=>wt(f,p(this,be)&&p(this,be).parent)):i(l)})}}Re=new WeakMap,ao=new WeakMap,Ye=new WeakMap,$t=new WeakMap,be=new WeakMap,Qe=new WeakMap,ke=new WeakMap,We=new WeakMap,pt=new WeakMap,Ut=new WeakMap,At=new WeakMap,Sn=new WeakMap,Mn=new WeakMap,kn=new WeakMap,Ze=new WeakMap,Hr=new WeakMap,ae=new WeakSet,Ap=function(){try{C(this,Qe,ve(()=>p(this,$t).call(this,p(this,Re))))}catch(t){this.error(t)}},Pp=function(t){const n=p(this,Ye).failed;n&&C(this,We,ve(()=>{n(p(this,Re),()=>t,()=>()=>{})}))},Fp=function(){const t=p(this,Ye).pending;t&&(this.is_pending=!0,C(this,ke,ve(()=>t(p(this,Re)))),Ue(()=>{var n=C(this,pt,document.createDocumentFragment()),r=ct();n.append(r),C(this,Qe,ie(this,ae,Yr).call(this,()=>(qt.ensure(),ve(()=>p(this,$t).call(this,r))))),p(this,At)===0&&(p(this,Re).before(n),C(this,pt,null),Bt(p(this,ke),()=>{C(this,ke,null)}),ie(this,ae,Kr).call(this))}))},vo=function(){try{if(this.is_pending=this.has_pending_snippet(),C(this,At,0),C(this,Ut,0),C(this,Qe,ve(()=>{p(this,$t).call(this,p(this,Re))})),p(this,At)>0){var t=C(this,pt,document.createDocumentFragment());zs(p(this,Qe),t);const n=p(this,Ye).pending;C(this,ke,ve(()=>n(p(this,Re))))}else ie(this,ae,Kr).call(this)}catch(n){this.error(n)}},Kr=function(){this.is_pending=!1;for(const t of p(this,Mn))z(t,ue),Ve(t);for(const t of p(this,kn))z(t,Ie),Ve(t);p(this,Mn).clear(),p(this,kn).clear()},Yr=function(t){var n=R,r=x,a=K;He(p(this,be)),Ce(p(this,be)),sn(p(this,be).ctx);try{return t()}catch(o){return ks(o),null}finally{He(n),Ce(r),sn(a)}},go=function(t){var n;if(!this.has_pending_snippet()){this.parent&&ie(n=this.parent,ae,go).call(n,t);return}C(this,At,p(this,At)+t),p(this,At)===0&&(ie(this,ae,Kr).call(this),p(this,ke)&&Bt(p(this,ke),()=>{C(this,ke,null)}),p(this,pt)&&(p(this,Re).before(p(this,pt)),C(this,pt,null)))};function Ts(e,t,n,r){const a=Rr;var o=e.filter(u=>!u.settled);if(n.length===0&&o.length===0){r(t.map(a));return}var s=R,i=Vc(),l=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(u=>u.promise)):null;function f(u){i();try{r(u)}catch(d){(s.f&it)===0&&wt(d,s)}Aa()}if(n.length===0){l.then(()=>f(t.map(a)));return}function c(){i(),Promise.all(n.map(u=>Wc(u))).then(u=>f([...t.map(a),...u])).catch(u=>wt(u,s))}l?l.then(c):c()}function Vc(){var e=R,t=x,n=K,r=L;if(b)var a=ln;return function(s=!0){He(e),Ce(t),sn(n),s&&(r==null||r.activate()),b&&xr(a)}}function Aa(e=!0){He(null),Ce(null),sn(null),e&&(L==null||L.deactivate()),b&&xr(null)}function Gc(){var e=R.b,t=L,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}const Hc=new Set;function Rr(e){var t=le|ue,n=x!==null&&(x.f&le)!==0?x:null;return R!==null&&(R.f|=on),{ctx:K,deps:null,effects:null,equals:ys,f:t,fn:e,reactions:null,rv:0,v:se,wv:0,parent:n??R,ac:null}}function Wc(e,t,n){R===null&&Uu();var a=void 0,o=Lt(se);b&&(o.label=t);var s=!x,i=new Map;return sf(()=>{var d;var l=ds();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(Aa)}catch(_){l.reject(_),Aa()}var f=L;if(s){var c=Gc();(d=i.get(f))==null||d.reject(Ot),i.delete(f),i.set(f,l)}const u=(_,m=void 0)=>{if(f.activate(),m)m!==Ot&&(o.f|=yt,fn(o,m));else{(o.f&yt)!==0&&(o.f^=yt),fn(o,_);for(const[w,h]of i){if(i.delete(w),w===f)break;h.reject(Ot)}}c&&c()};l.promise.then(u,_=>u(null,_||"unknown"))}),Ra(()=>{for(const l of i.values())l.reject(Ot)}),b&&(o.f|=Cr),new Promise(l=>{function f(c){function u(){c===a?l(o):f(a)}c.then(u,u)}f(a)})}function Dr(e){const t=Rr(e);return ti(t),t}function Rs(e){const t=Rr(e);return t.equals=ws,t}function Ds(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)fe(t[n])}}let Pa=[];function jc(e){for(var t=e.parent;t!==null;){if((t.f&le)===0)return(t.f&it)===0?t:null;t=t.parent}return null}function Fa(e){var t,n=R;if(He(jc(e)),b){let r=cn;Is(new Set);try{xt.call(Pa,e)&&Xu(),Pa.push(e),e.f&=~bt,Ds(e),t=Ia(e)}finally{He(n),Is(r),Pa.pop()}}else try{e.f&=~bt,Ds(e),t=Ia(e)}finally{He(n)}return t}function Os(e){var t=Fa(e);if(!e.equals(t)&&(e.wv=ai(),(!(L!=null&&L.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){z(e,oe);return}Mt||(ce!==null?(Ta()||L!=null&&L.is_fork)&&ce.set(e,t):Ma(e))}function $c(e){var t,n;if(e.effects!==null)for(const r of e.effects)(r.teardown||r.ac)&&((t=r.teardown)==null||t.call(r),(n=r.ac)==null||n.abort(Ot),r.teardown=U,r.ac=null,Zn(r,0),Oa(r))}function Ls(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&hn(t)}let cn=new Set;const St=new Map;function Is(e){cn=e}let Na=!1;function Uc(){Na=!0}function Lt(e,t){var n={f:0,v:e,reactions:null,equals:ys,rv:0,wv:0};return n}function Ne(e,t){const n=Lt(e);return ti(n),n}function Xc(e,t=!1,n=!0){const r=Lt(e);return t||(r.equals=ws),r}function me(e,t,n=!1){x!==null&&(!Ge||(x.f&Nr)!==0)&&Ms()&&(x.f&(le|st|Cr|Nr))!==0&&(xe===null||!xt.call(xe,e))&&oc();let r=n?dn(t):t;return b&&qs(r,e.label),fn(e,r)}function fn(e,t){var a;if(!e.equals(t)){var n=e.v;Mt?St.set(e,t):St.set(e,n),e.v=t;var r=qt.ensure();if(r.capture(e,n),b){if(R!==null){e.updated??(e.updated=new Map);const o=(((a=e.updated.get(""))==null?void 0:a.count)??0)+1;if(e.updated.set("",{error:null,count:o}),o>5){const s=Ec("updated at");if(s!==null){let i=e.updated.get(s.stack);i||(i={error:s,count:0},e.updated.set(s.stack,i)),i.count++}}}R!==null&&(e.set_during_effect=!0)}if((e.f&le)!==0){const o=e;(e.f&ue)!==0&&Fa(o),Ma(o)}e.wv=ai(),Vs(e,ue),R!==null&&(R.f&oe)!==0&&(R.f&(Le|Rt))===0&&(Te===null?cf([e]):Te.push(e)),!r.is_fork&&cn.size>0&&!Na&&Bs()}return t}function Bs(){Na=!1;for(const e of cn)(e.f&oe)!==0&&z(e,Ie),Qn(e)&&hn(e);cn.clear()}function Un(e){me(e,e.v+1)}function Vs(e,t){var n=e.reactions;if(n!==null)for(var r=n.length,a=0;a<r;a++){var o=n[a],s=o.f;if(b&&(s&Nr)!==0){cn.add(o);continue}var i=(s&ue)===0;if(i&&z(o,t),(s&le)!==0){var l=o;ce==null||ce.delete(l),(s&bt)===0&&(s&Pe&&(o.f|=bt),Vs(l,Ie))}else i&&((s&st)!==0&&Be!==null&&Be.add(o),Ve(o))}}const Kc=/^[a-zA-Z_$][a-zA-Z_$0-9]*$/;function dn(e){if(typeof e!="object"||e===null||ut in e)return e;const t=cs(e);if(t!==Vu&&t!==Gu)return e;var n=new Map,r=va(e),a=Ne(0),o=Gt,s=c=>{if(Gt===o)return c();var u=x,d=Gt;Ce(null),ri(o);var _=c();return Ce(u),ri(d),_};r&&(n.set("length",Ne(e.length)),b&&(e=Zc(e)));var i="";let l=!1;function f(c){if(!l){l=!0,i=c,$e(a,`${i} version`);for(const[u,d]of n)$e(d,It(i,u));l=!1}}return new Proxy(e,{defineProperty(c,u,d){(!("value"in d)||d.configurable===!1||d.enumerable===!1||d.writable===!1)&&rc();var _=n.get(u);return _===void 0?s(()=>{var m=Ne(d.value);return n.set(u,m),b&&typeof u=="string"&&$e(m,It(i,u)),m}):me(_,d.value,!0),!0},deleteProperty(c,u){var d=n.get(u);if(d===void 0){if(u in c){const _=s(()=>Ne(se));n.set(u,_),Un(a),b&&$e(_,It(i,u))}}else me(d,se),Un(a);return!0},get(c,u,d){var h;if(u===ut)return e;if(b&&u===ms)return f;var _=n.get(u),m=u in c;if(_===void 0&&(!m||(h=ot(c,u))!=null&&h.writable)&&(_=s(()=>{var v=dn(m?c[u]:se),F=Ne(v);return b&&$e(F,It(i,u)),F}),n.set(u,_)),_!==void 0){var w=M(_);return w===se?void 0:w}return Reflect.get(c,u,d)},getOwnPropertyDescriptor(c,u){var d=Reflect.getOwnPropertyDescriptor(c,u);if(d&&"value"in d){var _=n.get(u);_&&(d.value=M(_))}else if(d===void 0){var m=n.get(u),w=m==null?void 0:m.v;if(m!==void 0&&w!==se)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return d},has(c,u){var w;if(u===ut)return!0;var d=n.get(u),_=d!==void 0&&d.v!==se||Reflect.has(c,u);if(d!==void 0||R!==null&&(!_||(w=ot(c,u))!=null&&w.writable)){d===void 0&&(d=s(()=>{var h=_?dn(c[u]):se,v=Ne(h);return b&&$e(v,It(i,u)),v}),n.set(u,d));var m=M(d);if(m===se)return!1}return _},set(c,u,d,_){var H;var m=n.get(u),w=u in c;if(r&&u==="length")for(var h=d;h<m.v;h+=1){var v=n.get(h+"");v!==void 0?me(v,se):h in c&&(v=s(()=>Ne(se)),n.set(h+"",v),b&&$e(v,It(i,h)))}if(m===void 0)(!w||(H=ot(c,u))!=null&&H.writable)&&(m=s(()=>Ne(void 0)),b&&$e(m,It(i,u)),me(m,dn(d)),n.set(u,m));else{w=m.v!==se;var F=s(()=>dn(d));me(m,F)}var y=Reflect.getOwnPropertyDescriptor(c,u);if(y!=null&&y.set&&y.set.call(_,d),!w){if(r&&typeof u=="string"){var E=n.get("length"),A=Number(u);Number.isInteger(A)&&A>=E.v&&me(E,A+1)}Un(a)}return!0},ownKeys(c){M(a);var u=Reflect.ownKeys(c).filter(m=>{var w=n.get(m);return w===void 0||w.v!==se});for(var[d,_]of n)_.v!==se&&!(d in c)&&u.push(d);return u},setPrototypeOf(){ac()}})}function It(e,t){return typeof t=="symbol"?`${e}[Symbol(${t.description??""})]`:Kc.test(t)?`${e}.${t}`:/^\d+$/.test(t)?`${e}[${t}]`:`${e}['${t}']`}function Xn(e){try{if(e!==null&&typeof e=="object"&&ut in e)return e[ut]}catch{}return e}function Yc(e,t){return Object.is(Xn(e),Xn(t))}const Qc=new Set(["copyWithin","fill","pop","push","reverse","shift","sort","splice","unshift"]);function Zc(e){return new Proxy(e,{get(t,n,r){var a=Reflect.get(t,n,r);return Qc.has(n)?function(...o){Uc();var s=a.apply(this,o);return Bs(),s}:a}})}function Jc(){const e=Array.prototype,t=Array.__svelte_cleanup;t&&t();const{indexOf:n,lastIndexOf:r,includes:a}=e;e.indexOf=function(o,s){const i=n.call(this,o,s);if(i===-1){for(let l=s??0;l<this.length;l+=1)if(Xn(this[l])===o){qa("array.indexOf(...)");break}}return i},e.lastIndexOf=function(o,s){const i=r.call(this,o,s??this.length-1);if(i===-1){for(let l=0;l<=(s??this.length-1);l+=1)if(Xn(this[l])===o){qa("array.lastIndexOf(...)");break}}return i},e.includes=function(o,s){const i=a.call(this,o,s);if(!i){for(let l=0;l<this.length;l+=1)if(Xn(this[l])===o){qa("array.includes(...)");break}}return i},Array.__svelte_cleanup=()=>{e.indexOf=n,e.lastIndexOf=r,e.includes=a}}var Gs,Ca,Hs,Ws;function zc(){if(Gs===void 0){Gs=window,Ca=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;Hs=ot(t,"firstChild").get,Ws=ot(t,"nextSibling").get,fs(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),fs(n)&&(n.__t=void 0),b&&(e.__svelte_meta=null,Jc())}}function ct(e=""){return document.createTextNode(e)}function pn(e){return Hs.call(e)}function Kn(e){return Ws.call(e)}function S(e,t){return pn(e)}function X(e,t=!1){{var n=pn(e);return n instanceof Comment&&n.data===""?Kn(n):n}}function P(e,t=1,n=!1){let r=e;for(;t--;)r=Kn(r);return r}function ef(e){e.textContent=""}function js(){return!1}function $s(e,t,n){return document.createElementNS(t??bs,e,void 0)}function tf(e,t){if(t){const n=document.body;e.autofocus=!0,Ue(()=>{document.activeElement===n&&e.focus()})}}function xa(e){var t=x,n=R;Ce(null),He(null);try{return e()}finally{Ce(t),He(n)}}function nf(e){R===null&&(x===null&&Zu(e),Qu()),Mt&&Yu(e)}function rf(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function Xe(e,t,n){var r=R;if(b)for(;r!==null&&(r.f&Nr)!==0;)r=r.parent;r!==null&&(r.f&qe)!==0&&(e|=qe);var a={ctx:K,deps:null,nodes:null,f:e|ue|Pe,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null};if(b&&(a.component_function=$n),n)try{hn(a)}catch(i){throw fe(a),i}else t!==null&&Ve(a);var o=a;if(n&&o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&on)===0&&(o=o.first,(e&st)!==0&&(e&gt)!==0&&o!==null&&(o.f|=gt)),o!==null&&(o.parent=r,r!==null&&rf(o,r),x!==null&&(x.f&le)!==0&&(e&Rt)===0)){var s=x;(s.effects??(s.effects=[])).push(o)}return a}function Ta(){return x!==null&&!Ge}function Ra(e){const t=Xe(Fr,null,!1);return z(t,oe),t.teardown=e,t}function af(e){nf("$effect"),b&&Tt(e,"name",{value:"$effect"});var t=R.f,n=!x&&(t&Le)!==0&&(t&Dt)===0;if(n){var r=K;(r.e??(r.e=[])).push(e)}else return Us(e)}function Us(e){return Xe(Hn|ju,e,!1)}function of(e){qt.ensure();const t=Xe(Rt|on,e,!0);return(n={})=>new Promise(r=>{n.outro?Bt(t,()=>{fe(t),r(void 0)}):(fe(t),r(void 0))})}function Da(e){return Xe(Hn,e,!1)}function sf(e){return Xe(Cr|on,e,!0)}function Xs(e,t=0){return Xe(Fr|t,e,!0)}function ft(e,t=[],n=[],r=[]){Ts(r,t,n,a=>{Xe(Fr,()=>e(...a.map(M)),!0)})}function Yn(e,t=0){var n=Xe(st|t,e,!0);return b&&(n.dev_stack=ln),n}function Ks(e,t=0){var n=Xe(ga|t,e,!0);return b&&(n.dev_stack=ln),n}function ve(e){return Xe(Le|on,e,!0)}function Ys(e){var t=e.teardown;if(t!==null){const n=Mt,r=x;ei(!0),Ce(null);try{t.call(null)}finally{ei(n),Ce(r)}}}function Oa(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const a=n.ac;a!==null&&xa(()=>{a.abort(Ot)});var r=n.next;(n.f&Rt)!==0?n.parent=null:fe(n,t),n=r}}function lf(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&Le)===0&&fe(t),t=n}}function fe(e,t=!0){var n=!1;(t||(e.f&ps)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(uf(e.nodes.start,e.nodes.end),n=!0),Oa(e,t&&!n),Zn(e,0),z(e,it);var r=e.nodes&&e.nodes.t;if(r!==null)for(const o of r)o.stop();Ys(e);var a=e.parent;a!==null&&a.first!==null&&Qs(e),b&&(e.component_function=null),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function uf(e,t){for(;e!==null;){var n=e===t?null:Kn(e);e.remove(),e=n}}function Qs(e){var t=e.parent,n=e.prev,r=e.next;n!==null&&(n.next=r),r!==null&&(r.prev=n),t!==null&&(t.first===e&&(t.first=r),t.last===e&&(t.last=n))}function Bt(e,t,n=!0){var r=[];Zs(e,r,!0);var a=()=>{n&&fe(e),t&&t()},o=r.length;if(o>0){var s=()=>--o||a();for(var i of r)i.out(s)}else a()}function Zs(e,t,n){if((e.f&qe)===0){e.f^=qe;var r=e.nodes&&e.nodes.t;if(r!==null)for(const i of r)(i.is_global||n)&&t.push(i);for(var a=e.first;a!==null;){var o=a.next,s=(a.f&gt)!==0||(a.f&Le)!==0&&(e.f&st)!==0;Zs(a,t,s?n:!1),a=o}}}function La(e){Js(e,!0)}function Js(e,t){if((e.f&qe)!==0){e.f^=qe,(e.f&oe)===0&&(z(e,ue),Ve(e));for(var n=e.first;n!==null;){var r=n.next,a=(n.f&gt)!==0||(n.f&Le)!==0;Js(n,a?t:!1),n=r}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function zs(e,t){if(e.nodes)for(var n=e.nodes.start,r=e.nodes.end;n!==null;){var a=n===r?null:Kn(n);t.append(n),n=a}}let Or=!1,Mt=!1;function ei(e){Mt=e}let x=null,Ge=!1;function Ce(e){x=e}let R=null;function He(e){R=e}let xe=null;function ti(e){x!==null&&(xe===null?xe=[e]:xe.push(e))}let ge=null,Se=0,Te=null;function cf(e){Te=e}let ni=1,Vt=0,Gt=Vt;function ri(e){Gt=e}function ai(){return++ni}function Qn(e){var t=e.f;if((t&ue)!==0)return!0;if(t&le&&(e.f&=~bt),(t&Ie)!==0){for(var n=e.deps,r=n.length,a=0;a<r;a++){var o=n[a];if(Qn(o)&&Os(o),o.wv>e.wv)return!0}(t&Pe)!==0&&ce===null&&z(e,oe)}return!1}function oi(e,t,n=!0){var r=e.reactions;if(r!==null&&!(xe!==null&&xt.call(xe,e)))for(var a=0;a<r.length;a++){var o=r[a];(o.f&le)!==0?oi(o,t,!1):t===o&&(n?z(o,ue):(o.f&oe)!==0&&z(o,Ie),Ve(o))}}function Ia(e){var w;var t=ge,n=Se,r=Te,a=x,o=xe,s=K,i=Ge,l=Gt,f=e.f;ge=null,Se=0,Te=null,x=(f&(Le|Rt))===0?e:null,xe=null,sn(e.ctx),Ge=!1,Gt=++Vt,e.ac!==null&&(xa(()=>{e.ac.abort(Ot)}),e.ac=null);try{e.f|=ya;var c=e.fn,u=c();e.f|=Dt;var d=e.deps,_=L==null?void 0:L.is_fork;if(ge!==null){var m;if(_||Zn(e,Se),d!==null&&Se>0)for(d.length=Se+ge.length,m=0;m<ge.length;m++)d[Se+m]=ge[m];else e.deps=d=ge;if(Ta()&&(e.f&Pe)!==0)for(m=Se;m<d.length;m++)((w=d[m]).reactions??(w.reactions=[])).push(e)}else!_&&d!==null&&Se<d.length&&(Zn(e,Se),d.length=Se);if(Ms()&&Te!==null&&!Ge&&d!==null&&(e.f&(le|Ie|ue))===0)for(m=0;m<Te.length;m++)oi(Te[m],e);if(a!==null&&a!==e){if(Vt++,a.deps!==null)for(let h=0;h<n;h+=1)a.deps[h].rv=Vt;if(t!==null)for(const h of t)h.rv=Vt;Te!==null&&(r===null?r=Te:r.push(...Te))}return(e.f&yt)!==0&&(e.f^=yt),u}catch(h){return ks(h)}finally{e.f^=ya,ge=t,Se=n,Te=r,x=a,xe=o,sn(s),Ge=i,Gt=l}}function ff(e,t){let n=t.reactions;if(n!==null){var r=Iu.call(n,e);if(r!==-1){var a=n.length-1;a===0?n=t.reactions=null:(n[r]=n[a],n.pop())}}if(n===null&&(t.f&le)!==0&&(ge===null||!xt.call(ge,t))){var o=t;(o.f&Pe)!==0&&(o.f^=Pe,o.f&=~bt),Ma(o),$c(o),Zn(o,0)}}function Zn(e,t){var n=e.deps;if(n!==null)for(var r=t;r<n.length;r++)ff(e,n[r])}function hn(e){var t=e.f;if((t&it)===0){z(e,oe);var n=R,r=Or;if(R=e,Or=!0,b){var a=$n;Ss(e.component_function);var o=ln;xr(e.dev_stack??ln)}try{(t&(st|ga))!==0?lf(e):Oa(e),Ys(e);var s=Ia(e);e.teardown=typeof s=="function"?s:null,e.wv=ni;var i;b&&kc&&(e.f&ue)!==0&&e.deps}finally{Or=r,R=n,b&&(Ss(a),xr(o))}}}function M(e){var t=e.f,n=(t&le)!==0;if(x!==null&&!Ge){var r=R!==null&&(R.f&it)!==0;if(!r&&(xe===null||!xt.call(xe,e))){var a=x.deps;if((x.f&ya)!==0)e.rv<Vt&&(e.rv=Vt,ge===null&&a!==null&&a[Se]===e?Se++:ge===null?ge=[e]:ge.push(e));else{(x.deps??(x.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[x]:xt.call(o,x)||o.push(x)}}}if(b&&Hc.delete(e),Mt&&St.has(e))return St.get(e);if(n){var s=e;if(Mt){var i=s.v;return((s.f&oe)===0&&s.reactions!==null||ii(s))&&(i=Fa(s)),St.set(s,i),i}var l=(s.f&Pe)===0&&!Ge&&x!==null&&(Or||(x.f&Pe)!==0),f=(s.f&Dt)===0;Qn(s)&&(l&&(s.f|=Pe),Os(s)),l&&!f&&(Ls(s),si(s))}if(ce!=null&&ce.has(e))return ce.get(e);if((e.f&yt)!==0)throw e.v;return e.v}function si(e){if(e.f|=Pe,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&le)!==0&&(t.f&Pe)===0&&(Ls(t),si(t))}function ii(e){if(e.v===se)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(St.has(t)||(t.f&le)!==0&&ii(t))return!0;return!1}function Lr(e){var t=Ge;try{return Ge=!0,e()}finally{Ge=t}}function df(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const pf=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function hf(e){return pf.includes(e)}const mf={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function _f(e){return e=e.toLowerCase(),mf[e]??e}const vf=["touchstart","touchmove"];function gf(e){return vf.includes(e)}const Ht=Symbol("events"),li=new Set,Ba=new Set;function bf(e,t,n,r={}){function a(o){if(r.capture||Ga.call(t,o),!o.cancelBubble)return xa(()=>n==null?void 0:n.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Ue(()=>{t.addEventListener(e,a,r)}):t.addEventListener(e,a,r),a}function de(e,t,n){(t[Ht]??(t[Ht]={}))[e]=n}function Va(e){for(var t=0;t<e.length;t++)li.add(e[t]);for(var n of Ba)n(e)}let ui=null;function Ga(e){var h,v;var t=this,n=t.ownerDocument,r=e.type,a=((h=e.composedPath)==null?void 0:h.call(e))||[],o=a[0]||e.target;ui=e;var s=0,i=ui===e&&e[Ht];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[Ht]=t;return}var f=a.indexOf(t);if(f===-1)return;l<=f&&(s=l)}if(o=a[s]||e.target,o!==t){Tt(e,"currentTarget",{configurable:!0,get(){return o||n}});var c=x,u=R;Ce(null),He(null);try{for(var d,_=[];o!==null;){var m=o.assignedSlot||o.parentNode||o.host||null;try{var w=(v=o[Ht])==null?void 0:v[r];w!=null&&(!o.disabled||e.target===o)&&w.call(o,e)}catch(F){d?_.push(F):d=F}if(e.cancelBubble||m===t||m===null)break;o=m}if(d){for(let F of _)queueMicrotask(()=>{throw F});throw d}}finally{e[Ht]=t,delete e.currentTarget,Ce(c),He(u)}}}const Ha=((Bi=globalThis==null?void 0:globalThis.window)==null?void 0:Bi.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function yf(e){return(Ha==null?void 0:Ha.createHTML(e))??e}function ci(e){var t=$s("template");return t.innerHTML=yf(e.replaceAll("<!>","<!---->")),t.content}function Jn(e,t){var n=R;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function Ke(e,t){var n=(t&mc)!==0,r=(t&_c)!==0,a,o=!e.startsWith("<!>");return()=>{a===void 0&&(a=ci(o?e:"<!>"+e),n||(a=pn(a)));var s=r||Ca?document.importNode(a,!0):a.cloneNode(!0);if(n){var i=pn(s),l=s.lastChild;Jn(i,l)}else Jn(s,s);return s}}function wf(e,t,n="svg"){var r=!e.startsWith("<!>"),a=`<${n}>${r?e:"<!>"+e}</${n}>`,o;return()=>{if(!o){var s=ci(a),i=pn(s);o=pn(i)}var l=o.cloneNode(!0);return Jn(l,l),l}}function qf(e,t){return wf(e,t,"svg")}function Y(){var e=document.createDocumentFragment(),t=document.createComment(""),n=ct();return e.append(t,n),Jn(t,n),e}function O(e,t){e!==null&&e.before(t)}function kt(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function Sf(e,t){return Mf(e,t)}const Ir=new Map;function Mf(e,{target:t,anchor:n,props:r={},events:a,context:o,intro:s=!0,transformError:i}){zc();var l=void 0,f=of(()=>{var c=n??t.appendChild(ct());Ic(c,{pending:()=>{}},_=>{V({});var m=K;o&&(m.c=o),a&&(r.$$events=a),l=e(_,r)||{},G()},i);var u=new Set,d=_=>{for(var m=0;m<_.length;m++){var w=_[m];if(!u.has(w)){u.add(w);var h=gf(w);for(const y of[t,document]){var v=Ir.get(y);v===void 0&&(v=new Map,Ir.set(y,v));var F=v.get(w);F===void 0?(y.addEventListener(w,Ga,{passive:h}),v.set(w,1)):v.set(w,F+1)}}}};return d(Pr(li)),Ba.add(d),()=>{var h;for(var _ of u)for(const v of[t,document]){var m=Ir.get(v),w=m.get(_);--w==0?(v.removeEventListener(_,Ga),m.delete(_),m.size===0&&Ir.delete(v)):m.set(_,w)}Ba.delete(d),c!==n&&((h=c.parentNode)==null||h.removeChild(c))}});return Wa.set(l,f),l}let Wa=new WeakMap;function fi(e,t){const n=Wa.get(e);return n?(Wa.delete(e),n(t)):(b&&(ut in e?qc():yc()),Promise.resolve())}class ja{constructor(t,n=!0){nt(this,"anchor");T(this,je,new Map);T(this,Je,new Map);T(this,Ee,new Map);T(this,Xt,new Set);T(this,sr,!0);T(this,ir,()=>{var t=L;if(p(this,je).has(t)){var n=p(this,je).get(t),r=p(this,Je).get(n);if(r)La(r),p(this,Xt).delete(n);else{var a=p(this,Ee).get(n);a&&(p(this,Je).set(n,a.effect),p(this,Ee).delete(n),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),r=a.effect)}for(const[o,s]of p(this,je)){if(p(this,je).delete(o),o===t)break;const i=p(this,Ee).get(s);i&&(fe(i.effect),p(this,Ee).delete(s))}for(const[o,s]of p(this,Je)){if(o===n||p(this,Xt).has(o))continue;const i=()=>{if(Array.from(p(this,je).values()).includes(o)){var f=document.createDocumentFragment();zs(s,f),f.append(ct()),p(this,Ee).set(o,{effect:s,fragment:f})}else fe(s);p(this,Xt).delete(o),p(this,Je).delete(o)};p(this,sr)||!r?(p(this,Xt).add(o),Bt(s,i,!1)):i()}}});T(this,Wr,t=>{p(this,je).delete(t);const n=Array.from(p(this,je).values());for(const[r,a]of p(this,Ee))n.includes(r)||(fe(a.effect),p(this,Ee).delete(r))});this.anchor=t,C(this,sr,n)}ensure(t,n){var r=L,a=js();if(n&&!p(this,Je).has(t)&&!p(this,Ee).has(t))if(a){var o=document.createDocumentFragment(),s=ct();o.append(s),p(this,Ee).set(t,{effect:ve(()=>n(s)),fragment:o})}else p(this,Je).set(t,ve(()=>n(this.anchor)));if(p(this,je).set(r,t),a){for(const[i,l]of p(this,Je))i===t?r.unskip_effect(l):r.skip_effect(l);for(const[i,l]of p(this,Ee))i===t?r.unskip_effect(l.effect):r.skip_effect(l.effect);r.oncommit(p(this,ir)),r.ondiscard(p(this,Wr))}else p(this,ir).call(this)}}je=new WeakMap,Je=new WeakMap,Ee=new WeakMap,Xt=new WeakMap,sr=new WeakMap,ir=new WeakMap,Wr=new WeakMap;function mn(e,t,n=!1){var r=new ja(e),a=n?gt:0;function o(s,i){r.ensure(s,i)}Yn(()=>{var s=!1;t((i,l=0)=>{s=!0,o(l,i)}),s||o(!1,null)},a)}function di(e,t){return t}function kf(e,t,n){for(var r=[],a=t.length,o,s=t.length,i=0;i<a;i++){let u=t[i];Bt(u,()=>{if(o){if(o.pending.delete(u),o.done.add(u),o.pending.size===0){var d=e.outrogroups;$a(Pr(o.done)),d.delete(o),d.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var l=r.length===0&&n!==null;if(l){var f=n,c=f.parentNode;ef(c),c.append(f),e.items.clear()}$a(t,!l)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function $a(e,t=!0){for(var n=0;n<e.length;n++)fe(e[n],t)}var pi;function Br(e,t,n,r,a,o=null){var s=e,i=new Map,l=(t&gs)!==0;if(l){var f=e;s=f.appendChild(ct())}var c=null,u=Rs(()=>{var v=n();return va(v)?v:v==null?[]:Pr(v)}),d,_=!0;function m(){h.fallback=c,Ef(h,d,s,t,r),c!==null&&(d.length===0?(c.f&lt)===0?La(c):(c.f^=lt,er(c,null,s)):Bt(c,()=>{c=null}))}var w=Yn(()=>{d=M(u);for(var v=d.length,F=new Set,y=L,E=js(),A=0;A<v;A+=1){var H=d[A],D=r(H,A);if(b){var ye=r(H,A);D!==ye&&Ku(String(A),String(D),String(ye))}var I=_?null:i.get(D);I?(I.v&&fn(I.v,H),I.i&&fn(I.i,A),E&&y.unskip_effect(I.e)):(I=Af(i,_?s:pi??(pi=ct()),H,D,A,a,t,n),_||(I.e.f|=lt),i.set(D,I)),F.add(D)}if(v===0&&o&&!c&&(_?c=ve(()=>o(s)):(c=ve(()=>o(pi??(pi=ct()))),c.f|=lt)),v>F.size&&(b?Pf(d,r):vs("","","")),!_)if(E){for(const[ze,g]of i)F.has(ze)||y.skip_effect(g.e);y.oncommit(m),y.ondiscard(()=>{})}else m();M(u)}),h={effect:w,items:i,outrogroups:null,fallback:c};_=!1}function zn(e){for(;e!==null&&(e.f&Le)===0;)e=e.next;return e}function Ef(e,t,n,r,a){var ze,g,Kt,N,et,Pt,Yt,En,Qt;var o=(r&uc)!==0,s=t.length,i=e.items,l=zn(e.effect.first),f,c=null,u,d=[],_=[],m,w,h,v;if(o)for(v=0;v<s;v+=1)m=t[v],w=a(m,v),h=i.get(w).e,(h.f&lt)===0&&((g=(ze=h.nodes)==null?void 0:ze.a)==null||g.measure(),(u??(u=new Set)).add(h));for(v=0;v<s;v+=1){if(m=t[v],w=a(m,v),h=i.get(w).e,e.outrogroups!==null)for(const Ae of e.outrogroups)Ae.pending.delete(h),Ae.done.delete(h);if((h.f&lt)!==0)if(h.f^=lt,h===l)er(h,null,n);else{var F=c?c.next:l;h===e.effect.last&&(e.effect.last=h.prev),h.prev&&(h.prev.next=h.next),h.next&&(h.next.prev=h.prev),Et(e,c,h),Et(e,h,F),er(h,F,n),c=h,d=[],_=[],l=zn(c.next);continue}if((h.f&qe)!==0&&(La(h),o&&((N=(Kt=h.nodes)==null?void 0:Kt.a)==null||N.unfix(),(u??(u=new Set)).delete(h))),h!==l){if(f!==void 0&&f.has(h)){if(d.length<_.length){var y=_[0],E;c=y.prev;var A=d[0],H=d[d.length-1];for(E=0;E<d.length;E+=1)er(d[E],y,n);for(E=0;E<_.length;E+=1)f.delete(_[E]);Et(e,A.prev,H.next),Et(e,c,A),Et(e,H,y),l=y,c=H,v-=1,d=[],_=[]}else f.delete(h),er(h,l,n),Et(e,h.prev,h.next),Et(e,h,c===null?e.effect.first:c.next),Et(e,c,h),c=h;continue}for(d=[],_=[];l!==null&&l!==h;)(f??(f=new Set)).add(l),_.push(l),l=zn(l.next);if(l===null)continue}(h.f&lt)===0&&d.push(h),c=h,l=zn(h.next)}if(e.outrogroups!==null){for(const Ae of e.outrogroups)Ae.pending.size===0&&($a(Pr(Ae.done)),(et=e.outrogroups)==null||et.delete(Ae));e.outrogroups.size===0&&(e.outrogroups=null)}if(l!==null||f!==void 0){var D=[];if(f!==void 0)for(h of f)(h.f&qe)===0&&D.push(h);for(;l!==null;)(l.f&qe)===0&&l!==e.fallback&&D.push(l),l=zn(l.next);var ye=D.length;if(ye>0){var I=(r&gs)!==0&&s===0?n:null;if(o){for(v=0;v<ye;v+=1)(Yt=(Pt=D[v].nodes)==null?void 0:Pt.a)==null||Yt.measure();for(v=0;v<ye;v+=1)(Qt=(En=D[v].nodes)==null?void 0:En.a)==null||Qt.fix()}kf(e,D,I)}}o&&Ue(()=>{var Ae,De;if(u!==void 0)for(h of u)(De=(Ae=h.nodes)==null?void 0:Ae.a)==null||De.apply()})}function Af(e,t,n,r,a,o,s,i){var l=(s&ic)!==0?(s&cc)===0?Xc(n,!1,!1):Lt(n):null,f=(s&lc)!==0?Lt(a):null;return b&&l&&(l.trace=()=>{i()[(f==null?void 0:f.v)??a]}),{v:l,i:f,e:ve(()=>(o(t,l??n,f??a,i),()=>{e.delete(r)}))}}function er(e,t,n){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end,o=t&&(t.f&lt)===0?t.nodes.start:n;r!==null;){var s=Kn(r);if(o.before(r),r===a)return;r=s}}function Et(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function Pf(e,t){const n=new Map,r=e.length;for(let a=0;a<r;a++){const o=t(e[a],a);if(n.has(o)){const s=String(n.get(o)),i=String(a);let l=String(o);l.startsWith("[object ")&&(l=null),vs(s,i,l)}n.set(o,a)}}function Q(e,t,...n){var r=new ja(e);Yn(()=>{const a=t()??null;b&&a==null&&zu(),r.ensure(a,a&&(o=>a(o,...n)))},gt)}function Ff(e,t,n,r,a,o){var s=null,i=e,l=new ja(i,!1);Yn(()=>{const f=t()||null;var c=gc;if(f===null){l.ensure(null,null);return}return l.ensure(f,u=>{if(f){if(s=$s(f,c),Jn(s,s),r){var d=s.appendChild(ct());r(s,d)}R.nodes.end=s,u.before(s)}}),()=>{}},gt),Ra(()=>{})}function Nf(e,t){var n=void 0,r;Ks(()=>{n!==(n=t())&&(r&&(fe(r),r=null),n&&(r=ve(()=>{Da(()=>n(e))})))})}function hi(e){var t,n,r="";if(typeof e=="string"||typeof e=="number")r+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(n=hi(e[t]))&&(r&&(r+=" "),r+=n)}else for(n in e)e[n]&&(r&&(r+=" "),r+=n);return r}function Cf(){for(var e,t,n=0,r="",a=arguments.length;n<a;n++)(e=arguments[n])&&(t=hi(e))&&(r&&(r+=" "),r+=t);return r}function mi(e){return typeof e=="object"?Cf(e):e??""}const _i=[...` 	
\r\f \v\uFEFF`];function xf(e,t,n){var r=e==null?"":""+e;if(t&&(r=r?r+" "+t:t),n){for(var a of Object.keys(n))if(n[a])r=r?r+" "+a:a;else if(r.length)for(var o=a.length,s=0;(s=r.indexOf(a,s))>=0;){var i=s+o;(s===0||_i.includes(r[s-1]))&&(i===r.length||_i.includes(r[i]))?r=(s===0?"":r.substring(0,s))+r.substring(i+1):s=i}}return r===""?null:r}function vi(e,t=!1){var n=t?" !important;":";",r="";for(var a of Object.keys(e)){var o=e[a];o!=null&&o!==""&&(r+=" "+a+": "+o+n)}return r}function Ua(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Tf(e,t){if(t){var n="",r,a;if(Array.isArray(t)?(r=t[0],a=t[1]):r=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,i=!1,l=[];r&&l.push(...Object.keys(r).map(Ua)),a&&l.push(...Object.keys(a).map(Ua));var f=0,c=-1;const w=e.length;for(var u=0;u<w;u++){var d=e[u];if(i?d==="/"&&e[u-1]==="*"&&(i=!1):o?o===d&&(o=!1):d==="/"&&e[u+1]==="*"?i=!0:d==='"'||d==="'"?o=d:d==="("?s++:d===")"&&s--,!i&&o===!1&&s===0){if(d===":"&&c===-1)c=u;else if(d===";"||u===w-1){if(c!==-1){var _=Ua(e.substring(f,c).trim());if(!l.includes(_)){d!==";"&&u++;var m=e.substring(f,u).trim();n+=" "+m+";"}}f=u+1,c=-1}}}}return r&&(n+=vi(r)),a&&(n+=vi(a,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function Xa(e,t,n,r,a,o){var s=e.__className;if(s!==n||s===void 0){var i=xf(n,r,o);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=n}else if(o&&a!==o)for(var l in o){var f=!!o[l];(a==null||f!==!!a[l])&&e.classList.toggle(l,f)}return o}function Ka(e,t={},n,r){for(var a in n){var o=n[a];t[a]!==o&&(n[a]==null?e.style.removeProperty(a):e.style.setProperty(a,o,r))}}function Rf(e,t,n,r){var a=e.__style;if(a!==t){var o=Tf(t,r);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else r&&(Array.isArray(r)?(Ka(e,n==null?void 0:n[0],r[0]),Ka(e,n==null?void 0:n[1],r[1],"important")):Ka(e,n,r));return r}function Ya(e,t,n=!1){if(e.multiple){if(t==null)return;if(!va(t))return wc();for(var r of e.options)r.selected=t.includes(gi(r));return}for(r of e.options){var a=gi(r);if(Yc(a,t)){r.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function Df(e){var t=new MutationObserver(()=>{Ya(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Ra(()=>{t.disconnect()})}function gi(e){return"__value"in e?e.__value:e.value}const tr=Symbol("class"),nr=Symbol("style"),bi=Symbol("is custom element"),yi=Symbol("is html"),Of=wa?"option":"OPTION",Lf=wa?"select":"SELECT",If=wa?"progress":"PROGRESS";function Bf(e,t){var n=Qa(e);n.value===(n.value=t??void 0)||e.value===t&&(t!==0||e.nodeName!==If)||(e.value=t??"")}function Vf(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function q(e,t,n,r){var a=Qa(e);a[t]!==(a[t]=n)&&(t==="loading"&&(e[$u]=n),n==null?e.removeAttribute(t):typeof n!="string"&&Si(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function Gf(e,t,n,r,a=!1,o=!1){var s=Qa(e),i=s[bi],l=!s[yi],f=t||{},c=e.nodeName===Of;for(var u in t)u in n||(n[u]=null);n.class?n.class=mi(n.class):n[tr]&&(n.class=null),n[nr]&&(n.style??(n.style=null));var d=Si(e);for(const y in n){let E=n[y];if(c&&y==="value"&&E==null){e.value=e.__value="",f[y]=E;continue}if(y==="class"){var _=e.namespaceURI==="http://www.w3.org/1999/xhtml";Xa(e,_,E,r,t==null?void 0:t[tr],n[tr]),f[y]=E,f[tr]=n[tr];continue}if(y==="style"){Rf(e,E,t==null?void 0:t[nr],n[nr]),f[y]=E,f[nr]=n[nr];continue}var m=f[y];if(!(E===m&&!(E===void 0&&e.hasAttribute(y)))){f[y]=E;var w=y[0]+y[1];if(w!=="$$")if(w==="on"){const A={},H="$$"+y;let D=y.slice(2);var h=hf(D);if(df(D)&&(D=D.slice(0,-7),A.capture=!0),!h&&m){if(E!=null)continue;e.removeEventListener(D,f[H],A),f[H]=null}if(h)de(D,e,E),Va([D]);else if(E!=null){let ye=function(I){f[y].call(this,I)};f[H]=bf(D,e,ye,A)}}else if(y==="style")q(e,y,E);else if(y==="autofocus")tf(e,!!E);else if(!i&&(y==="__value"||y==="value"&&E!=null))e.value=e.__value=E;else if(y==="selected"&&c)Vf(e,E);else{var v=y;l||(v=_f(v));var F=v==="defaultValue"||v==="defaultChecked";if(E==null&&!i&&!F)if(s[y]=null,v==="value"||v==="checked"){let A=e;const H=t===void 0;if(v==="value"){let D=A.defaultValue;A.removeAttribute(v),A.defaultValue=D,A.value=A.__value=H?D:null}else{let D=A.defaultChecked;A.removeAttribute(v),A.defaultChecked=D,A.checked=H?D:!1}}else e.removeAttribute(y);else F||d.includes(v)&&(i||typeof E!="string")?(e[v]=E,v in s&&(s[v]=se)):typeof E!="function"&&q(e,v,E)}}}return f}function wi(e,t,n=[],r=[],a=[],o,s=!1,i=!1){Ts(a,n,r,l=>{var f=void 0,c={},u=e.nodeName===Lf,d=!1;if(Ks(()=>{var m=t(...l.map(M)),w=Gf(e,f,m,o,s,i);d&&u&&"value"in m&&Ya(e,m.value);for(let v of Object.getOwnPropertySymbols(c))m[v]||fe(c[v]);for(let v of Object.getOwnPropertySymbols(m)){var h=m[v];v.description===bc&&(!f||h!==f[v])&&(c[v]&&fe(c[v]),c[v]=ve(()=>Nf(e,()=>h))),w[v]=h}f=w}),u){var _=e;Da(()=>{Ya(_,f.value,!0),Df(_)})}d=!0})}function Qa(e){return e.__attributes??(e.__attributes={[bi]:e.nodeName.includes("-"),[yi]:e.namespaceURI===bs})}var qi=new Map;function Si(e){var t=e.getAttribute("is")||e.nodeName,n=qi.get(t);if(n)return n;qi.set(t,n=[]);for(var r,a=e,o=Element.prototype;o!==a;){r=Bu(a);for(var s in r)r[s].set&&n.push(s);a=cs(a)}return n}function Mi(e,t){return e===t||(e==null?void 0:e[ut])===t}function Hf(e={},t,n,r){return Da(()=>{var a,o;return Xs(()=>{a=o,o=[],Lr(()=>{e!==n(...o)&&(t(e,...o),a&&Mi(n(...a),e)&&t(null,...a))})}),()=>{Ue(()=>{o&&Mi(n(...o),e)&&t(null,...o)})}}),e}let Vr=!1;function Wf(e){var t=Vr;try{return Vr=!1,[e(),Vr]}finally{Vr=t}}const jf={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return b&&tc(`${e.name}.${String(t)}`),!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Z(e,t,n){return new Proxy(b?{props:e,exclude:t,name:n,other:{},to_proxy:[]}:{props:e,exclude:t},jf)}const $f={get(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(Gn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r)return r[t]}},set(e,t,n){let r=e.props.length;for(;r--;){let a=e.props[r];Gn(a)&&(a=a());const o=ot(a,t);if(o&&o.set)return o.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(Gn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r){const a=ot(r,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===ut||t===hs)return!1;for(let n of e.props)if(Gn(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(Gn(n)&&(n=n()),!!n){for(const r in n)t.includes(r)||t.push(r);for(const r of Object.getOwnPropertySymbols(n))t.includes(r)||t.push(r)}return t}};function ee(...e){return new Proxy({props:e},$f)}function _n(e,t,n,r){var F;var a=(n&pc)!==0,o=(n&hc)!==0,s=r,i=!0,l=()=>(i&&(i=!1,s=o?Lr(r):r),s),f;if(a){var c=ut in e||hs in e;f=((F=ot(e,t))==null?void 0:F.set)??(c&&t in e?y=>e[t]=y:void 0)}var u,d=!1;a?[u,d]=Wf(()=>e[t]):u=e[t],u===void 0&&r!==void 0&&(u=l(),f&&(ec(t),f(u)));var _;if(_=()=>{var y=e[t];return y===void 0?l():(i=!0,y)},(n&dc)===0)return _;if(f){var m=e.$$legacy;return(function(y,E){return arguments.length>0?((!E||m||d)&&f(E?_():y),y):_()})}var w=!1,h=((n&fc)!==0?Rr:Rs)(()=>(w=!1,_()));b&&(h.label=t),a&&M(h);var v=R;return(function(y,E){if(arguments.length>0){const A=E?M(h):a?dn(y):y;return me(h,A),w=!0,s!==void 0&&(s=A),y}return Mt&&w||(v.f&it)!==0?h.v:M(h)})}if(b){let e=function(t){if(!(t in globalThis)){let n;Object.defineProperty(globalThis,t,{configurable:!0,get:()=>{if(n!==void 0)return n;nc(t)},set:r=>{n=r}})}};e("$state"),e("$effect"),e("$derived"),e("$inspect"),e("$props"),e("$bindable")}function ki(e){K===null&&_s("onMount"),af(()=>{const t=Lr(e);if(typeof t=="function")return t})}const Uf="5";typeof window<"u"&&((Vi=window.__svelte??(window.__svelte={})).v??(Vi.v=new Set)).add(Uf);/**
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
 */const Xf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const Kf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const Yf=Symbol("lucide-context"),Qf=()=>Pc(Yf);var Zf=qf("<svg><!><!></svg>");function te(e,t){V(t,!0);const n=Qf()??{},r=_n(t,"color",19,()=>n.color??"currentColor"),a=_n(t,"size",19,()=>n.size??24),o=_n(t,"strokeWidth",19,()=>n.strokeWidth??2),s=_n(t,"absoluteStrokeWidth",19,()=>n.absoluteStrokeWidth??!1),i=_n(t,"iconNode",19,()=>[]),l=Z(t,["$$slots","$$events","$$legacy","name","color","size","strokeWidth","absoluteStrokeWidth","iconNode","children"]),f=Dr(()=>s()?Number(o())*24/Number(a()):o());var c=Zf();wi(c,_=>({...Xf,..._,...l,width:a(),height:a(),stroke:r(),"stroke-width":M(f),class:["lucide-icon lucide",n.class,t.name&&`lucide-${t.name}`,t.class]}),[()=>!t.children&&!Kf(l)&&{"aria-hidden":"true"}]);var u=S(c);Br(u,17,i,di,(_,m)=>{var w=Dr(()=>Wu(M(m),2));let h=()=>M(w)[0],v=()=>M(w)[1];var F=Y(),y=X(F);Ff(y,h,!0,(E,A)=>{wi(E,()=>({...v()}))}),O(_,F)});var d=P(u);Q(d,()=>t.children??U),O(e,c),G()}function Jf(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];te(e,ee({name:"chart-line"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function zf(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 9 6 6 6-6"}]];te(e,ee({name:"chevron-down"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function ed(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"}],["path",{d:"M12 17h.01"}]];te(e,ee({name:"circle-question-mark"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function td(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 12 18z"}],["path",{d:"M2 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 2 18z"}]];te(e,ee({name:"fast-forward"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function nd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]];te(e,ee({name:"folder-open"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function rd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["rect",{x:"14",y:"3",width:"5",height:"18",rx:"1"}],["rect",{x:"5",y:"3",width:"5",height:"18",rx:"1"}]];te(e,ee({name:"pause"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function ad(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"}]];te(e,ee({name:"play"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function od(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m15 14 5-5-5-5"}],["path",{d:"M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13"}]];te(e,ee({name:"redo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function sd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];te(e,ee({name:"refresh-cw"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function id(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m2 9 3-3 3 3"}],["path",{d:"M13 18H7a2 2 0 0 1-2-2V6"}],["path",{d:"m22 15-3 3-3-3"}],["path",{d:"M11 6h6a2 2 0 0 1 2 2v10"}]];te(e,ee({name:"repeat-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function ld(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 12 18z"}],["path",{d:"M22 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 22 18z"}]];te(e,ee({name:"rewind"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function ud(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]];te(e,ee({name:"scissors"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function cd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];te(e,ee({name:"settings"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function fd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];te(e,ee({name:"sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function dd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]];te(e,ee({name:"timer-reset"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function pd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];te(e,ee({name:"trash-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function hd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"}]];te(e,ee({name:"undo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function md(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}]];te(e,ee({name:"volume-1"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function _d(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}],["path",{d:"M19.364 18.364a9 9 0 0 0 0-12.728"}]];te(e,ee({name:"volume-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function vd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]];te(e,ee({name:"volume-x"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function gd(e,t){V(t,!0);/**
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
 */let n=Z(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}]];te(e,ee({name:"waves"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=Y(),i=X(s);Q(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}var bd=Ke('<span aria-hidden="true"><!></span>');function $(e,t){V(t,!0);const n=_n(t,"className",3,""),r=Dr(()=>["aqe-button-icon",n()].filter(Boolean).join(" "));var a=bd(),o=S(a);{var s=g=>{Jf(g,{size:14,strokeWidth:2})},i=g=>{zf(g,{size:14,strokeWidth:2})},l=g=>{ed(g,{size:14,strokeWidth:2})},f=g=>{td(g,{size:14,strokeWidth:2})},c=g=>{nd(g,{size:14,strokeWidth:2})},u=g=>{rd(g,{size:14,strokeWidth:2})},d=g=>{ad(g,{size:14,strokeWidth:2})},_=g=>{od(g,{size:14,strokeWidth:2})},m=g=>{sd(g,{size:14,strokeWidth:2})},w=g=>{id(g,{size:14,strokeWidth:2})},h=g=>{ld(g,{size:14,strokeWidth:2})},v=g=>{ud(g,{size:14,strokeWidth:2})},F=g=>{cd(g,{size:14,strokeWidth:2})},y=g=>{fd(g,{size:14,strokeWidth:2})},E=g=>{dd(g,{size:14,strokeWidth:2})},A=g=>{pd(g,{size:14,strokeWidth:2})},H=g=>{hd(g,{size:14,strokeWidth:2})},D=g=>{md(g,{size:14,strokeWidth:2})},ye=g=>{_d(g,{size:14,strokeWidth:2})},I=g=>{vd(g,{size:14,strokeWidth:2})},ze=g=>{gd(g,{size:14,strokeWidth:2})};mn(o,g=>{t.icon==="chart-line"?g(s):t.icon==="chevron-down"?g(i,1):t.icon==="circle-help"?g(l,2):t.icon==="fast-forward"?g(f,3):t.icon==="folder-open"?g(c,4):t.icon==="pause"?g(u,5):t.icon==="play"?g(d,6):t.icon==="redo-2"?g(_,7):t.icon==="refresh-cw"?g(m,8):t.icon==="repeat-2"?g(w,9):t.icon==="rewind"?g(h,10):t.icon==="scissors"?g(v,11):t.icon==="settings"?g(F,12):t.icon==="sparkles"?g(y,13):t.icon==="timer-reset"?g(E,14):t.icon==="trash-2"?g(A,15):t.icon==="undo-2"?g(H,16):t.icon==="volume-1"?g(D,17):t.icon==="volume-2"?g(ye,18):t.icon==="volume-x"?g(I,19):t.icon==="waves"&&g(ze,20)})}ft(()=>Xa(a,1,mi(M(r)))),O(e,a),G()}const yd=50,wd=1e4,qd=.5,Sd=12,Md=.01,kd=.25,Gr={denoiseAlgorithm:"standard",pauseAggressiveness:"normal",speedStep:.05,trimStepMs:100,volumeStepDb:3};function Ed(){return window.__aqeSplitButtonStates??(window.__aqeSplitButtonStates={}),window.__aqeSplitButtonStates}function Ad(){var e;return{...Gr,...(e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.splitButtonDefaults}}function Za(e){return Number.isFinite(e)?Math.max(yd,Math.min(wd,Math.round(e))):Gr.trimStepMs}function Ja(e){return Number.isFinite(e)?Math.max(qd,Math.min(Sd,Math.round(e*10)/10)):Gr.volumeStepDb}function za(e){return Number.isFinite(e)?Math.max(Md,Math.min(kd,Math.round(e*100)/100)):Gr.speedStep}function Ei(e){const t=Za(e);if(t<1e3)return`${t} ms`;const n=t/1e3;return`${Number.isInteger(n)?n.toFixed(0):n.toFixed(1)} s`}function Ai(e){const t=Ja(e);return`${Number.isInteger(t)?t.toFixed(0):t.toFixed(1)} dB`}function Pi(e,t){const n=za(e);return`x${(t==="aqe:slower"?1-n:1+n).toFixed(2)}`}function vn(e){const t=Ad(),n=Za(t.trimStepMs),r=Ja(t.volumeStepDb),a=za(t.speedStep),o=Ed(),s=o[e];if(s)return!s.trimEdited&&s.defaultTrimStepMs!==n&&(s.defaultTrimStepMs=n,s.trimStepMs=n),!s.volumeEdited&&s.defaultVolumeStepDb!==r&&(s.defaultVolumeStepDb=r,s.volumeStepDb=r),!s.speedEdited&&s.defaultSpeedStep!==a&&(s.defaultSpeedStep=a,s.speedStep=a),s;const i={defaultTrimStepMs:n,defaultVolumeStepDb:r,defaultSpeedStep:a,speedEdited:!1,speedStep:a,trimEdited:!1,trimStepMs:n,volumeEdited:!1,volumeStepDb:r};return o[e]=i,i}function Pd(e,t){const n=vn(e);return n.trimEdited=!0,n.trimStepMs=Za(t),n}function Fd(e,t){const n=vn(e);return n.volumeEdited=!0,n.volumeStepDb=Ja(t),n}function Nd(e,t){const n=vn(e);return n.speedEdited=!0,n.speedStep=za(t),n}function Cd(e,t){return{command:e,fieldOrd:t,overrides:{trimStepMs:vn(t).trimStepMs}}}function xd(e,t){const n=vn(t);return e==="aqe:volume-up"||e==="aqe:volume-down"?{command:e,fieldOrd:t,overrides:{volumeStepDb:n.volumeStepDb}}:e==="aqe:faster"||e==="aqe:slower"?{command:e,fieldOrd:t,overrides:{speedStep:n.speedStep}}:Cd(e,t)}var Td=Ke('<button type="button" class="aqe-button aqe-split-preset"> </button>'),Rd=Ke('<div class="aqe-split-popover"><div class="aqe-split-popover-header"><strong> </strong> <span> </span></div> <input type="range"/> <div class="aqe-split-range-labels"><span> </span> <span> </span></div> <div class="aqe-split-presets"></div></div>'),Dd=Ke('<span class="aqe-split-button"><button type="button" class="aqe-button aqe-split-primary" data-aqe-button-state="default"><!> <span class="aqe-button-label"> </span></button> <button type="button" class="aqe-button aqe-icon-only aqe-split-menu-button"><!> <span class="aqe-button-label">Options</span></button> <!></span>');function Od(e,t){V(t,!0);let n,r=Ne(!1),a=Ne(100),o=Ne(3),s=Ne(.05);function i(){return Cn[t.button.command]}function l(){me(r,!1)}function f(N){N.preventDefault(),N.stopPropagation(),me(r,!M(r))}function c(N){me(a,Pd(t.target.ord,N).trimStepMs,!0)}function u(N){me(o,Fd(t.target.ord,N).volumeStepDb,!0)}function d(N){me(s,Nd(t.target.ord,N).speedStep,!0)}function _(){l(),la(t.button.command,t.target.node,t.target.ord,xd(t.button.command,t.target.ord))}function m(){return t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"?Ai(M(o)):t.button.command==="aqe:faster"||t.button.command==="aqe:slower"?Pi(M(s),t.button.command):Ei(M(a))}function w(){return t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"?M(o):t.button.command==="aqe:faster"||t.button.command==="aqe:slower"?M(s):M(a)}function h(){return t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"?{min:"0.5",max:"12",step:"0.5",labels:["0.5 dB","12 dB"],presets:[1,3,6,9]}:t.button.command==="aqe:faster"||t.button.command==="aqe:slower"?{min:"0.01",max:"0.25",step:"0.01",labels:["x1.01","x1.25"],presets:[.03,.05,.1,.2]}:{min:"50",max:"10000",step:"50",labels:["50 ms","10 s"],presets:[100,200,500,1e3]}}function v(N){if(t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"){u(N);return}if(t.button.command==="aqe:faster"||t.button.command==="aqe:slower"){d(N);return}c(N)}function F(N){!M(r)||!n||N.target instanceof Node&&n.contains(N.target)||l()}function y(N){N.key==="Escape"&&l()}ki(()=>{const N=vn(t.target.ord);return me(a,N.trimStepMs,!0),me(o,N.volumeStepDb,!0),me(s,N.speedStep,!0),document.addEventListener("mousedown",F,!0),document.addEventListener("keydown",y,!0),()=>{document.removeEventListener("mousedown",F,!0),document.removeEventListener("keydown",y,!0)}});var E=Dd(),A=S(E),H=S(A);$(H,{get icon(){return t.button.icon}});var D=P(H,2),ye=S(D),I=P(A,2),ze=S(I);$(ze,{icon:"chevron-down"});var g=P(I,2);{var Kt=N=>{var et=Rd(),Pt=S(et),Yt=S(Pt),En=S(Yt),Qt=P(Yt,2),Ae=S(Qt),De=P(Pt,2),lr=P(De,2),jr=S(lr),oo=S(jr),$r=P(jr,2),so=S($r),io=P(lr,2);Br(io,21,()=>h().presets,di,(Ft,tt)=>{var ht=Td(),An=S(ht);ft((ur,cr,Pn)=>{q(ht,"data-testid",ur),q(ht,"aria-pressed",cr),kt(An,Pn)},[()=>`aqe-split-${t.target.ord}-${i()}-preset-${M(tt)}`,()=>w()===M(tt)?"true":"false",()=>t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"?Ai(M(tt)):t.button.command==="aqe:faster"||t.button.command==="aqe:slower"?Pi(M(tt),t.button.command):Ei(M(tt))]),de("click",ht,()=>v(M(tt))),O(Ft,ht)}),ft((Ft,tt,ht,An,ur,cr,Pn,lo,uo)=>{q(et,"data-testid",Ft),kt(En,t.button.label),kt(Ae,tt),q(De,"data-testid",ht),q(De,"min",An),q(De,"max",ur),q(De,"step",cr),Bf(De,Pn),kt(oo,lo),kt(so,uo)},[()=>`aqe-split-${t.target.ord}-${i()}-popover`,m,()=>`aqe-split-${t.target.ord}-${i()}-slider`,()=>h().min,()=>h().max,()=>h().step,w,()=>h().labels[0],()=>h().labels[1]]),de("input",De,Ft=>v(Number(Ft.currentTarget.value))),O(N,et)};mn(g,N=>{M(r)&&N(Kt)})}Hf(E,N=>n=N,()=>n),ft((N,et)=>{q(A,"data-aqe-command",t.button.command),q(A,"data-testid",N),q(A,"title",t.button.title),q(A,"aria-label",t.button.title),kt(ye,t.button.label),q(I,"data-testid",et),q(I,"title",`${t.button.title} amount`),q(I,"aria-label",`${t.button.title} amount`),q(I,"aria-expanded",M(r)?"true":"false")},[()=>`aqe-button-${t.target.ord}-${i()}`,()=>`aqe-split-${t.target.ord}-${i()}-menu`]),de("mousedown",A,N=>N.preventDefault()),de("click",A,_),de("mousedown",I,N=>N.preventDefault()),de("click",I,f),O(e,E),G()}Va(["mousedown","click","input"]);function Fi(){return document.body.dataset.aqeBusy==="true"}function Ni(e,t,n){if(Fi())return;const r=B(n);if(!r)return;const a=Ho(r,e);Ln(r),a&&(typeof t.focus=="function"&&t.focus(),vt(r,{clearAudio:!0}),il(a),window.__aqeActiveField=n,he.info("region delete request queued",{ord:n,sourceFilename:a.sourceFilename,selectionStartMs:a.selectionStartMs,selectionEndMs:a.selectionEndMs,durationMs:a.durationMs,trigger:e,playbackActive:a.playbackActive}),nn(n,!0,bo("aqe:delete-selection")),en(n,"aqe:delete-selection"))}function Ld(e,t){if(e.key!=="Backspace")return;const n=B(t);if(!(!n||document.activeElement!==n||Fi())){if(!Ho(n,"backspace")){Ln(n);return}e.preventDefault(),Ni("backspace",n,t)}}var Id=Ke('<button type="button"><!> <!> <span class="aqe-button-label"> </span></button>'),Bd=Ke('<button type="button" class="aqe-button aqe-icon-only aqe-repeat-button" title="Repeat selected region, or the whole graph when no region is selected." aria-label="Repeat playback"><!> <span class="aqe-button-label">Repeat</span></button>'),Vd=Ke('<button type="button" class="aqe-button aqe-menu-item" data-aqe-button-state="default" role="menuitem"><!> <span class="aqe-button-label"> </span></button>'),Gd=Ke('<details class="aqe-menu"><summary class="aqe-button aqe-menu-summary" title="Denoise audio" aria-label="Denoise audio"><!> <span class="aqe-button-label">Denoise</span> <!></summary> <div class="aqe-menu-items" role="menu"></div></details>'),Hd=Ke("<!> <!> <!>",1),Wd=Ke('<div class="aqe-controls"><!> <button type="button" class="aqe-button aqe-delete-region-button" data-aqe-command="aqe:delete-selection" data-aqe-button-state="default" title="Delete selected region" aria-label="Delete selected region" hidden=""><!> <span class="aqe-button-label">Delete Region</span></button> <span class="aqe-status"></span> <details class="aqe-help"><summary class="aqe-help-summary" title="Show editor help"><!> <span>Help</span></summary> <div class="aqe-help-body"><section class="aqe-help-section"><h4 class="aqe-help-title">Graph and regions</h4> <ul class="aqe-help-list"><li><kbd>Shift</kbd>-drag on the graph to select a region.</li> <li>Play uses the selected region when one is active; Repeat loops the selected region, or the full graph otherwise.</li> <li>Delete Region removes only the selected region. Backspace does the same when the graph is focused.</li> <li>In the graph, grey is loudness and lines are pitch of the voice.</li></ul></section> <section class="aqe-help-section"><h4 class="aqe-help-title">Buttons</h4> <div class="aqe-help-grid"><span class="aqe-help-item"><span class="aqe-help-command"><!><span>Play</span></span> <span>Start or pause audio.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Graph</span></span> <span>Show pitch and loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Folder</span></span> <span>Open the current audio file.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-L</span></span> <span>Trim 100 ms from the left.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-R</span></span> <span>Trim 100 ms from the right.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Shorten Pauses</span></span> <span>Speed up long internal pauses.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Denoise</span></span> <span>Use Standard or RNNoise cleanup.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Slower</span></span> <span>Decrease speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Faster</span></span> <span>Increase speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume -</span></span> <span>Decrease loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume +</span></span> <span>Increase loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Undo</span></span> <span>Restore the previous edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Redo</span></span> <span>Restore the undone edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Delete Region</span></span> <span>Remove the selected graph region.</span></span></div></section> <p class="aqe-help-note">Every edit creates a new media file and updates the field to point at it. The original file remains in your media collection.</p></div></details> <div class="aqe-visualizer" data-anchor-ms="0" data-cursor-ms="0" data-progress-ms="0" data-graph-active="false" data-graph-busy="false" data-has-track="false" data-playback-state="stopped" data-playback-engine="" data-playback-start-ms="0" data-playback-end-ms="0" data-playback-region-mode="full" data-resume-requires-restart="false" data-selection-active="false" data-selection-start-ms="" data-selection-end-ms="" data-selection-draft-active="false" data-selection-draft-start-ms="" data-selection-draft-end-ms="" role="button" aria-label="Audio graph" tabindex="0" hidden=""><audio class="aqe-audio-clock" preload="metadata" hidden=""></audio> <svg class="aqe-visualizer-svg" preserveAspectRatio="xMinYMin meet" role="img" aria-label="Audio pitch and intensity visualization"><rect class="aqe-selection" width="0" visibility="hidden"></rect><path class="aqe-intensity" d=""></path><g class="aqe-pitch"></g><g class="aqe-labels"></g><g class="aqe-x-axis"></g><line class="aqe-selection-edge aqe-selection-start" visibility="hidden"></line><line class="aqe-selection-edge aqe-selection-end" visibility="hidden"></line><line class="aqe-cursor"></line></svg> <div class="aqe-visualizer-meta"><span class="aqe-spinner" hidden="" aria-hidden="true"></span> <span class="aqe-cursor-label">0 ms</span> <span class="aqe-visualizer-status"></span></div></div></div>');function jd(e,t){var Ki;V(t,!0);const n=((Ki=window.__AQE_EDITOR_CONFIG__)==null?void 0:Ki.repeatPlaybackByDefault)===!0;function r(ne){const Ur=ne.currentTarget.ariaPressed!=="true";vu(t.target.ord,Ur)}function a(ne){return["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:volume-down","aqe:volume-up"].includes(ne)}ki(()=>{const ne=B(t.target.ord);ne&&(fu(ne),wu(ne),mu(ne))});var o=Wd(),s=S(o);Br(s,17,()=>W,ne=>ne.command,(ne,pe)=>{var Ur=Hd(),Yi=X(Ur);{var vp=we=>{Od(we,{get button(){return M(pe)},get target(){return t.target}})},gp=Dr(()=>a(M(pe).command)),bp=we=>{var J=Id();let Zt;var Jt=S(J);$(Jt,{className:"aqe-button-icon-default",get icon(){return M(pe).icon}});var Xr=P(Jt,2);{var co=_e=>{$(_e,{className:"aqe-button-icon-active",get icon(){return M(pe).activeIcon}})};mn(Xr,_e=>{M(pe).activeIcon&&_e(co)})}var mr=P(Xr,2),mt=S(mr);ft(_e=>{Zt=Xa(J,1,"aqe-button",null,Zt,{"aqe-icon-only":M(pe).iconOnly===!0}),q(J,"data-aqe-command",M(pe).command),q(J,"data-aqe-button-state",M(pe).command==="aqe:play"?"play":M(pe).command==="aqe:analyze"?"graph":"default"),q(J,"data-testid",_e),q(J,"title",M(pe).title),q(J,"aria-label",M(pe).title),kt(mt,M(pe).label)},[()=>Qr(t.target.ord,M(pe).command)]),de("mousedown",J,_e=>_e.preventDefault()),de("click",J,()=>la(M(pe).command,t.target.node,t.target.ord)),O(we,J)};mn(Yi,we=>{M(gp)?we(vp):we(bp,!1)})}var Qi=P(Yi,2);{var yp=we=>{var J=Bd(),Zt=S(J);$(Zt,{icon:"repeat-2"}),ft(()=>{q(J,"data-aqe-button-state",n?"active":"default"),q(J,"data-testid",`aqe-repeat-${t.target.ord}`),q(J,"aria-pressed",n?"true":"false")}),de("mousedown",J,Jt=>Jt.preventDefault()),de("click",J,r),O(we,J)};mn(Qi,we=>{M(pe).command==="aqe:play"&&we(yp)})}var wp=P(Qi,2);{var qp=we=>{var J=Gd(),Zt=S(J),Jt=S(Zt);$(Jt,{icon:"sparkles"});var Xr=P(Jt,4);$(Xr,{className:"aqe-menu-chevron",icon:"chevron-down"});var co=P(Zt,2);Br(co,21,()=>j,mr=>mr.command,(mr,mt)=>{var _e=Vd(),Zi=S(_e);$(Zi,{get icon(){return M(mt).icon}});var Sp=P(Zi,2),Mp=S(Sp);ft(fo=>{q(_e,"data-aqe-command",M(mt).command),q(_e,"data-testid",fo),q(_e,"title",M(mt).title),q(_e,"aria-label",M(mt).title),kt(Mp,M(mt).label)},[()=>Qr(t.target.ord,M(mt).command)]),de("mousedown",_e,fo=>fo.preventDefault()),de("click",_e,()=>la(M(mt).command,t.target.node,t.target.ord)),O(mr,_e)}),ft(()=>q(J,"data-testid",`aqe-denoise-menu-${t.target.ord}`)),O(we,J)};mn(wp,we=>{M(pe).command==="aqe:remove-pauses"&&we(qp)})}O(ne,Ur)});var i=P(s,2),l=S(i);$(l,{icon:"trash-2"});var f=P(i,2),c=P(f,2),u=S(c),d=S(u);$(d,{icon:"circle-help"});var _=P(u,2),m=P(S(_),2),w=P(S(m),2),h=S(w),v=S(h),F=S(v);$(F,{icon:"play"});var y=P(h,2),E=S(y),A=S(E);$(A,{icon:"chart-line"});var H=P(y,2),D=S(H),ye=S(D);$(ye,{icon:"folder-open"});var I=P(H,2),ze=S(I),g=S(ze);$(g,{icon:"scissors"});var Kt=P(I,2),N=S(Kt),et=S(N);$(et,{icon:"scissors"});var Pt=P(Kt,2),Yt=S(Pt),En=S(Yt);$(En,{icon:"timer-reset"});var Qt=P(Pt,2),Ae=S(Qt),De=S(Ae);$(De,{icon:"sparkles"});var lr=P(Qt,2),jr=S(lr),oo=S(jr);$(oo,{icon:"rewind"});var $r=P(lr,2),so=S($r),io=S(so);$(io,{icon:"fast-forward"});var Ft=P($r,2),tt=S(Ft),ht=S(tt);$(ht,{icon:"volume-1"});var An=P(Ft,2),ur=S(An),cr=S(ur);$(cr,{icon:"volume-2"});var Pn=P(An,2),lo=S(Pn),uo=S(lo);$(uo,{icon:"undo-2"});var Gi=P(Pn,2),cp=S(Gi),fp=S(cp);$(fp,{icon:"redo-2"});var dp=P(Gi,2),pp=S(dp),hp=S(pp);$(hp,{icon:"trash-2"});var fr=P(c,2),Hi=S(fr),dr=P(Hi,2),pr=S(dr),Wi=P(pr),ji=P(Wi),$i=P(ji,2),Fn=P($i),Nn=P(Fn),hr=P(Nn),mp=P(dr,2),Ui=S(mp),Xi=P(Ui,2),_p=P(Xi,2);ft(ne=>{q(o,"data-aqe-field-ord",t.target.ord),q(o,"data-aqe-source-filename",t.target.sourceFilename),q(o,"data-testid",`aqe-controls-${t.target.ord}`),q(i,"data-testid",ne),q(f,"data-testid",`aqe-status-${t.target.ord}`),q(c,"data-testid",`aqe-help-${t.target.ord}`),q(fr,"data-aqe-field-ord",t.target.ord),q(fr,"data-repeat-enabled",n?"true":"false"),q(fr,"data-testid",`aqe-graph-${t.target.ord}`),q(Hi,"data-testid",`aqe-audio-clock-${t.target.ord}`),q(dr,"data-testid",`aqe-graph-svg-${t.target.ord}`),q(dr,"viewBox",`0 0 ${k.width} ${k.height}`),q(pr,"data-testid",`aqe-selection-${t.target.ord}`),q(pr,"x",k.left),q(pr,"y",k.top),q(pr,"height",k.height-k.top-k.bottom),q(Wi,"data-testid",`aqe-intensity-${t.target.ord}`),q(ji,"data-testid",`aqe-pitch-${t.target.ord}`),q($i,"data-testid",`aqe-x-axis-${t.target.ord}`),q(Fn,"data-testid",`aqe-selection-start-${t.target.ord}`),q(Fn,"x1",k.left),q(Fn,"x2",k.left),q(Fn,"y1",k.top),q(Fn,"y2",k.height-k.bottom),q(Nn,"data-testid",`aqe-selection-end-${t.target.ord}`),q(Nn,"x1",k.left),q(Nn,"x2",k.left),q(Nn,"y1",k.top),q(Nn,"y2",k.height-k.bottom),q(hr,"data-testid",`aqe-cursor-${t.target.ord}`),q(hr,"x1",k.left),q(hr,"x2",k.left),q(hr,"y1",k.top),q(hr,"y2",k.height-k.bottom),q(Ui,"data-testid",`aqe-graph-spinner-${t.target.ord}`),q(Xi,"data-testid",`aqe-progress-label-${t.target.ord}`),q(_p,"data-testid",`aqe-graph-status-${t.target.ord}`)},[()=>Qr(t.target.ord,"aqe:delete-selection")]),de("mousedown",i,ne=>ne.preventDefault()),de("click",i,()=>Ni("button",t.target.node,t.target.ord)),de("keydown",fr,ne=>Ld(ne,t.target.ord)),de("pointerdown",dr,ne=>ku(ne,t.target.ord)),O(e,o),G()}Va(["mousedown","click","keydown","pointerdown"]);const gn=new Map;function $d(e){const t=gn.get(e.ord);if(t){if(document.body.contains(t.host)||Ci(e,t.host),eo(e.ord,t.host),!e.sourceFilename||t.sourceFilename===e.sourceFilename)return t;const o=B(e.ord);if((o==null?void 0:o.dataset.graphBusy)==="true"||(o==null?void 0:o.dataset.hasTrack)==="true"){const s=o.dataset.sourceFilename||e.sourceFilename;t.sourceFilename=s;const i=document.querySelector(`.aqe-controls[data-aqe-field-ord="${e.ord}"]`);return i&&(i.dataset.aqeSourceFilename=s),eo(e.ord,t.host),t}}Ud(e.ord);const n=document.createElement("div");n.className="aqe-mount-host",Ci(e,n);const a={component:Sf(jd,{target:n,props:{target:e}}),host:n,ord:e.ord,sourceFilename:e.sourceFilename};return gn.set(e.ord,a),eo(e.ord,n),a}function Ud(e){const t=gn.get(e);t&&(fi(t.component),t.host.remove(),gn.delete(e)),document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>n.remove())}function Xd(){for(const e of gn.values())fi(e.component),e.host.remove();gn.clear(),Kd()}function Ci(e,t){const n=e.node.closest(".field-container")||e.node.closest(".field")||e.node.parentElement||e.node;n.parentElement?n.after(t):e.node.after(t)}function eo(e,t){document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>{t.contains(n)||n.remove()}),document.querySelectorAll(".aqe-mount-host").forEach(n=>{n!==t&&!n.querySelector(".aqe-controls")&&n.remove()})}function Kd(){document.querySelectorAll(".aqe-mount-host").forEach(e=>e.remove()),document.querySelectorAll(".aqe-controls").forEach(e=>e.remove())}function Yd(){window.__aqeGraphStateForTest=zd,window.__aqeInstallAudioPlaybackTestDriverForTest=Qd,window.__aqeSetCursorByClientXForTest=Jd,window.__aqeSetCursorForTest=Zd}function Qd(e){const t=B(e),n=Oe(t);return!t||!n?!1:(n.__aqeTestDriverInstalled=!0,n.pause=function(){n.__aqeTestPlaying=!1,n.__aqeTestFrame&&(window.cancelAnimationFrame(n.__aqeTestFrame),n.__aqeTestFrame=null)},n.play=function(){n.__aqeTestPlaying=!0,n.__aqeTestLastNow=performance.now();const a=()=>{if(!n.__aqeTestPlaying)return;const o=performance.now(),s=Number(t.dataset.durationMs||"0")/1e3,i=Math.max(0,(o-Number(n.__aqeTestLastNow||o))/1e3);if(n.__aqeTestLastNow=o,n.currentTime=Math.min(s,(Number(n.currentTime)||0)+i),s&&n.currentTime>=s){n.__aqeTestPlaying=!1,n.dispatchEvent(new Event("ended"));return}n.__aqeTestFrame=window.requestAnimationFrame(a)};return n.__aqeTestFrame=window.requestAnimationFrame(a),Promise.resolve()},!0)}function Zd(e,t,n){const r=B(e);return r?(r.hidden=!1,r.dataset.graphActive="true",Ct(r,t,!!n),!0):!1}function Jd(e,t,n){var i;const r=B(e),a=(r==null?void 0:r.querySelector(".aqe-visualizer-svg"))??null;if(!r||!a)return null;const o=Number(r.dataset.durationMs||"0"),s=Dn({clientX:t},a,o);return Ct(r,s,!!n),{cursorMs:Number(r.dataset.cursorMs||"0"),cursorX:Number(((i=r.querySelector(".aqe-cursor"))==null?void 0:i.getAttribute("x1"))||"0"),bounds:Oo(a)}}function zd(e){var f,c,u,d,_;const t=B(e),n=wo(e),r=qo(e),a=((f=rt(e))==null?void 0:f.querySelector(".aqe-delete-region-button"))??null;if(!t)return null;const o=_r().flatMap(m=>Array.from(m.querySelectorAll(".aqe-button-icon svg"))),s=Oe(t),i=Zo(t),l=Jo(t);return{active:t.dataset.graphActive==="true",busy:t.dataset.graphBusy==="true",hidden:!!t.hidden,hasTrack:t.dataset.hasTrack==="true",durationMs:Number(t.dataset.durationMs||"0"),anchorMs:Number(t.dataset.anchorMs||"0"),cursorMs:Number(t.dataset.cursorMs||"0"),progressMs:Number(t.dataset.progressMs||"0"),sourceFilename:t.dataset.sourceFilename||"",graphButtonLabel:xi(n),graphButtonState:(n==null?void 0:n.dataset.aqeButtonState)||"",playButtonLabel:xi(r),playButtonState:(r==null?void 0:r.dataset.aqeButtonState)||"",playbackState:ep(t),selectionActive:i!==null,selectionStartMs:(i==null?void 0:i.startMs)??null,selectionEndMs:(i==null?void 0:i.endMs)??null,selectionDraftActive:l!==null,selectionDraftStartMs:(l==null?void 0:l.startMs)??null,selectionDraftEndMs:(l==null?void 0:l.endMs)??null,repeatEnabled:t.dataset.repeatEnabled==="true",repeatControlDisabled:!!((c=So(e))!=null&&c.disabled),regionDeleteButtonDisabled:!!(a!=null&&a.disabled),regionDeleteButtonHidden:a?!!a.hidden:!0,playbackStartMs:Number(t.dataset.playbackStartMs||"0"),playbackEndMs:Number(t.dataset.playbackEndMs||"0"),playbackRegionMode:t.dataset.playbackRegionMode==="selection"?"selection":"full",resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true",audioClockSrc:s&&s.getAttribute("src")||"",audioClockCurrentMs:s?Math.round((Number(s.currentTime)||0)*1e3):0,audioClockReady:!!(s&&t.__aqeAudioClockAvailable),audioClockFallback:!!t.__aqeAudioClockFallback,audioClockMuted:!!(s&&s.muted),audioPlaybackTestDriver:!!(s&&s.__aqeTestDriverInstalled),playbackEngine:Vn(t),progressClockMode:tp(t),xAxisLabels:Array.from(t.querySelectorAll(".aqe-x-label")).map(m=>m.textContent||""),pitchPaths:t.querySelectorAll(".aqe-pitch-path").length,intensity:((u=t.querySelector(".aqe-intensity"))==null?void 0:u.getAttribute("d"))||"",cursorX:Number(((d=t.querySelector(".aqe-cursor"))==null?void 0:d.getAttribute("x1"))||"0"),spinnerVisible:t.querySelector(".aqe-spinner")?!((_=t.querySelector(".aqe-spinner"))!=null&&_.hidden):!1,allButtonsDisabled:_r().every(m=>m.disabled),anyButtonDisabled:_r().some(m=>m.disabled),buttonIconCount:o.length,buttonIconStrokeValues:o.map(m=>m.getAttribute("stroke")||getComputedStyle(m).stroke||"")}}function ep(e){const t=e.dataset.playbackState;return ta(t)?t:"stopped"}function tp(e){const t=e.dataset.progressClockMode;return t==="audio"||t==="manual"||t==="stopped"?t:"stopped"}function xi(e){var t;return((t=e==null?void 0:e.querySelector(".aqe-button-label"))==null?void 0:t.textContent)||(e==null?void 0:e.textContent)||""}function np(){window.__aqeSetBusy=nn,window.__aqeSetStatus=Qo,window.__aqeSetVisualizer=Au,window.__aqeSetVisualizerStatus=Pu,window.__aqeResetGraphAfterEdit=Eu,window.__aqeSetPlaybackState=Tu,window.__aqeGetPlaybackRequest=Ru,window.__aqeStopEditorPlayback=Du,window.__aqeGetCursorMs=Ou,window.__aqeGetCursorIntent=Lu,window.__aqePrepareForNewNote=rs,window.__aqePopFrontendLog=rl,window.__aqePopPendingGraphAnalysisRequest=sl,window.__aqePopPendingRegionDeleteRequest=ll,Yd()}const rp=/\[sound:([^\]]+)\]/i,ap=/\.(aac|flac|m4a|mp3|oga|ogg|opus|wav|webm)$/i;let rr=[];function op(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){Ti(),window.__AQE_EDITOR_CONFIG__=e,np(),rs(),wl(),window.__aqeEditorDispose=Ti,he.info("editor runtime initialized",{audioFieldIndices:e.audioFieldIndices,showGraphByDefault:e.showGraphByDefault===!0});const t=()=>sp(e);window.__aqeScan=t,no(t,0),no(t,250),no(t,1e3)}function Ti(){rr.forEach(e=>window.clearTimeout(e)),rr=[],Xd()}function sp(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){if(e.audioFieldIndices.length){const r=lp(e.audioFieldIndices,e.audioFieldSources);r.forEach(a=>Ri(a)),he.debug("scan mounted explicit fields",{count:r.length}),pa(),Di(e,r);return}const t=[];let n=0;ip().forEach((r,a)=>{const o=to(r);if(!o)return;const s={node:r,ord:up(r,a),sourceFilename:o};Ri(s),t.push(s),n+=1}),he.debug("scan mounted detected fields",{count:n}),pa(),Di(e,t)}function ip(){const e=Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]')),t=new Set;return e.filter(n=>t.has(n)?!1:(t.add(n),!!(n.textContent||n.innerHTML)))}function lp(e,t={}){return e.map(n=>{const r=document.querySelector(`.field-container[data-index="${n}"]`);if(!r)return null;const a=r.querySelector('[contenteditable="true"]')||r,o=to(a)||to(r)||t[n]||"";return{ord:n,node:a,sourceFilename:o}}).filter(n=>n!==null)}function up(e,t){const n=["data-field-ord","data-ord","data-index"];for(const a of n){const o=e.getAttribute(a);if(o!==null&&/^\d+$/.test(o))return Number(o)}const r=/(\d+)/.exec(String(e.id||""));return r?Number(r[1]):t}function to(e){const t=e.innerHTML||e.textContent||"",n=rp.exec(t),r=n==null?void 0:n[1];return r&&ap.test(r)?r:""}function Ri(e){$d(e)}function Di(e,t){e.showGraphByDefault&&ql(t.map(({ord:n,sourceFilename:r})=>({ord:n,sourceFilename:r})),{anyBusy:()=>document.body.dataset.aqeBusy==="true",requestDefaultGraph:ts})}function no(e,t){const n=window.setTimeout(()=>{rr=rr.filter(r=>r!==n),e()},t);rr.push(n)}op()})();
