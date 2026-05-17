var ef=Object.defineProperty;var vs=T=>{throw TypeError(T)};var tf=(T,R,I)=>R in T?ef(T,R,{enumerable:!0,configurable:!0,writable:!0,value:I}):T[R]=I;var Oe=(T,R,I)=>tf(T,typeof R!="symbol"?R+"":R,I),Zr=(T,R,I)=>R.has(T)||vs("Cannot "+I);var h=(T,R,I)=>(Zr(T,R,"read from private field"),I?I.call(T):R.get(T)),P=(T,R,I)=>R.has(T)?vs("Cannot add the same private member more than once"):R instanceof WeakSet?R.add(T):R.set(T,I),A=(T,R,I,qn)=>(Zr(T,R,"write to private field"),qn?qn.call(T,I):R.set(T,I),I),G=(T,R,I)=>(Zr(T,R,"access private method"),I);(function(){"use strict";var us,cs,fs,jt,Ht,Mt,Wt,wn,Mn,kt,He,Gt,fe,Jr,zr,ea,ms,be,Kr,Te,St,ie,Re,de,Ce,We,qt,it,Ut,Xt,Yt,Le,Wn,j,nf,rf,af,ta,Un,Xn,na,ds,Pe,$e,he,At,kn,Sn,Gn,hs;const T=[{activeIcon:"pause",command:"aqe:play",icon:"play",label:"Play",title:"Play or pause current audio"},{activeIcon:"refresh-cw",command:"aqe:analyze",icon:"chart-line",label:"Graph",title:"Analyze and show pitch/intensity graph"},{command:"aqe:show-file",icon:"folder-open",label:"Folder",title:"Show current audio file in folder"},{command:"aqe:trim-left",icon:"scissors",label:"-L",title:"Trim 100 ms from left"},{command:"aqe:trim-right",icon:"scissors",label:"-R",title:"Trim 100 ms from right"},{command:"aqe:remove-pauses",icon:"timer-reset",label:"Shorten Pauses",title:"Speed up long internal pauses"},{command:"aqe:sidon",icon:"wand-sparkles",label:"Sidon",title:"Restore speech with Sidon"},{command:"aqe:mp-senet",icon:"sparkles",label:"MP-SENet",title:"Denoise speech with MP-SENet"},{command:"aqe:remove-noise",icon:"volume-x",label:"Remove noise",title:"Reduce background noise with DeepFilterNet"},{command:"aqe:slower",icon:"rewind",label:"Slower",title:"Decrease speed"},{command:"aqe:faster",icon:"fast-forward",label:"Faster",title:"Increase speed"},{command:"aqe:volume-down",icon:"volume-1",label:"Volume -",title:"Decrease volume"},{command:"aqe:volume-up",icon:"volume-2",label:"Volume +",title:"Increase volume"},{command:"aqe:undo",icon:"undo-2",label:"Undo",title:"Restore the previous generated audio reference"}],R=new Set(["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:remove-pauses","aqe:remove-noise","aqe:sidon","aqe:mp-senet","aqe:volume-down","aqe:volume-up"]),I={"aqe:play":"play","aqe:analyze":"graph","aqe:show-file":"show-file","aqe:trim-left":"trim-left","aqe:trim-right":"trim-right","aqe:remove-pauses":"remove-pauses","aqe:remove-noise":"remove-noise","aqe:sidon":"sidon","aqe:mp-senet":"mp-senet","aqe:slower":"slower","aqe:faster":"faster","aqe:volume-down":"volume-down","aqe:volume-up":"volume-up","aqe:undo":"undo"};function qn(e,t){return`aqe-button-${e}-${I[t]}`}function gs(e){return e==="aqe:remove-noise"?"Removing noise...":e==="aqe:sidon"?"Restoring speech...":e==="aqe:mp-senet"?"Denoising with MP-SENet...":"Processing..."}function Et(e){return document.querySelector(`.aqe-controls[data-aqe-field-ord="${e}"]`)}function $(e){return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${e}"]`)}function ra(e,t){const n=Et(e);return(n==null?void 0:n.querySelector(`[data-aqe-command="${t}"]`))??null}function aa(e){return ra(e,"aqe:analyze")}function oa(e){return ra(e,"aqe:play")}function sa(e){const t=Et(e);return(t==null?void 0:t.querySelector(".aqe-repeat-checkbox"))??null}function An(){return Array.from(document.querySelectorAll(".aqe-button"))}function ys(){return Array.from(document.querySelectorAll(".aqe-repeat-checkbox"))}function ia(){return Array.from(document.querySelectorAll(".aqe-visualizer"))}const la=[];function Yn(e){globalThis.pycmd!==void 0&&globalThis.pycmd(e)}function Kt(e,t){Yn(`focus:${e}`),Yn(t)}function bs(e){la.push(e),Yn("aqe:frontend-log")}function ws(){return la.shift()??null}function Ms(e){window.__aqePendingPlaybackRequest=e,window.__aqeLastPlaybackRequest=e}function ks(){if(!window.__aqePendingPlaybackRequest)return null;const e=window.__aqePendingPlaybackRequest;return window.__aqePendingPlaybackRequest=null,e}function Ss(e){window.__aqeLastCursorIntent=e}function qs(e){return encodeURIComponent(e||"").replaceAll("%2F","/")}function we(e){return(e==null?void 0:e.querySelector(".aqe-audio-clock"))??null}function Kn(e){e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!1,e.__aqeAudioClockLastSeekedMs=0,e.dataset.progressClockMode="stopped"}function Qt(e){const t=we(e);if(!(!t||typeof t.pause!="function"))try{t.pause()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Qn(e){const t=we(e);if(Kn(e),!!t){Qt(e),t.removeAttribute("src"),t.src="";try{t.load()}catch{e.__aqeAudioClockFallback=!0}}}function As(e,t){const n=we(e);if(Kn(e),!n){e.__aqeAudioClockFallback=!0;return}if(Qt(e),!t){Qn(e);return}n.setAttribute("src",qs(t));try{n.load()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Es(e,t={}){const n=we(e);!n||n.__aqeClockHandlersInstalled||(n.__aqeClockHandlersInstalled=!0,n.addEventListener("loadedmetadata",()=>{n.getAttribute("src")&&(e.__aqeAudioClockAvailable=!0,e.__aqeAudioClockFallback=!1)}),n.addEventListener("error",()=>{var r;e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,e.dataset.playbackState==="playing"&&e.dataset.progressClockMode==="audio"&&((r=t.onErrorDuringPlayback)==null||r.call(t))}),n.addEventListener("ended",()=>{var r;e.dataset.playbackState==="playing"&&((r=t.onEndedDuringPlayback)==null||r.call(t))}),n.addEventListener("seeked",()=>{e.__aqeAudioClockLastSeekedMs=Math.round((Number(n.currentTime)||0)*1e3)}))}function En(e){const t=we(e);return!t||!(e!=null&&e.__aqeAudioClockAvailable)||!t.getAttribute("src")?!1:t.readyState===void 0||t.readyState>=1}function Cn(e,t,n){const r=we(e);if(!r)return!1;const a=Math.max(0,Math.min(Number(t)||0,n||0));try{return r.currentTime=a/1e3,e.__aqeAudioClockLastSeekedMs=Math.round(a),!0}catch{return e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,!1}}var Zt=(e=>(e.Debug="debug",e.Error="error",e.Info="info",e.Unknown="unknown",e.Warn="warn",e))(Zt||{});function Cs(e){return e==="error"?console.error:console.warn}function Ps(e){return e==="debug"?Zt.Debug:e==="warn"?Zt.Warn:e==="error"?Zt.Error:Zt.Info}function Zn(e,t=0){const n=Ns(e);return n!==void 0?n:Array.isArray(e)?Fs(e,t):e!==null&&typeof e=="object"?xs(e,t):Ts(e)}function Ns(e){if(e===void 0)return"[undefined]";if(e===null)return null;if(typeof e=="boolean"||typeof e=="number"||typeof e=="string")return e}function Fs(e,t){return t>=4?"[array]":e.map(n=>Zn(n,t+1))}function xs(e,t){if(t>=4)return"[object]";const n={};for(const[r,a]of Object.entries(e))n[r]=Zn(a,t+1);return n}function Ts(e){return typeof e=="bigint"?e.toString():typeof e=="symbol"?e.description?`Symbol(${e.description})`:"Symbol()":typeof e=="function"?`[function ${e.name||"anonymous"}]`:"[unserializable]"}function Rs(e,t,n){const r={level:Ps(e),message:t};return n!==void 0&&(r.context=Zn(n)),r}function Ls(e,t){function n(r,a,o){const s=Cs(r);o===void 0?s(`[${e}] ${a}`):s(`[${e}] ${a}`,o);try{t(Rs(r,a,o))}catch{}}return{debug:(r,a)=>n("debug",r,a),error:(r,a)=>n("error",r,a),info:(r,a)=>n("info",r,a),warn:(r,a)=>n("warn",r,a)}}const le=Ls("editor",bs);function $s(e,t){return Math.max(t.startMs,Math.min(Number(e)||0,t.endMs))}function Os(e){let t="start";e.playbackState==="playing"&&(t="pause"),e.playbackState==="paused"&&(t=e.resumeRequiresRestart?"start":"resume");let n=e.anchorMs;return t==="start"&&e.region.mode==="selection"&&(n=e.region.startMs),t==="pause"&&(n=ua(e.currentProgressMs,e.cursorMs,n)),t==="resume"&&(n=ua(e.currentProgressMs,e.cursorMs,n),e.region.mode==="selection"&&(n<e.region.startMs||n>e.region.endMs)&&(t="start",n=e.region.startMs)),{action:t,cursorMs:Math.round(n),endMs:Math.round(e.region.endMs),engine:e.engine,loop:e.repeat,ord:e.ord,regionMode:e.region.mode}}function ua(e,t,n){return Number(e||t||n||0)}function Ds(e){return{analyzerName:e.analyzerName,durationMs:Number(e.durationMs)||0,pitchMaxHz:e.pitchMaxHz,pitchMinHz:e.pitchMinHz,points:e.points.map(Is),sourceFilename:e.sourceFilename}}function Is(e){const t=typeof e[0]=="number"?e[0]:0,n=typeof e[1]=="number"?e[1]:null,r=typeof e[2]=="number"?e[2]:null,a=typeof e[3]=="boolean"?e[3]:!1;return[t,n,r,a]}function ca(e){return e==="playing"||e==="paused"||e==="stopped"}const fa=50,Bs=4;function da(){return{active:!1,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:null,startMs:null}}function ha(e,t){return Math.max(0,Math.min(Number(e)||0,Math.max(0,Number(t)||0)))}function Pn(e,t,n,r=fa){const a=ha(Math.min(e,t),n),o=ha(Math.max(e,t),n);return!n||o-a<r?null:{startMs:Math.round(a),endMs:Math.round(o)}}function Vs(e,t){if(!e.active||e.startMs===null||e.endMs===null)return null;const n=Pn(e.startMs,e.endMs,t);return n?{...n,mode:"selection"}:null}function js(e,t){if(!e.draftActive||e.draftStartMs===null||e.draftEndMs===null)return null;const n=Pn(e.draftStartMs,e.draftEndMs,t);return n?{...n,mode:"selection"}:null}function Hs(e,t,n,r){const a=Pn(t,n,r);return a?{...e,active:!0,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:a.endMs,startMs:a.startMs}:Gs(e)}function Ws(e,t,n,r){const a=Pn(t,n,r);return a?{...e,draftActive:!0,draftEndMs:a.endMs,draftStartMs:a.startMs}:pa(e)}function Gs(e){return{...pa(e),active:!1,endMs:null,startMs:null}}function pa(e){return{...e,draftActive:!1,draftEndMs:null,draftStartMs:null}}function _a(e,t,n,r){return Math.abs(t.clientX-e.clientX)<Bs||Math.abs(r-n)<fa}const M={width:620,height:150,left:44,right:10,top:10,bottom:34};function va(){return M.width-M.left-M.right}function ma(){return M.height-M.top-M.bottom}function Ue(e,t){return t?M.left+Math.max(0,Math.min(1,e/t))*va():M.left}function Us(e,t,n){if(!e||!t||!n||n<=t)return M.height-M.bottom;const r=Math.max(0,Math.min(1,(e-t)/(n-t)));return M.top+(1-r)*ma()}function ga(e,t){return t&&t<2e3?`${Math.round(e)} ms`:`${(e/1e3).toFixed(2)}s`}function Xs(e,t){if(!e.length||!t)return"";const n=M.height-M.bottom,r=e[0];if(!r)return"";const a=`M ${Ue(r[0],t).toFixed(2)} ${n.toFixed(2)}`,o=e.map(l=>{const c=Ue(l[0],t).toFixed(2),p=Math.max(0,Math.min(1,l[2]??0)),u=(n-p*ma()).toFixed(2);return`L ${c} ${u}`}).join(" "),s=e.at(-1)??r,i=`L ${Ue(s[0],t).toFixed(2)} ${n.toFixed(2)} Z`;return`${a} ${o} ${i}`}function Ys(e,t,n,r){const a=[];let o=[];for(const s of e){const i=s[1];if(!(s[3]===!0&&i!==null&&i!==void 0)){o.length&&a.push(o),o=[];continue}o.push([Ue(s[0],t),Us(i,n,r)])}return o.length&&a.push(o),a}function Ks(e,t){const n=e.querySelector(".aqe-pitch");if(n){n.textContent="";for(const r of Ys(t.points,t.durationMs,t.pitchMinHz,t.pitchMaxHz)){if(r.length<2)continue;const a=document.createElementNS("http://www.w3.org/2000/svg","path");a.setAttribute("class","aqe-pitch-path"),a.setAttribute("d",r.map((o,s)=>{const i=o[0]??0,l=o[1]??0;return`${s?"L":"M"} ${i.toFixed(2)} ${l.toFixed(2)}`}).join(" ")),n.appendChild(a)}}}function Qs(e,t){const n=e.querySelector(".aqe-labels");if(!n)return;n.textContent="";const r=t.pitchMaxHz||500,a=t.pitchMinHz||75;for(const o of[[r,M.top+10],[a,M.height-M.bottom]]){const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","aqe-hz-label"),s.setAttribute("x","2"),s.setAttribute("y",String(o[1])),s.textContent=`${Math.round(o[0])} Hz`,n.appendChild(s)}}function Zs(e,t){const n=e.querySelector(".aqe-x-axis");if(!n)return;n.textContent="";const r=[0,t/2,t].filter((a,o,s)=>o===0||a!==s[o-1]);for(const a of r){const o=Ue(a,t),s=document.createElementNS("http://www.w3.org/2000/svg","line");s.setAttribute("class","aqe-x-tick"),s.setAttribute("x1",o.toFixed(2)),s.setAttribute("x2",o.toFixed(2)),s.setAttribute("y1",String(M.height-M.bottom)),s.setAttribute("y2",String(M.height-M.bottom+4));const i=document.createElementNS("http://www.w3.org/2000/svg","text");i.setAttribute("class","aqe-x-label"),i.setAttribute("x",o.toFixed(2)),i.setAttribute("y",String(M.height-8)),i.textContent=ga(a,t),n.append(s,i)}}function ya(e){const t=e.getBoundingClientRect(),n=Number(t.width)||M.width,r=Number(t.height)||M.height,a=Math.min(n/M.width,r/M.height)||1;return{left:t.left+(n-M.width*a)/2+M.left*a,width:va()*a}}function Jt(e,t,n){const r=ya(t);return Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*n}function Js(e){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="true",e.dataset.hasTrack="false",e.dataset.durationMs="0",e.dataset.sourceFilename="",e.dataset.anchorMs="0",e.dataset.cursorMs="0",e.dataset.progressMs="0",e.dataset.resumeRequiresRestart="false",e.dataset.playbackEngine="",e.dataset.playbackStartMs="0",e.dataset.playbackEndMs="0",e.dataset.playbackRegionMode="full",ba(e)}function zs(e,t){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="false",e.dataset.hasTrack="true",e.dataset.durationMs=String(t.durationMs||0),e.dataset.analyzerName=t.analyzerName||"",e.dataset.sourceFilename=t.sourceFilename||"";const n=e.querySelector(".aqe-intensity");n&&n.setAttribute("d",Xs(t.points,t.durationMs)),Ks(e,t),Qs(e,t),Zs(e,t.durationMs||0)}function ei(e,t,n="info"){const r=e.querySelector(".aqe-visualizer-status"),a=e.querySelector(".aqe-spinner"),o=n==="processing";e.dataset.graphBusy=o?"true":"false",a&&(a.hidden=!o),r&&(r.textContent=t||"",r.dataset.kind=n||"info")}function ti(e,t,n){const r=e.querySelector(".aqe-selection"),a=e.querySelector(".aqe-selection-start"),o=e.querySelector(".aqe-selection-end"),s=n??t,i=Number(e.dataset.durationMs||"0");if(!r||!a||!o||!s||!i){r==null||r.setAttribute("width","0"),r==null||r.setAttribute("visibility","hidden"),r==null||r.classList.remove("aqe-selection-draft"),a==null||a.setAttribute("visibility","hidden"),o==null||o.setAttribute("visibility","hidden");return}const l=Ue(s.startMs,i),c=Ue(s.endMs,i);r.setAttribute("visibility","visible"),r.classList.toggle("aqe-selection-draft",n!==null),r.setAttribute("x",l.toFixed(2)),r.setAttribute("y",String(M.top)),r.setAttribute("width",Math.max(0,c-l).toFixed(2)),r.setAttribute("height",String(M.height-M.top-M.bottom)),a.setAttribute("visibility","visible"),o.setAttribute("visibility","visible");for(const[p,u]of[[a,l],[o,c]])p.setAttribute("x1",u.toFixed(2)),p.setAttribute("x2",u.toFixed(2)),p.setAttribute("y1",String(M.top)),p.setAttribute("y2",String(M.height-M.bottom))}function ni(e,t,n){const r=Ue(t,n),a=e.querySelector(".aqe-cursor");a&&(a.setAttribute("x1",r.toFixed(2)),a.setAttribute("x2",r.toFixed(2)));const o=e.querySelector(".aqe-cursor-label");o&&(o.textContent=ga(t,n))}function ba(e){var t;(t=e.querySelector(".aqe-intensity"))==null||t.setAttribute("d",""),Jn(e,".aqe-pitch"),Jn(e,".aqe-labels"),Jn(e,".aqe-x-axis")}function ri(e){const t=e.querySelector(".aqe-cursor");t&&(t.setAttribute("x1",String(M.left)),t.setAttribute("x2",String(M.left)));const n=e.querySelector(".aqe-cursor-label");n&&(n.textContent="0 ms")}function ai(e,t){return{analyzerName:t.analyzerName,durationMs:t.durationMs,ord:e,points:t.points.length,sourceFilename:t.sourceFilename}}function Jn(e,t){const n=e.querySelector(t);n&&(n.textContent="")}function zn(e){return!e||e.dataset.selectionActive!=="true"?null:Vs({active:e.dataset.selectionActive==="true",startMs:Number(e.dataset.selectionStartMs||"0"),endMs:Number(e.dataset.selectionEndMs||"0")},Number(e.dataset.durationMs||"0"))}function er(e){return!e||e.dataset.selectionDraftActive!=="true"?null:js({draftActive:e.dataset.selectionDraftActive==="true",draftStartMs:Number(e.dataset.selectionDraftStartMs||"0"),draftEndMs:Number(e.dataset.selectionDraftEndMs||"0")},Number(e.dataset.durationMs||"0"))}function wa(e){const t=zn(e);return t||{startMs:0,endMs:Number(e.dataset.durationMs||"0")||0,mode:"full"}}function Ct(e,t={}){e.dataset.selectionDraftActive="false",e.dataset.selectionDraftStartMs="",e.dataset.selectionDraftEndMs="",t.redraw!==!1&&Nn(e)}function oi(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Ws(da(),t,n,a);return!o.draftActive||o.draftStartMs===null||o.draftEndMs===null?(Ct(e,r),!1):(e.dataset.selectionDraftActive="true",e.dataset.selectionDraftStartMs=String(o.draftStartMs),e.dataset.selectionDraftEndMs=String(o.draftEndMs),r.redraw!==!1&&Nn(e),!0)}function si(e,t,n={}){const r=er(e);return r?(Ct(e,{redraw:!1}),ii(e,r.startMs,r.endMs,t,n)):(Ct(e),!1)}function Ma(e,t={}){if(e.dataset.selectionActive="false",e.dataset.selectionStartMs="",e.dataset.selectionEndMs="",Ct(e,{redraw:!1}),Nn(e),t.resetPlaybackRegion!==!1){const n=wa(e);e.dataset.playbackStartMs=String(Math.round(n.startMs)),e.dataset.playbackEndMs=String(Math.round(n.endMs)),e.dataset.playbackRegionMode=n.mode}}function ii(e,t,n,r,a={}){const o=Number(e.dataset.durationMs||"0"),s=Hs(da(),t,n,o);return!s.active||s.startMs===null||s.endMs===null?(Ma(e),!1):(Ct(e,{redraw:!1}),e.dataset.selectionActive="true",e.dataset.selectionStartMs=String(s.startMs),e.dataset.selectionEndMs=String(s.endMs),e.dataset.playbackStartMs=String(s.startMs),e.dataset.playbackEndMs=String(s.endMs),e.dataset.playbackRegionMode="selection",Nn(e),a.updateCursor!==!1&&r.setCursor(e,s.startMs,!1),!0)}function Nn(e){const t=er(e),n=t??zn(e);ti(e,n,t)}function li(e,t,n,r,a){e.preventDefault();const o=a.playbackStateFor(t),s=t.querySelector(".aqe-visualizer-svg"),i=Number(t.dataset.durationMs||"0");if(!s||!i)return;o==="playing"&&a.stopProgressClock(t);const l=p=>{a.setCursor(t,ka(p,s,i,t,a),!1)},c=p=>{window.removeEventListener("pointermove",l),window.removeEventListener("pointerup",c);const u=o==="playing";o==="paused"&&(t.dataset.resumeRequiresRestart="true");const d=ka(p,s,i,t,a),v=u&&a.audioClockReady(t)?"html":"";a.setCursor(t,d,r,{previousPlaybackState:o,restartPlayback:u,engine:v}),a.audioClockReady(t)&&a.seekAudioClock(t,d),u&&v==="html"&&a.startEditorHtmlPlayback(t,a.playbackRequestForStart(t,n,d,"html"))};l(e),window.addEventListener("pointermove",l),window.addEventListener("pointerup",c)}function ui(e,t,n,r){e.preventDefault();const a=t.querySelector(".aqe-visualizer-svg"),o=Number(t.dataset.durationMs||"0");if(!a||!o)return;const s=r.playbackStateFor(t),i=r.currentProgressMs(t)??Number(t.dataset.cursorMs||"0"),l={clientX:e.clientX},c=Jt(e,a,o);let p=!1,u=S=>{},d=S=>{},v=()=>{},f=S=>{};const m=()=>{window.removeEventListener("pointermove",u),window.removeEventListener("pointerup",d),window.removeEventListener("pointercancel",v),window.removeEventListener("keydown",f),window.removeEventListener("blur",v),a.removeEventListener("lostpointercapture",v)},w=()=>{p||s!=="playing"||(p=!0,r.stopProgressClock(t,{clearEngine:!1}),r.setCursor(t,i,!1,{updateAnchor:!1}))},g=()=>{s==="playing"&&p&&r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,i,"html"))};u=S=>{const b=Jt(S,a,o);if(_a(l,S,c,b)){r.clearSelectionDraft(t);return}w(),r.setSelectionDraft(t,c,b)},d=S=>{m();const b=Jt(S,a,o);if(_a(l,S,c,b)){r.clearSelection(t),g();return}w(),r.draftSelectionForVisualizer(t)||r.setSelectionDraft(t,c,b,{redraw:!1});const k=r.commitSelectionDraft(t);if(s==="paused"&&(t.dataset.resumeRequiresRestart="true"),k&&s==="playing"){const _=r.selectionForVisualizer(t);r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,(_==null?void 0:_.startMs)??c,"html"))}},v=()=>{m(),r.clearSelectionDraft(t),g()},f=S=>{S.key==="Escape"&&v()},window.addEventListener("pointermove",u),window.addEventListener("pointerup",d),window.addEventListener("pointercancel",v),window.addEventListener("keydown",f),window.addEventListener("blur",v),a.addEventListener("lostpointercapture",v)}function ci(e,t,n){const r=n.visualizerForOrd(t);if(r){if(e.shiftKey){ui(e,r,t,n);return}li(e,r,t,!0,n)}}function ka(e,t,n,r,a){const o=Jt(e,t,n),s=a.selectionForVisualizer(r);return s&&r.dataset.repeatEnabled==="true"?$s(o,s):o}function lt(e){e.__aqePlaybackTimer&&(window.cancelAnimationFrame(e.__aqePlaybackTimer),e.__aqePlaybackTimer=null)}function Sa(e){const t=Number(e.dataset.durationMs||"0"),n=performance.now()-Number(e.dataset.playStartedAt||"0");return Math.min(t,Number(e.dataset.playStartMs||"0")+n)}function qa(e){const t=we(e);if(!t)return null;const n=Number(e.dataset.durationMs||"0");return Math.min(n,(Number(t.currentTime)||0)*1e3)}function Aa(e){return e.dataset.progressClockMode==="audio"?qa(e):e.dataset.progressClockMode==="manual"?Sa(e):Number(e.dataset.progressMs||e.dataset.cursorMs||"0")}function tr(e,t,n,r={}){return t<_i(e,n)?!1:n.repeatEnabledFor(e)?(vi(e,n,r),!0):(fi(e,n),!0)}function fi(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=t.effectivePlaybackRegion(e),a=e.dataset.playbackRegionMode==="selection"?r.startMs:Number(e.dataset.anchorMs||"0");rr(e,t),t.setCursor(e,a,!1,{updateAnchor:!1}),En(e)&&Cn(e,a,Number(e.dataset.durationMs||"0")),t.clearStatus(n),window.__aqeActiveField=n,t.focusAndSendCommand(n,"aqe:play-ended")}function nr(e,t){const n=()=>{if(e.dataset.playbackState!=="playing")return;const r=qa(e);if(r===null){De(e,Number(e.dataset.cursorMs||"0"),t);return}t.setCursor(e,r,!1,{updateAnchor:!1}),!tr(e,r,t)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(n))};e.__aqePlaybackTimer=window.requestAnimationFrame(n)}function De(e,t,n){if(lt(e),Qt(e),!Number(e.dataset.durationMs||"0"))return;const a=Ea(e,t);e.__aqeAudioClockFallback=!0,e.dataset.playbackState="playing",e.dataset.progressClockMode="manual",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),ar(e,a,n),n.setPlaybackButtonLabel(e,"Pause");const o=()=>{if(e.dataset.playbackState!=="playing")return;const s=Sa(e);n.setCursor(e,s,!1,{updateAnchor:!1}),!tr(e,s,n)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(o))};e.__aqePlaybackTimer=window.requestAnimationFrame(o)}function di(e,t,n,r={}){var i;const a=we(e);if(!a||!Cn(e,t,Number(e.dataset.durationMs||"0"))||typeof a.play!="function"){if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}De(e,t,n);return}e.dataset.progressClockMode="audio",e.__aqeAudioClockFallback=!1;const o=()=>{var l;if(r.manualFallback===!1){(l=r.onAudioPlayFailed)==null||l.call(r);return}De(e,t,n)},s=()=>{var l;e.dataset.playbackState==="playing"&&(lt(e),e.dataset.progressClockMode="audio",le.info("html audio playback started",{ord:e.dataset.aqeFieldOrd}),nr(e,n),(l=r.onAudioStarted)==null||l.call(r))};Promise.resolve(a.play()).then(s).catch(()=>{e.dataset.playbackState==="playing"&&(le.warn("html audio play rejected; using manual clock",{ord:e.dataset.aqeFieldOrd}),o())})}function hi(e,t,n,r={}){var i;const a=r.engine||e.dataset.playbackEngine||"";if(rr(e,n,{clearEngine:!1}),n.stopOtherPlayback(e),!Number(e.dataset.durationMs||"0"))return;const s=Ea(e,t);if(e.dataset.playbackEngine=a,e.dataset.playbackState="playing",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(s),ar(e,s,n),n.setCursor(e,s,!1,{updateAnchor:!1}),n.setPlaybackButtonLabel(e,"Pause"),le.info("playback clock selected",{engine:a||"auto",startMs:s}),a==="native"){De(e,s,n);return}if(En(e)){di(e,s,n,r);return}if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}De(e,s,n)}function pi(e,t){const n=Aa(e);n!==null&&t.setCursor(e,n,!1,{updateAnchor:!1}),lt(e),Qt(e),e.dataset.playbackState="paused",e.dataset.progressClockMode="stopped",t.setPlaybackButtonLabel(e,"Play")}function rr(e,t,n={}){lt(e),Qt(e),e.dataset.playbackState="stopped",e.dataset.progressClockMode="stopped",e.dataset.resumeRequiresRestart="false",n.clearEngine!==!1&&(e.dataset.playbackEngine=""),n.clearAudio&&Qn(e),t.setPlaybackButtonLabel(e,"Play")}function ar(e,t,n,r=n.effectivePlaybackRegion(e)){e.dataset.playbackStartMs=String(Math.round(t)),e.dataset.playbackEndMs=String(Math.round(r.endMs)),e.dataset.playbackRegionMode=r.mode}function _i(e,t){const n=t.effectivePlaybackRegion(e),r=Number(e.dataset.playbackEndMs||"0")||n.endMs;return Math.max(n.startMs,Math.min(r,Number(e.dataset.durationMs||"0")||0))}function vi(e,t,n={}){const r=t.effectivePlaybackRegion(e),a=r.startMs;if(ar(e,a,t,r),e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),t.setCursor(e,a,!1,{updateAnchor:!1}),e.dataset.progressClockMode!=="audio"||!En(e)){De(e,a,t);return}if(!Cn(e,a,Number(e.dataset.durationMs||"0"))){De(e,a,t);return}if(!n.forceAudioPlay){lt(e),nr(e,t);return}const o=we(e);!o||typeof o.play!="function"||(lt(e),Promise.resolve(o.play()).then(()=>{e.dataset.playbackState==="playing"&&nr(e,t)}).catch(()=>{e.dataset.playbackState==="playing"&&De(e,a,t)}))}function Ea(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function mi(){return document.body.dataset.aqeBusy==="true"}function Ca(){var e;return((e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.repeatPlaybackByDefault)===!0}function gi(e){for(const t of ia())t!==e&&Nt(t)!=="stopped"&&ct(t)}function yi(){for(const e of ia())Nt(e)!=="stopped"&&ct(e)}function Fn(e,t,n="",r=""){document.body.dataset.aqeBusy=t?"true":"false",document.querySelectorAll(".aqe-controls").forEach(s=>{s.dataset.busy=t?"true":"false"}),An().forEach(s=>{s.disabled=!!t}),ys().forEach(s=>{s.disabled=!!t});const a=Et(e),o=a==null?void 0:a.querySelector(".aqe-status");o&&(o.textContent=n||"",o.dataset.kind=t?"processing":"info",o.title=r||"")}function Pa(e,t="info"){const n=Number(window.__aqeActiveField??0),r=Et(n),a=r==null?void 0:r.querySelector(".aqe-status");a&&(a.textContent=e||"",a.dataset.kind=t||"info")}function bi(e){const t=Et(e),n=t==null?void 0:t.querySelector(".aqe-status");n&&(n.textContent="",n.dataset.kind="info",n.title="")}function Pt(e,t,n){var o;const r=t==="aqe:play"?oa(e):t==="aqe:analyze"?aa(e):((o=Et(e))==null?void 0:o.querySelector(`[data-aqe-command="${t}"]`))??null;if(!r)return;const a=r.querySelector(".aqe-button-label");a?a.textContent=n:r.textContent=n,t==="aqe:play"&&(r.dataset.aqeButtonState=n==="Pause"?"pause":"play"),t==="aqe:analyze"&&(r.dataset.aqeButtonState=n==="Redraw"?"redraw":"graph")}function wi(e,t,n){if(!mi()){if(typeof t.focus=="function"&&t.focus(),window.__aqeActiveField=n,le.info("command dispatched",{command:e,ord:n}),e==="aqe:analyze"){Ta(n,!0);return}e==="aqe:play"&&Hi(n)||(R.has(e)&&(yi(),Fn(n,!0,gs(e))),Kt(n,e))}}function Mi(e){Kn(e)}function ki(e){lt(e)}function Si(e){Qn(e)}function qi(e,t){As(e,t)}function Ai(e){Es(e,{onErrorDuringPlayback(){le.warn("audio clock failed during playback",{ord:e.dataset.aqeFieldOrd}),ji(e,Number(e.dataset.cursorMs||"0"))},onEndedDuringPlayback(){Vi(e,Number(e.dataset.durationMs||"0"),{forceAudioPlay:!0})}})}function or(e){return En(e)}function Ei(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function Na(e){return zn(e)}function Fa(e){return er(e)}function sr(e){return wa(e)}function ir(e,t){e.dataset.repeatEnabled=t?"true":"false";const n=Number(e.dataset.aqeFieldOrd||"0"),r=sa(n);r&&(r.checked=t)}function Ci(e,t){const n=$(e);return n?(ir(n,t),!0):!1}function Pi(e,t={}){Ct(e,t)}function Ni(e,t,n,r={}){return oi(e,t,n,r)}function Fi(e,t={}){return si(e,Ri(),t)}function zt(e,t={}){Ma(e,t)}function xi(e){e.dataset.playbackStartMs="0",e.dataset.playbackEndMs=String(Number(e.dataset.durationMs||"0")||0),e.dataset.playbackRegionMode="full",ir(e,Ca()),zt(e,{resetPlaybackRegion:!1})}function Ti(){return{audioClockReady:or,clearSelection:zt,clearSelectionDraft:Pi,commitSelectionDraft:Fi,currentProgressMs:La,draftSelectionForVisualizer:Fa,playbackRequestForStart:Li,playbackStateFor:Nt,seekAudioClock:xa,selectionForVisualizer:Na,setCursor:ut,setSelectionDraft:Ni,startEditorHtmlPlayback:Ia,stopProgressClock:ct,visualizerForOrd:$}}function Ri(){return{setCursor:ut}}function lr(e){return e.dataset.repeatEnabled==="true"}function en(){return{clearStatus:bi,effectivePlaybackRegion:sr,focusAndSendCommand:Kt,playbackEngineFor:tn,repeatEnabledFor:lr,setCursor:ut,setPlaybackButtonLabel:Bi,stopOtherPlayback:gi}}function Li(e,t,n,r=tn(e)){const a=sr(e);return{ord:t,action:"start",cursorMs:Math.round(Ei(e,n)),endMs:Math.round(a.endMs),engine:r,loop:lr(e),regionMode:a.mode}}function xa(e,t){return Cn(e,t,Number(e.dataset.durationMs||"0"))}function ut(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Math.max(0,Math.min(Number(t)||0,a||0));if(e.dataset.cursorMs=String(Math.round(o)),e.dataset.progressMs=String(Math.round(o)),r.updateAnchor!==!1&&(e.dataset.anchorMs=String(Math.round(o))),ni(e,o,a),n){window.__aqeActiveField=Number(e.dataset.aqeFieldOrd||"0");const s={cursorMs:Math.round(o),previousPlaybackState:r.previousPlaybackState||Nt(e),restartPlayback:!!r.restartPlayback};r.engine&&(s.engine=r.engine),Ss(s),le.info("cursor committed",s),Kt(window.__aqeActiveField,"aqe:set-cursor")}}function $i(e,t){ci(e,t,Ti())}function Ta(e,t){const n=$(e);n&&(ct(n,{clearAudio:!0}),Js(n),zt(n),ut(n,0,!1),Pt(e,"aqe:analyze","Redraw"),cr(e,"Analyzing...","processing"),window.__aqeActiveField=e,le.info("graph requested",{notifyPython:t,ord:e}),Fn(e,!0,"Analyzing...",""),Kt(e,"aqe:analyze"))}function Oi(e){return window.__aqePendingGraphRedrawField=e,ur()}function ur(){const e=window.__aqePendingGraphRedrawField;if(typeof e!="number")return!1;const t=$(e);return t?(t.dataset.graphBusy==="true"||t.dataset.hasTrack==="true"||Ta(e,!0),!0):!1}function cr(e,t,n="info"){const r=$(e);r&&ei(r,t,n)}function Di(e,t,n){const r=$(e);if(!r||!t)return;const a=Ds(t);zs(r,a),r.dataset.anchorMs=String(n||0),window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null),zt(r),r.dataset.playbackStartMs="0",r.dataset.playbackEndMs=String(a.durationMs||0),r.dataset.playbackRegionMode="full",qi(r,a.sourceFilename||""),Pt(e,"aqe:analyze","Redraw"),ut(r,n||0,!1),or(r)&&xa(r,n||0),cr(e,a.analyzerName||"","info"),Fn(e,!1,"",""),le.info("graph rendered",ai(e,a))}function Ii(e,t,n="info"){n!=="processing"&&window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null);const r=$(e);r&&(r.hidden=!1,r.dataset.graphActive="true",n==="processing"&&(r.dataset.hasTrack="false"),Pt(e,"aqe:analyze","Redraw")),cr(e,t,n)}function Ra(){document.body.dataset.aqeBusy="false",window.__aqeActiveField=null,window.__aqeLastCursorIntent=null,document.querySelectorAll(".aqe-controls").forEach(e=>{e.dataset.busy="false",e.dataset.aqeSourceFilename="",e.querySelectorAll(".aqe-button").forEach(o=>{o.disabled=!1,o.dataset.aqeCommand==="aqe:analyze"&&Pt(Number(e.dataset.aqeFieldOrd||"0"),"aqe:analyze","Graph"),o.dataset.aqeCommand==="aqe:play"&&Pt(Number(e.dataset.aqeFieldOrd||"0"),"aqe:play","Play")}),e.querySelectorAll(".aqe-repeat-checkbox").forEach(o=>{o.disabled=!1});const t=e.querySelector(".aqe-status");t&&(t.textContent="",t.dataset.kind="info",t.title="");const n=e.querySelector(".aqe-visualizer");if(!n)return;ki(n),Si(n),n.hidden=!0,n.dataset.anchorMs="0",n.dataset.cursorMs="0",n.dataset.progressMs="0",n.dataset.graphActive="false",n.dataset.graphBusy="false",n.dataset.hasTrack="false",n.dataset.playbackState="stopped",n.dataset.playbackEngine="",n.dataset.resumeRequiresRestart="false",n.dataset.durationMs="0",n.dataset.sourceFilename="",n.dataset.analyzerName="",n.dataset.playStartedAt="0",n.dataset.playStartMs="0",n.dataset.playbackStartMs="0",n.dataset.playbackEndMs="0",n.dataset.playbackRegionMode="full",n.dataset.progressClockMode="stopped",ir(n,Ca()),zt(n),ba(n),ri(n);const r=n.querySelector(".aqe-visualizer-status");r&&(r.textContent="",r.dataset.kind="info");const a=n.querySelector(".aqe-spinner");a&&(a.hidden=!0)})}function Bi(e,t){const n=Number(e.dataset.aqeFieldOrd||"0");Pt(n,"aqe:play",t)}function La(e){return Aa(e)}function Vi(e,t,n={}){return tr(e,t,en(),n)}function ji(e,t){De(e,t,en())}function $a(e,t,n={}){hi(e,t,en(),n)}function Oa(e){pi(e,en())}function ct(e,t={}){rr(e,en(),t)}function Da(e){const t=$(e);return t?Os({anchorMs:Number(t.dataset.anchorMs||t.dataset.cursorMs||"0"),currentProgressMs:La(t),cursorMs:Number(t.dataset.cursorMs||"0"),engine:tn(t),ord:e,playbackState:Nt(t),region:sr(t),repeat:lr(t),resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true"}):{ord:e,action:"start",cursorMs:0}}function tn(e){if(!e||e.dataset.hasTrack!=="true")return"native";const t=e.dataset.playbackEngine||"";return e.dataset.playbackState!=="stopped"&&(t==="html"||t==="native")?t:or(e)?"html":"native"}function fr(e){const t=$(e.ord);t&&(t.dataset.playbackEngine=e.engine||""),Ms(e),window.__aqeActiveField=e.ord,le.info("playback request queued",e),Kt(e.ord,"aqe:play")}function Ia(e,t){return $a(e,t.cursorMs,{engine:"html",manualFallback:!1,onAudioStarted(){fr(t)},onAudioPlayFailed(){if(le.warn("html playback failed; falling back to native",{ord:t.ord}),ct(e),t.regionMode==="selection"||t.loop){window.__aqeActiveField=t.ord,Pa("Selected repeat playback needs browser audio.","warning");return}fr({...t,engine:"native"})}}),!0}function Hi(e){const t=$(e);if(!t||tn(t)!=="html")return!1;const n={...Da(e),engine:"html"};return n.action==="pause"?(Oa(t),n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0"),fr(n),!0):(n.action==="resume"&&(n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0")),Ia(t,n))}function Wi(e,t,n){const r=$(e);r&&((t==="playing"||t==="paused")&&(r.dataset.resumeRequiresRestart="false"),t==="playing"?$a(r,n,{engine:r.dataset.playbackEngine==="html"||r.dataset.playbackEngine==="native"?r.dataset.playbackEngine:""}):t==="paused"?Oa(r):ct(r))}function Gi(){const e=ks();if(e)return e;const t=Number(window.__aqeActiveField||"0"),n=Da(t),r=$(t);return r&&(r.dataset.playbackEngine=n.engine||""),n}function Ui(e){const t=$(e);return t?(ct(t),!0):!1}function Xi(){const e=Number(window.__aqeActiveField||"0"),t=$(e);return t?Number(t.dataset.cursorMs||"0"):0}function Yi(){const e=Number(window.__aqeActiveField||"0"),t=$(e),n=t?Number(t.dataset.cursorMs||"0"):0;return window.__aqeLastCursorIntent||{cursorMs:n,previousPlaybackState:t?Nt(t):"stopped",restartPlayback:!1}}function Nt(e){const t=e.dataset.playbackState;return ca(t)?t:"stopped"}const Ba=(cs=(us=globalThis.process)==null?void 0:us.env)==null?void 0:cs.NODE_ENV,y=Ba&&!Ba.toLowerCase().startsWith("prod");var dr=Array.isArray,Ki=Array.prototype.indexOf,ft=Array.prototype.includes,xn=Array.from,dt=Object.defineProperty,Ie=Object.getOwnPropertyDescriptor,Qi=Object.getOwnPropertyDescriptors,Zi=Object.prototype,Ji=Array.prototype,Va=Object.getPrototypeOf,ja=Object.isExtensible;function nn(e){return typeof e=="function"}const U=()=>{};function zi(e){for(var t=0;t<e.length;t++)e[t]()}function Ha(){var e,t,n=new Promise((r,a)=>{e=r,t=a});return{promise:n,resolve:e,reject:t}}function el(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const r of e)if(n.push(r),n.length===t)break;return n}const X=2,rn=4,Tn=8,hr=1<<24,Be=16,Me=32,ht=64,pr=128,_e=512,H=1024,Y=2048,ke=4096,ue=8192,Ve=16384,pt=32768,Xe=65536,Rn=1<<17,Wa=1<<18,Ft=1<<19,tl=1<<20,Ye=1<<25,Ke=65536,_r=1<<21,Ln=1<<22,Qe=1<<23,Ze=Symbol("$state"),Ga=Symbol("legacy props"),nl=Symbol(""),Ua=Symbol("proxy path"),_t=new class extends Error{constructor(){super(...arguments);Oe(this,"name","StaleReactionError");Oe(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}},Xa=!!((fs=globalThis.document)!=null&&fs.contentType)&&globalThis.document.contentType.includes("xml");function Ya(e){if(y){const t=new Error(`lifecycle_outside_component
\`${e}(...)\` can only be used during component initialisation
https://svelte.dev/e/lifecycle_outside_component`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/lifecycle_outside_component")}function rl(){if(y){const e=new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/async_derived_orphan")}function al(){if(y){const e=new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/derived_references_self")}function Ka(e,t,n){if(y){const r=new Error(`each_key_duplicate
${n?`Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}`:`Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_duplicate")}function ol(e,t,n){if(y){const r=new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_volatile")}function sl(e){if(y){const t=new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_in_teardown")}function il(){if(y){const e=new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function ll(e){if(y){const t=new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_orphan")}function ul(){if(y){const e=new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function cl(){if(y){const e=new Error("invalid_snippet\nCould not `{@render}` snippet due to the expression being `null` or `undefined`. Consider using optional chaining `{@render snippet?.()}`\nhttps://svelte.dev/e/invalid_snippet");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/invalid_snippet")}function fl(e){if(y){const t=new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_invalid_value")}function dl(e){if(y){const t=new Error(`props_rest_readonly
Rest element properties of \`$props()\` such as \`${e}\` are readonly
https://svelte.dev/e/props_rest_readonly`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_rest_readonly")}function hl(e){if(y){const t=new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/rune_outside_svelte")}function pl(){if(y){const e=new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function _l(){if(y){const e=new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_prototype_fixed")}function vl(){if(y){const e=new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function ml(){if(y){const e=new Error("svelte_boundary_reset_onerror\nA `<svelte:boundary>` `reset` function cannot be called while an error is still being handled\nhttps://svelte.dev/e/svelte_boundary_reset_onerror");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const gl=1,yl=2,bl=16,wl=1,Ml=4,kl=8,Sl=16,ql=1,Al=2,W=Symbol(),El=Symbol("filename"),Qa="http://www.w3.org/1999/xhtml",Cl="http://www.w3.org/2000/svg",Pl="@attach";var an="font-weight: bold",on="font-weight: normal";function Nl(){y?console.warn(`%c[svelte] lifecycle_double_unmount
%cTried to unmount a component that was not mounted
https://svelte.dev/e/lifecycle_double_unmount`,an,on):console.warn("https://svelte.dev/e/lifecycle_double_unmount")}function Fl(){y?console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value",an,on):console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function vr(e){y?console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`,an,on):console.warn("https://svelte.dev/e/state_proxy_equality_mismatch")}function xl(){y?console.warn(`%c[svelte] state_proxy_unmount
%cTried to unmount a state proxy, rather than a component
https://svelte.dev/e/state_proxy_unmount`,an,on):console.warn("https://svelte.dev/e/state_proxy_unmount")}function Tl(){y?console.warn("%c[svelte] svelte_boundary_reset_noop\n%cA `<svelte:boundary>` `reset` function only resets the boundary the first time it is called\nhttps://svelte.dev/e/svelte_boundary_reset_noop",an,on):console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Za(e){return e===this.v}function Rl(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Ja(e){return!Rl(e,this.v)}let Ll=!1;function Fe(e,t){return e.label=t,za(e.v,t),e}function za(e,t){var n;return(n=e==null?void 0:e[Ua])==null||n.call(e,t),e}function $l(e){const t=new Error,n=Ol();return n.length===0?null:(n.unshift(`
`),dt(t,"stack",{value:n.join(`
`)}),dt(t,"name",{value:e}),t)}function Ol(){const e=Error.stackTraceLimit;Error.stackTraceLimit=1/0;const t=new Error().stack;if(Error.stackTraceLimit=e,!t)return[];const n=t.split(`
`),r=[];for(let a=0;a<n.length;a++){const o=n[a],s=o.replaceAll("\\","/");if(o.trim()!=="Error"){if(o.includes("validate_each_keys"))return[];s.includes("svelte/src/internal")||s.includes("node_modules/.vite")||r.push(o)}}return r}let L=null;function xt(e){L=e}let Tt=null;function $n(e){Tt=e}let sn=null;function eo(e){sn=e}function Dl(e){return Il("getContext").get(e)}function B(e,t=!1,n){L={p:L,i:!1,c:null,e:null,s:e,x:null,l:null},y&&(L.function=n,sn=n)}function V(e){var t=L,n=t.e;if(n!==null){t.e=null;for(var r of n)So(r)}return t.i=!0,L=t.p,y&&(sn=(L==null?void 0:L.function)??null),{}}function to(){return!0}function Il(e){return L===null&&Ya(e),L.c??(L.c=new Map(Bl(L)||void 0))}function Bl(e){let t=e.p;for(;t!==null;){const n=t.c;if(n!==null)return n;t=t.p}return null}let Rt=[];function Vl(){var e=Rt;Rt=[],zi(e)}function Je(e){if(Rt.length===0){var t=Rt;queueMicrotask(()=>{t===Rt&&Vl()})}Rt.push(e)}const mr=new WeakMap;function no(e){var t=N;if(t===null)return E.f|=Qe,e;if(y&&e instanceof Error&&!mr.has(e)&&mr.set(e,jl(e,t)),(t.f&pt)===0&&(t.f&rn)===0)throw y&&!t.parent&&e instanceof Error&&ro(e),e;ze(e,t)}function ze(e,t){for(;t!==null;){if((t.f&pr)!==0){if((t.f&pt)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw y&&e instanceof Error&&ro(e),e}function jl(e,t){var s,i,l;const n=Ie(e,"message");if(!(n&&!n.configurable)){for(var r=Ar?"  ":"	",a=`
${r}in ${((s=t.fn)==null?void 0:s.name)||"<unknown>"}`,o=t.ctx;o!==null;)a+=`
${r}in ${(i=o.function)==null?void 0:i[El].split("/").pop()}`,o=o.p;return{message:e.message+`
${a}
`,stack:(l=e.stack)==null?void 0:l.split(`
`).filter(c=>!c.includes("svelte/src/internal")).join(`
`)}}}function ro(e){const t=mr.get(e);t&&(dt(e,"message",{value:t.message}),dt(e,"stack",{value:t.stack}))}const Hl=-7169;function O(e,t){e.f=e.f&Hl|t}function gr(e){(e.f&_e)!==0||e.deps===null?O(e,H):O(e,ke)}function ao(e){if(e!==null)for(const t of e)(t.f&X)===0||(t.f&Ke)===0||(t.f^=Ke,ao(t.deps))}function oo(e,t,n){(e.f&Y)!==0?t.add(e):(e.f&ke)!==0&&n.add(e),ao(e.deps),O(e,H)}const On=new Set;let F=null,K=null,ve=[],yr=null,br=!1;const Yr=class Yr{constructor(){P(this,fe);Oe(this,"current",new Map);Oe(this,"previous",new Map);P(this,jt,new Set);P(this,Ht,new Set);P(this,Mt,0);P(this,Wt,0);P(this,wn,null);P(this,Mn,new Set);P(this,kt,new Set);P(this,He,new Map);Oe(this,"is_fork",!1);P(this,Gt,!1)}skip_effect(t){h(this,He).has(t)||h(this,He).set(t,{d:[],m:[]})}unskip_effect(t){var n=h(this,He).get(t);if(n){h(this,He).delete(t);for(var r of n.d)O(r,Y),qe(r);for(r of n.m)O(r,ke),qe(r)}}process(t){var a;ve=[],this.apply();var n=[],r=[];for(const o of t)G(this,fe,zr).call(this,o,n,r);if(G(this,fe,Jr).call(this)){G(this,fe,ea).call(this,r),G(this,fe,ea).call(this,n);for(const[o,s]of h(this,He))uo(o,s)}else{for(const o of h(this,jt))o();h(this,jt).clear(),h(this,Mt)===0&&G(this,fe,ms).call(this),F=null,so(r),so(n),(a=h(this,wn))==null||a.resolve()}K=null}capture(t,n){n!==W&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&Qe)===0&&(this.current.set(t,t.v),K==null||K.set(t,t.v))}activate(){F=this,this.apply()}deactivate(){F===this&&(F=null,K=null)}flush(){if(this.activate(),ve.length>0){if(Wl(),F!==null&&F!==this)return}else h(this,Mt)===0&&this.process([]);this.deactivate()}discard(){for(const t of h(this,Ht))t(this);h(this,Ht).clear()}increment(t){A(this,Mt,h(this,Mt)+1),t&&A(this,Wt,h(this,Wt)+1)}decrement(t){A(this,Mt,h(this,Mt)-1),t&&A(this,Wt,h(this,Wt)-1),!h(this,Gt)&&(A(this,Gt,!0),Je(()=>{A(this,Gt,!1),G(this,fe,Jr).call(this)?ve.length>0&&this.flush():this.revive()}))}revive(){for(const t of h(this,Mn))h(this,kt).delete(t),O(t,Y),qe(t);for(const t of h(this,kt))O(t,ke),qe(t);this.flush()}oncommit(t){h(this,jt).add(t)}ondiscard(t){h(this,Ht).add(t)}settled(){return(h(this,wn)??A(this,wn,Ha())).promise}static ensure(){if(F===null){const t=F=new Yr;On.add(F),Je(()=>{F===t&&t.flush()})}return F}apply(){}};jt=new WeakMap,Ht=new WeakMap,Mt=new WeakMap,Wt=new WeakMap,wn=new WeakMap,Mn=new WeakMap,kt=new WeakMap,He=new WeakMap,Gt=new WeakMap,fe=new WeakSet,Jr=function(){return this.is_fork||h(this,Wt)>0},zr=function(t,n,r){t.f^=H;for(var a=t.first;a!==null;){var o=a.f,s=(o&(Me|ht))!==0,i=s&&(o&H)!==0,l=i||(o&ue)!==0||h(this,He).has(a);if(!l&&a.fn!==null){s?a.f^=H:(o&rn)!==0?n.push(a):dn(a)&&((o&Be)!==0&&h(this,kt).add(a),It(a));var c=a.first;if(c!==null){a=c;continue}}for(;a!==null;){var p=a.next;if(p!==null){a=p;break}a=a.parent}}},ea=function(t){for(var n=0;n<t.length;n+=1)oo(t[n],h(this,Mn),h(this,kt))},ms=function(){var a;if(On.size>1){this.previous.clear();var t=K,n=!0;for(const o of On){if(o===this){n=!1;continue}const s=[];for(const[l,c]of this.current){if(o.current.has(l))if(n&&c!==o.current.get(l))o.current.set(l,c);else continue;s.push(l)}if(s.length===0)continue;const i=[...o.current.keys()].filter(l=>!this.current.has(l));if(i.length>0){var r=ve;ve=[];const l=new Set,c=new Map;for(const p of s)io(p,i,l,c);if(ve.length>0){F=o,o.apply();for(const p of ve)G(a=o,fe,zr).call(a,p,[],[]);o.deactivate()}ve=r}}F=null,K=t}On.delete(this)};let et=Yr;function Wl(){br=!0;var e=y?new Set:null;try{for(var t=0;ve.length>0;){var n=et.ensure();if(t++>1e3){if(y){var r=new Map;for(const o of n.current.keys())for(const[s,i]of o.updated??[]){var a=r.get(s);a||(a={error:i.error,count:0},r.set(s,a)),a.count+=i.count}for(const o of r.values())o.error&&console.error(o.error)}Gl()}if(n.process(ve),tt.clear(),y)for(const o of n.current.keys())e.add(o)}}finally{if(ve=[],br=!1,yr=null,y)for(const o of e)o.updated=null}}function Gl(){try{ul()}catch(e){y&&dt(e,"stack",{value:""}),ze(e,yr)}}let Se=null;function so(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var r=e[n++];if((r.f&(Ve|ue))===0&&dn(r)&&(Se=new Set,It(r),r.deps===null&&r.first===null&&r.nodes===null&&r.teardown===null&&r.ac===null&&Co(r),(Se==null?void 0:Se.size)>0)){tt.clear();for(const a of Se){if((a.f&(Ve|ue))!==0)continue;const o=[a];let s=a.parent;for(;s!==null;)Se.has(s)&&(Se.delete(s),o.push(s)),s=s.parent;for(let i=o.length-1;i>=0;i--){const l=o[i];(l.f&(Ve|ue))===0&&It(l)}}Se.clear()}}Se=null}}function io(e,t,n,r){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const a of e.reactions){const o=a.f;(o&X)!==0?io(a,t,n,r):(o&(Ln|Be))!==0&&(o&Y)===0&&lo(a,t,r)&&(O(a,Y),qe(a))}}function lo(e,t,n){const r=n.get(e);if(r!==void 0)return r;if(e.deps!==null)for(const a of e.deps){if(ft.call(t,a))return!0;if((a.f&X)!==0&&lo(a,t,n))return n.set(a,!0),!0}return n.set(e,!1),!1}function qe(e){var t=yr=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(rn|Tn|hr))!==0&&(e.f&pt)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var r=t.f;if(br&&t===N&&(r&Be)!==0&&(r&Wa)===0&&(r&pt)!==0)return;if((r&(ht|Me))!==0){if((r&H)===0)return;t.f^=H}}ve.push(t)}function uo(e,t){if(!((e.f&Me)!==0&&(e.f&H)!==0)){(e.f&Y)!==0?t.d.push(e):(e.f&ke)!==0&&t.m.push(e),O(e,H);for(var n=e.first;n!==null;)uo(n,t),n=n.next}}function Ul(e){let t=0,n=vt(0),r;return y&&Fe(n,"createSubscriber version"),()=>{Cr()&&(x(n),mu(()=>(t===0&&(r=Tr(()=>e(()=>ln(n)))),t+=1,()=>{Je(()=>{t-=1,t===0&&(r==null||r(),r=void 0,ln(n))})})))}}var Xl=Xe|Ft;function Yl(e,t,n,r){new Kl(e,t,n,r)}class Kl{constructor(t,n,r,a){P(this,j);Oe(this,"parent");Oe(this,"is_pending",!1);Oe(this,"transform_error");P(this,be);P(this,Kr,null);P(this,Te);P(this,St);P(this,ie);P(this,Re,null);P(this,de,null);P(this,Ce,null);P(this,We,null);P(this,qt,0);P(this,it,0);P(this,Ut,!1);P(this,Xt,new Set);P(this,Yt,new Set);P(this,Le,null);P(this,Wn,Ul(()=>(A(this,Le,vt(h(this,qt))),y&&Fe(h(this,Le),"$effect.pending()"),()=>{A(this,Le,null)})));var o;A(this,be,t),A(this,Te,n),A(this,St,s=>{var i=N;i.b=this,i.f|=pr,r(s)}),this.parent=N.b,this.transform_error=a??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),A(this,ie,fn(()=>{G(this,j,ta).call(this)},Xl))}defer_effect(t){oo(t,h(this,Xt),h(this,Yt))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!h(this,Te).pending}update_pending_count(t){G(this,j,na).call(this,t),A(this,qt,h(this,qt)+t),!(!h(this,Le)||h(this,Ut))&&(A(this,Ut,!0),Je(()=>{A(this,Ut,!1),h(this,Le)&&$t(h(this,Le),h(this,qt))}))}get_effect_pending(){return h(this,Wn).call(this),x(h(this,Le))}error(t){var n=h(this,Te).onerror;let r=h(this,Te).failed;if(!n&&!r)throw t;h(this,Re)&&(Z(h(this,Re)),A(this,Re,null)),h(this,de)&&(Z(h(this,de)),A(this,de,null)),h(this,Ce)&&(Z(h(this,Ce)),A(this,Ce,null));var a=!1,o=!1;const s=()=>{if(a){Tl();return}a=!0,o&&ml(),h(this,Ce)!==null&&gt(h(this,Ce),()=>{A(this,Ce,null)}),G(this,j,Xn).call(this,()=>{et.ensure(),G(this,j,ta).call(this)})},i=l=>{try{o=!0,n==null||n(l,s),o=!1}catch(c){ze(c,h(this,ie)&&h(this,ie).parent)}r&&A(this,Ce,G(this,j,Xn).call(this,()=>{et.ensure();try{return oe(()=>{var c=N;c.b=this,c.f|=pr,r(h(this,be),()=>l,()=>s)})}catch(c){return ze(c,h(this,ie).parent),null}}))};Je(()=>{var l;try{l=this.transform_error(t)}catch(c){ze(c,h(this,ie)&&h(this,ie).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,c=>ze(c,h(this,ie)&&h(this,ie).parent)):i(l)})}}be=new WeakMap,Kr=new WeakMap,Te=new WeakMap,St=new WeakMap,ie=new WeakMap,Re=new WeakMap,de=new WeakMap,Ce=new WeakMap,We=new WeakMap,qt=new WeakMap,it=new WeakMap,Ut=new WeakMap,Xt=new WeakMap,Yt=new WeakMap,Le=new WeakMap,Wn=new WeakMap,j=new WeakSet,nf=function(){try{A(this,Re,oe(()=>h(this,St).call(this,h(this,be))))}catch(t){this.error(t)}},rf=function(t){const n=h(this,Te).failed;n&&A(this,Ce,oe(()=>{n(h(this,be),()=>t,()=>()=>{})}))},af=function(){const t=h(this,Te).pending;t&&(this.is_pending=!0,A(this,de,oe(()=>t(h(this,be)))),Je(()=>{var n=A(this,We,document.createDocumentFragment()),r=at();n.append(r),A(this,Re,G(this,j,Xn).call(this,()=>(et.ensure(),oe(()=>h(this,St).call(this,r))))),h(this,it)===0&&(h(this,be).before(n),A(this,We,null),gt(h(this,de),()=>{A(this,de,null)}),G(this,j,Un).call(this))}))},ta=function(){try{if(this.is_pending=this.has_pending_snippet(),A(this,it,0),A(this,qt,0),A(this,Re,oe(()=>{h(this,St).call(this,h(this,be))})),h(this,it)>0){var t=A(this,We,document.createDocumentFragment());Fo(h(this,Re),t);const n=h(this,Te).pending;A(this,de,oe(()=>n(h(this,be))))}else G(this,j,Un).call(this)}catch(n){this.error(n)}},Un=function(){this.is_pending=!1;for(const t of h(this,Xt))O(t,Y),qe(t);for(const t of h(this,Yt))O(t,ke),qe(t);h(this,Xt).clear(),h(this,Yt).clear()},Xn=function(t){var n=N,r=E,a=L;Ee(h(this,ie)),me(h(this,ie)),xt(h(this,ie).ctx);try{return t()}catch(o){return no(o),null}finally{Ee(n),me(r),xt(a)}},na=function(t){var n;if(!this.has_pending_snippet()){this.parent&&G(n=this.parent,j,na).call(n,t);return}A(this,it,h(this,it)+t),h(this,it)===0&&(G(this,j,Un).call(this),h(this,de)&&gt(h(this,de),()=>{A(this,de,null)}),h(this,We)&&(h(this,be).before(h(this,We)),A(this,We,null)))};function co(e,t,n,r){const a=Dn;var o=e.filter(u=>!u.settled);if(n.length===0&&o.length===0){r(t.map(a));return}var s=N,i=Ql(),l=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(u=>u.promise)):null;function c(u){i();try{r(u)}catch(d){(s.f&Ve)===0&&ze(d,s)}wr()}if(n.length===0){l.then(()=>c(t.map(a)));return}function p(){i(),Promise.all(n.map(u=>zl(u))).then(u=>c([...t.map(a),...u])).catch(u=>ze(u,s))}l?l.then(p):p()}function Ql(){var e=N,t=E,n=L,r=F;if(y)var a=Tt;return function(s=!0){Ee(e),me(t),xt(n),s&&(r==null||r.activate()),y&&$n(a)}}function wr(e=!0){Ee(null),me(null),xt(null),e&&(F==null||F.deactivate()),y&&$n(null)}function Zl(){var e=N.b,t=F,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}const Jl=new Set;function Dn(e){var t=X|Y,n=E!==null&&(E.f&X)!==0?E:null;return N!==null&&(N.f|=Ft),{ctx:L,deps:null,effects:null,equals:Za,f:t,fn:e,reactions:null,rv:0,v:W,wv:0,parent:n??N,ac:null}}function zl(e,t,n){N===null&&rl();var a=void 0,o=vt(W);y&&(o.label=t);var s=!E,i=new Map;return vu(()=>{var d;var l=Ha();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(wr)}catch(v){l.reject(v),wr()}var c=F;if(s){var p=Zl();(d=i.get(c))==null||d.reject(_t),i.delete(c),i.set(c,l)}const u=(v,f=void 0)=>{if(c.activate(),f)f!==_t&&(o.f|=Qe,$t(o,f));else{(o.f&Qe)!==0&&(o.f^=Qe),$t(o,v);for(const[m,w]of i){if(i.delete(m),m===c)break;w.reject(_t)}}p&&p()};l.promise.then(u,v=>u(null,v||"unknown"))}),Pr(()=>{for(const l of i.values())l.reject(_t)}),y&&(o.f|=Ln),new Promise(l=>{function c(p){function u(){p===a?l(o):c(a)}p.then(u,u)}c(a)})}function Mr(e){const t=Dn(e);return To(t),t}function fo(e){const t=Dn(e);return t.equals=Ja,t}function ho(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)Z(t[n])}}let kr=[];function eu(e){for(var t=e.parent;t!==null;){if((t.f&X)===0)return(t.f&Ve)===0?t:null;t=t.parent}return null}function Sr(e){var t,n=N;if(Ee(eu(e)),y){let r=Lt;vo(new Set);try{ft.call(kr,e)&&al(),kr.push(e),e.f&=~Ke,ho(e),t=xr(e)}finally{Ee(n),vo(r),kr.pop()}}else try{e.f&=~Ke,ho(e),t=xr(e)}finally{Ee(n)}return t}function po(e){var t=Sr(e);if(!e.equals(t)&&(e.wv=$o(),(!(F!=null&&F.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){O(e,H);return}ot||(K!==null?(Cr()||F!=null&&F.is_fork)&&K.set(e,t):gr(e))}function tu(e){var t,n;if(e.effects!==null)for(const r of e.effects)(r.teardown||r.ac)&&((t=r.teardown)==null||t.call(r),(n=r.ac)==null||n.abort(_t),r.teardown=U,r.ac=null,hn(r,0),Nr(r))}function _o(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&It(t)}let Lt=new Set;const tt=new Map;function vo(e){Lt=e}let qr=!1;function nu(){qr=!0}function vt(e,t){var n={f:0,v:e,reactions:null,equals:Za,rv:0,wv:0};return n}function nt(e,t){const n=vt(e);return To(n),n}function ru(e,t=!1,n=!0){const r=vt(e);return t||(r.equals=Ja),r}function rt(e,t,n=!1){E!==null&&(!Ae||(E.f&Rn)!==0)&&to()&&(E.f&(X|Be|Ln|Rn))!==0&&(ge===null||!ft.call(ge,e))&&vl();let r=n?Ot(t):t;return y&&za(r,e.label),$t(e,r)}function $t(e,t){var a;if(!e.equals(t)){var n=e.v;ot?tt.set(e,t):tt.set(e,n),e.v=t;var r=et.ensure();if(r.capture(e,n),y){if(N!==null){e.updated??(e.updated=new Map);const o=(((a=e.updated.get(""))==null?void 0:a.count)??0)+1;if(e.updated.set("",{error:null,count:o}),o>5){const s=$l("updated at");if(s!==null){let i=e.updated.get(s.stack);i||(i={error:s,count:0},e.updated.set(s.stack,i)),i.count++}}}N!==null&&(e.set_during_effect=!0)}if((e.f&X)!==0){const o=e;(e.f&Y)!==0&&Sr(o),gr(o)}e.wv=$o(),go(e,Y),N!==null&&(N.f&H)!==0&&(N.f&(Me|ht))===0&&(ye===null?bu([e]):ye.push(e)),!r.is_fork&&Lt.size>0&&!qr&&mo()}return t}function mo(){qr=!1;for(const e of Lt)(e.f&H)!==0&&O(e,ke),dn(e)&&It(e);Lt.clear()}function ln(e){rt(e,e.v+1)}function go(e,t){var n=e.reactions;if(n!==null)for(var r=n.length,a=0;a<r;a++){var o=n[a],s=o.f;if(y&&(s&Rn)!==0){Lt.add(o);continue}var i=(s&Y)===0;if(i&&O(o,t),(s&X)!==0){var l=o;K==null||K.delete(l),(s&Ke)===0&&(s&_e&&(o.f|=Ke),go(l,ke))}else i&&((s&Be)!==0&&Se!==null&&Se.add(o),qe(o))}}const au=/^[a-zA-Z_$][a-zA-Z_$0-9]*$/;function Ot(e){if(typeof e!="object"||e===null||Ze in e)return e;const t=Va(e);if(t!==Zi&&t!==Ji)return e;var n=new Map,r=dr(e),a=nt(0),o=bt,s=p=>{if(bt===o)return p();var u=E,d=bt;me(null),Lo(o);var v=p();return me(u),Lo(d),v};r&&(n.set("length",nt(e.length)),y&&(e=iu(e)));var i="";let l=!1;function c(p){if(!l){l=!0,i=p,Fe(a,`${i} version`);for(const[u,d]of n)Fe(d,mt(i,u));l=!1}}return new Proxy(e,{defineProperty(p,u,d){(!("value"in d)||d.configurable===!1||d.enumerable===!1||d.writable===!1)&&pl();var v=n.get(u);return v===void 0?s(()=>{var f=nt(d.value);return n.set(u,f),y&&typeof u=="string"&&Fe(f,mt(i,u)),f}):rt(v,d.value,!0),!0},deleteProperty(p,u){var d=n.get(u);if(d===void 0){if(u in p){const v=s(()=>nt(W));n.set(u,v),ln(a),y&&Fe(v,mt(i,u))}}else rt(d,W),ln(a);return!0},get(p,u,d){var w;if(u===Ze)return e;if(y&&u===Ua)return c;var v=n.get(u),f=u in p;if(v===void 0&&(!f||(w=Ie(p,u))!=null&&w.writable)&&(v=s(()=>{var g=Ot(f?p[u]:W),S=nt(g);return y&&Fe(S,mt(i,u)),S}),n.set(u,v)),v!==void 0){var m=x(v);return m===W?void 0:m}return Reflect.get(p,u,d)},getOwnPropertyDescriptor(p,u){var d=Reflect.getOwnPropertyDescriptor(p,u);if(d&&"value"in d){var v=n.get(u);v&&(d.value=x(v))}else if(d===void 0){var f=n.get(u),m=f==null?void 0:f.v;if(f!==void 0&&m!==W)return{enumerable:!0,configurable:!0,value:m,writable:!0}}return d},has(p,u){var m;if(u===Ze)return!0;var d=n.get(u),v=d!==void 0&&d.v!==W||Reflect.has(p,u);if(d!==void 0||N!==null&&(!v||(m=Ie(p,u))!=null&&m.writable)){d===void 0&&(d=s(()=>{var w=v?Ot(p[u]):W,g=nt(w);return y&&Fe(g,mt(i,u)),g}),n.set(u,d));var f=x(d);if(f===W)return!1}return v},set(p,u,d,v){var J;var f=n.get(u),m=u in p;if(r&&u==="length")for(var w=d;w<f.v;w+=1){var g=n.get(w+"");g!==void 0?rt(g,W):w in p&&(g=s(()=>nt(W)),n.set(w+"",g),y&&Fe(g,mt(i,w)))}if(f===void 0)(!m||(J=Ie(p,u))!=null&&J.writable)&&(f=s(()=>nt(void 0)),y&&Fe(f,mt(i,u)),rt(f,Ot(d)),n.set(u,f));else{m=f.v!==W;var S=s(()=>Ot(d));rt(f,S)}var b=Reflect.getOwnPropertyDescriptor(p,u);if(b!=null&&b.set&&b.set.call(v,d),!m){if(r&&typeof u=="string"){var k=n.get("length"),_=Number(u);Number.isInteger(_)&&_>=k.v&&rt(k,_+1)}ln(a)}return!0},ownKeys(p){x(a);var u=Reflect.ownKeys(p).filter(f=>{var m=n.get(f);return m===void 0||m.v!==W});for(var[d,v]of n)v.v!==W&&!(d in p)&&u.push(d);return u},setPrototypeOf(){_l()}})}function mt(e,t){return typeof t=="symbol"?`${e}[Symbol(${t.description??""})]`:au.test(t)?`${e}.${t}`:/^\d+$/.test(t)?`${e}[${t}]`:`${e}['${t}']`}function un(e){try{if(e!==null&&typeof e=="object"&&Ze in e)return e[Ze]}catch{}return e}function ou(e,t){return Object.is(un(e),un(t))}const su=new Set(["copyWithin","fill","pop","push","reverse","shift","sort","splice","unshift"]);function iu(e){return new Proxy(e,{get(t,n,r){var a=Reflect.get(t,n,r);return su.has(n)?function(...o){nu();var s=a.apply(this,o);return mo(),s}:a}})}function lu(){const e=Array.prototype,t=Array.__svelte_cleanup;t&&t();const{indexOf:n,lastIndexOf:r,includes:a}=e;e.indexOf=function(o,s){const i=n.call(this,o,s);if(i===-1){for(let l=s??0;l<this.length;l+=1)if(un(this[l])===o){vr("array.indexOf(...)");break}}return i},e.lastIndexOf=function(o,s){const i=r.call(this,o,s??this.length-1);if(i===-1){for(let l=0;l<=(s??this.length-1);l+=1)if(un(this[l])===o){vr("array.lastIndexOf(...)");break}}return i},e.includes=function(o,s){const i=a.call(this,o,s);if(!i){for(let l=0;l<this.length;l+=1)if(un(this[l])===o){vr("array.includes(...)");break}}return i},Array.__svelte_cleanup=()=>{e.indexOf=n,e.lastIndexOf=r,e.includes=a}}var yo,Ar,bo,wo;function uu(){if(yo===void 0){yo=window,Ar=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;bo=Ie(t,"firstChild").get,wo=Ie(t,"nextSibling").get,ja(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),ja(n)&&(n.__t=void 0),y&&(e.__svelte_meta=null,lu())}}function at(e=""){return document.createTextNode(e)}function Dt(e){return bo.call(e)}function cn(e){return wo.call(e)}function je(e,t){return Dt(e)}function Q(e,t=!1){{var n=Dt(e);return n instanceof Comment&&n.data===""?cn(n):n}}function z(e,t=1,n=!1){let r=e;for(;t--;)r=cn(r);return r}function cu(e){e.textContent=""}function Mo(){return!1}function ko(e,t,n){return document.createElementNS(t??Qa,e,void 0)}function fu(e,t){if(t){const n=document.body;e.autofocus=!0,Je(()=>{document.activeElement===n&&e.focus()})}}function Er(e){var t=E,n=N;me(null),Ee(null);try{return e()}finally{me(t),Ee(n)}}function du(e){N===null&&(E===null&&ll(e),il()),ot&&sl(e)}function hu(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function xe(e,t,n){var r=N;if(y)for(;r!==null&&(r.f&Rn)!==0;)r=r.parent;r!==null&&(r.f&ue)!==0&&(e|=ue);var a={ctx:L,deps:null,nodes:null,f:e|Y|_e,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null};if(y&&(a.component_function=sn),n)try{It(a)}catch(i){throw Z(a),i}else t!==null&&qe(a);var o=a;if(n&&o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&Ft)===0&&(o=o.first,(e&Be)!==0&&(e&Xe)!==0&&o!==null&&(o.f|=Xe)),o!==null&&(o.parent=r,r!==null&&hu(o,r),E!==null&&(E.f&X)!==0&&(e&ht)===0)){var s=E;(s.effects??(s.effects=[])).push(o)}return a}function Cr(){return E!==null&&!Ae}function Pr(e){const t=xe(Tn,null,!1);return O(t,H),t.teardown=e,t}function pu(e){du("$effect"),y&&dt(e,"name",{value:"$effect"});var t=N.f,n=!E&&(t&Me)!==0&&(t&pt)===0;if(n){var r=L;(r.e??(r.e=[])).push(e)}else return So(e)}function So(e){return xe(rn|tl,e,!1)}function _u(e){et.ensure();const t=xe(ht|Ft,e,!0);return(n={})=>new Promise(r=>{n.outro?gt(t,()=>{Z(t),r(void 0)}):(Z(t),r(void 0))})}function qo(e){return xe(rn,e,!1)}function vu(e){return xe(Ln|Ft,e,!0)}function mu(e,t=0){return xe(Tn|t,e,!0)}function In(e,t=[],n=[],r=[]){co(r,t,n,a=>{xe(Tn,()=>e(...a.map(x)),!0)})}function fn(e,t=0){var n=xe(Be|t,e,!0);return y&&(n.dev_stack=Tt),n}function Ao(e,t=0){var n=xe(hr|t,e,!0);return y&&(n.dev_stack=Tt),n}function oe(e){return xe(Me|Ft,e,!0)}function Eo(e){var t=e.teardown;if(t!==null){const n=ot,r=E;xo(!0),me(null);try{t.call(null)}finally{xo(n),me(r)}}}function Nr(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const a=n.ac;a!==null&&Er(()=>{a.abort(_t)});var r=n.next;(n.f&ht)!==0?n.parent=null:Z(n,t),n=r}}function gu(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&Me)===0&&Z(t),t=n}}function Z(e,t=!0){var n=!1;(t||(e.f&Wa)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(yu(e.nodes.start,e.nodes.end),n=!0),Nr(e,t&&!n),hn(e,0),O(e,Ve);var r=e.nodes&&e.nodes.t;if(r!==null)for(const o of r)o.stop();Eo(e);var a=e.parent;a!==null&&a.first!==null&&Co(e),y&&(e.component_function=null),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function yu(e,t){for(;e!==null;){var n=e===t?null:cn(e);e.remove(),e=n}}function Co(e){var t=e.parent,n=e.prev,r=e.next;n!==null&&(n.next=r),r!==null&&(r.prev=n),t!==null&&(t.first===e&&(t.first=r),t.last===e&&(t.last=n))}function gt(e,t,n=!0){var r=[];Po(e,r,!0);var a=()=>{n&&Z(e),t&&t()},o=r.length;if(o>0){var s=()=>--o||a();for(var i of r)i.out(s)}else a()}function Po(e,t,n){if((e.f&ue)===0){e.f^=ue;var r=e.nodes&&e.nodes.t;if(r!==null)for(const i of r)(i.is_global||n)&&t.push(i);for(var a=e.first;a!==null;){var o=a.next,s=(a.f&Xe)!==0||(a.f&Me)!==0&&(e.f&Be)!==0;Po(a,t,s?n:!1),a=o}}}function Fr(e){No(e,!0)}function No(e,t){if((e.f&ue)!==0){e.f^=ue,(e.f&H)===0&&(O(e,Y),qe(e));for(var n=e.first;n!==null;){var r=n.next,a=(n.f&Xe)!==0||(n.f&Me)!==0;No(n,a?t:!1),n=r}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function Fo(e,t){if(e.nodes)for(var n=e.nodes.start,r=e.nodes.end;n!==null;){var a=n===r?null:cn(n);t.append(n),n=a}}let Bn=!1,ot=!1;function xo(e){ot=e}let E=null,Ae=!1;function me(e){E=e}let N=null;function Ee(e){N=e}let ge=null;function To(e){E!==null&&(ge===null?ge=[e]:ge.push(e))}let se=null,ce=0,ye=null;function bu(e){ye=e}let Ro=1,yt=0,bt=yt;function Lo(e){bt=e}function $o(){return++Ro}function dn(e){var t=e.f;if((t&Y)!==0)return!0;if(t&X&&(e.f&=~Ke),(t&ke)!==0){for(var n=e.deps,r=n.length,a=0;a<r;a++){var o=n[a];if(dn(o)&&po(o),o.wv>e.wv)return!0}(t&_e)!==0&&K===null&&O(e,H)}return!1}function Oo(e,t,n=!0){var r=e.reactions;if(r!==null&&!(ge!==null&&ft.call(ge,e)))for(var a=0;a<r.length;a++){var o=r[a];(o.f&X)!==0?Oo(o,t,!1):t===o&&(n?O(o,Y):(o.f&H)!==0&&O(o,ke),qe(o))}}function xr(e){var m;var t=se,n=ce,r=ye,a=E,o=ge,s=L,i=Ae,l=bt,c=e.f;se=null,ce=0,ye=null,E=(c&(Me|ht))===0?e:null,ge=null,xt(e.ctx),Ae=!1,bt=++yt,e.ac!==null&&(Er(()=>{e.ac.abort(_t)}),e.ac=null);try{e.f|=_r;var p=e.fn,u=p();e.f|=pt;var d=e.deps,v=F==null?void 0:F.is_fork;if(se!==null){var f;if(v||hn(e,ce),d!==null&&ce>0)for(d.length=ce+se.length,f=0;f<se.length;f++)d[ce+f]=se[f];else e.deps=d=se;if(Cr()&&(e.f&_e)!==0)for(f=ce;f<d.length;f++)((m=d[f]).reactions??(m.reactions=[])).push(e)}else!v&&d!==null&&ce<d.length&&(hn(e,ce),d.length=ce);if(to()&&ye!==null&&!Ae&&d!==null&&(e.f&(X|ke|Y))===0)for(f=0;f<ye.length;f++)Oo(ye[f],e);if(a!==null&&a!==e){if(yt++,a.deps!==null)for(let w=0;w<n;w+=1)a.deps[w].rv=yt;if(t!==null)for(const w of t)w.rv=yt;ye!==null&&(r===null?r=ye:r.push(...ye))}return(e.f&Qe)!==0&&(e.f^=Qe),u}catch(w){return no(w)}finally{e.f^=_r,se=t,ce=n,ye=r,E=a,ge=o,xt(s),Ae=i,bt=l}}function wu(e,t){let n=t.reactions;if(n!==null){var r=Ki.call(n,e);if(r!==-1){var a=n.length-1;a===0?n=t.reactions=null:(n[r]=n[a],n.pop())}}if(n===null&&(t.f&X)!==0&&(se===null||!ft.call(se,t))){var o=t;(o.f&_e)!==0&&(o.f^=_e,o.f&=~Ke),gr(o),tu(o),hn(o,0)}}function hn(e,t){var n=e.deps;if(n!==null)for(var r=t;r<n.length;r++)wu(e,n[r])}function It(e){var t=e.f;if((t&Ve)===0){O(e,H);var n=N,r=Bn;if(N=e,Bn=!0,y){var a=sn;eo(e.component_function);var o=Tt;$n(e.dev_stack??Tt)}try{(t&(Be|hr))!==0?gu(e):Nr(e),Eo(e);var s=xr(e);e.teardown=typeof s=="function"?s:null,e.wv=Ro;var i;y&&Ll&&(e.f&Y)!==0&&e.deps}finally{Bn=r,N=n,y&&(eo(a),$n(o))}}}function x(e){var t=e.f,n=(t&X)!==0;if(E!==null&&!Ae){var r=N!==null&&(N.f&Ve)!==0;if(!r&&(ge===null||!ft.call(ge,e))){var a=E.deps;if((E.f&_r)!==0)e.rv<yt&&(e.rv=yt,se===null&&a!==null&&a[ce]===e?ce++:se===null?se=[e]:se.push(e));else{(E.deps??(E.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[E]:ft.call(o,E)||o.push(E)}}}if(y&&Jl.delete(e),ot&&tt.has(e))return tt.get(e);if(n){var s=e;if(ot){var i=s.v;return((s.f&H)===0&&s.reactions!==null||Io(s))&&(i=Sr(s)),tt.set(s,i),i}var l=(s.f&_e)===0&&!Ae&&E!==null&&(Bn||(E.f&_e)!==0),c=(s.f&pt)===0;dn(s)&&(l&&(s.f|=_e),po(s)),l&&!c&&(_o(s),Do(s))}if(K!=null&&K.has(e))return K.get(e);if((e.f&Qe)!==0)throw e.v;return e.v}function Do(e){if(e.f|=_e,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&X)!==0&&(t.f&_e)===0&&(_o(t),Do(t))}function Io(e){if(e.v===W)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(tt.has(t)||(t.f&X)!==0&&Io(t))return!0;return!1}function Tr(e){var t=Ae;try{return Ae=!0,e()}finally{Ae=t}}function Mu(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const ku=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Su(e){return ku.includes(e)}const qu={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Au(e){return e=e.toLowerCase(),qu[e]??e}const Eu=["touchstart","touchmove"];function Cu(e){return Eu.includes(e)}const wt=Symbol("events"),Bo=new Set,Rr=new Set;function Pu(e,t,n,r={}){function a(o){if(r.capture||Lr.call(t,o),!o.cancelBubble)return Er(()=>n==null?void 0:n.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Je(()=>{t.addEventListener(e,a,r)}):t.addEventListener(e,a,r),a}function pn(e,t,n){(t[wt]??(t[wt]={}))[e]=n}function Vo(e){for(var t=0;t<e.length;t++)Bo.add(e[t]);for(var n of Rr)n(e)}let jo=null;function Lr(e){var w,g;var t=this,n=t.ownerDocument,r=e.type,a=((w=e.composedPath)==null?void 0:w.call(e))||[],o=a[0]||e.target;jo=e;var s=0,i=jo===e&&e[wt];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[wt]=t;return}var c=a.indexOf(t);if(c===-1)return;l<=c&&(s=l)}if(o=a[s]||e.target,o!==t){dt(e,"currentTarget",{configurable:!0,get(){return o||n}});var p=E,u=N;me(null),Ee(null);try{for(var d,v=[];o!==null;){var f=o.assignedSlot||o.parentNode||o.host||null;try{var m=(g=o[wt])==null?void 0:g[r];m!=null&&(!o.disabled||e.target===o)&&m.call(o,e)}catch(S){d?v.push(S):d=S}if(e.cancelBubble||f===t||f===null)break;o=f}if(d){for(let S of v)queueMicrotask(()=>{throw S});throw d}}finally{e[wt]=t,delete e.currentTarget,me(p),Ee(u)}}}const $r=((ds=globalThis==null?void 0:globalThis.window)==null?void 0:ds.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Nu(e){return($r==null?void 0:$r.createHTML(e))??e}function Ho(e){var t=ko("template");return t.innerHTML=Nu(e.replaceAll("<!>","<!---->")),t.content}function _n(e,t){var n=N;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function Vn(e,t){var n=(t&ql)!==0,r=(t&Al)!==0,a,o=!e.startsWith("<!>");return()=>{a===void 0&&(a=Ho(o?e:"<!>"+e),n||(a=Dt(a)));var s=r||Ar?document.importNode(a,!0):a.cloneNode(!0);if(n){var i=Dt(s),l=s.lastChild;_n(i,l)}else _n(s,s);return s}}function Fu(e,t,n="svg"){var r=!e.startsWith("<!>"),a=`<${n}>${r?e:"<!>"+e}</${n}>`,o;return()=>{if(!o){var s=Ho(a),i=Dt(s);o=Dt(i)}var l=o.cloneNode(!0);return _n(l,l),l}}function xu(e,t){return Fu(e,t,"svg")}function ee(){var e=document.createDocumentFragment(),t=document.createComment(""),n=at();return e.append(t,n),_n(t,n),e}function D(e,t){e!==null&&e.before(t)}function Tu(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function Ru(e,t){return Lu(e,t)}const jn=new Map;function Lu(e,{target:t,anchor:n,props:r={},events:a,context:o,intro:s=!0,transformError:i}){uu();var l=void 0,c=_u(()=>{var p=n??t.appendChild(at());Yl(p,{pending:()=>{}},v=>{B({});var f=L;o&&(f.c=o),a&&(r.$$events=a),l=e(v,r)||{},V()},i);var u=new Set,d=v=>{for(var f=0;f<v.length;f++){var m=v[f];if(!u.has(m)){u.add(m);var w=Cu(m);for(const b of[t,document]){var g=jn.get(b);g===void 0&&(g=new Map,jn.set(b,g));var S=g.get(m);S===void 0?(b.addEventListener(m,Lr,{passive:w}),g.set(m,1)):g.set(m,S+1)}}}};return d(xn(Bo)),Rr.add(d),()=>{var w;for(var v of u)for(const g of[t,document]){var f=jn.get(g),m=f.get(v);--m==0?(g.removeEventListener(v,Lr),f.delete(v),f.size===0&&jn.delete(g)):f.set(v,m)}Rr.delete(d),p!==n&&((w=p.parentNode)==null||w.removeChild(p))}});return Or.set(l,c),l}let Or=new WeakMap;function Wo(e,t){const n=Or.get(e);return n?(Or.delete(e),n(t)):(y&&(Ze in e?xl():Nl()),Promise.resolve())}class Dr{constructor(t,n=!0){Oe(this,"anchor");P(this,Pe,new Map);P(this,$e,new Map);P(this,he,new Map);P(this,At,new Set);P(this,kn,!0);P(this,Sn,()=>{var t=F;if(h(this,Pe).has(t)){var n=h(this,Pe).get(t),r=h(this,$e).get(n);if(r)Fr(r),h(this,At).delete(n);else{var a=h(this,he).get(n);a&&(h(this,$e).set(n,a.effect),h(this,he).delete(n),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),r=a.effect)}for(const[o,s]of h(this,Pe)){if(h(this,Pe).delete(o),o===t)break;const i=h(this,he).get(s);i&&(Z(i.effect),h(this,he).delete(s))}for(const[o,s]of h(this,$e)){if(o===n||h(this,At).has(o))continue;const i=()=>{if(Array.from(h(this,Pe).values()).includes(o)){var c=document.createDocumentFragment();Fo(s,c),c.append(at()),h(this,he).set(o,{effect:s,fragment:c})}else Z(s);h(this,At).delete(o),h(this,$e).delete(o)};h(this,kn)||!r?(h(this,At).add(o),gt(s,i,!1)):i()}}});P(this,Gn,t=>{h(this,Pe).delete(t);const n=Array.from(h(this,Pe).values());for(const[r,a]of h(this,he))n.includes(r)||(Z(a.effect),h(this,he).delete(r))});this.anchor=t,A(this,kn,n)}ensure(t,n){var r=F,a=Mo();if(n&&!h(this,$e).has(t)&&!h(this,he).has(t))if(a){var o=document.createDocumentFragment(),s=at();o.append(s),h(this,he).set(t,{effect:oe(()=>n(s)),fragment:o})}else h(this,$e).set(t,oe(()=>n(this.anchor)));if(h(this,Pe).set(r,t),a){for(const[i,l]of h(this,$e))i===t?r.unskip_effect(l):r.skip_effect(l);for(const[i,l]of h(this,he))i===t?r.unskip_effect(l.effect):r.skip_effect(l.effect);r.oncommit(h(this,Sn)),r.ondiscard(h(this,Gn))}else h(this,Sn).call(this)}}Pe=new WeakMap,$e=new WeakMap,he=new WeakMap,At=new WeakMap,kn=new WeakMap,Sn=new WeakMap,Gn=new WeakMap;function Ir(e,t,n=!1){var r=new Dr(e),a=n?Xe:0;function o(s,i){r.ensure(s,i)}fn(()=>{var s=!1;t((i,l=0)=>{s=!0,o(l,i)}),s||o(!1,null)},a)}function $u(e,t){return t}function Ou(e,t,n){for(var r=[],a=t.length,o,s=t.length,i=0;i<a;i++){let u=t[i];gt(u,()=>{if(o){if(o.pending.delete(u),o.done.add(u),o.pending.size===0){var d=e.outrogroups;Br(xn(o.done)),d.delete(o),d.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var l=r.length===0&&n!==null;if(l){var c=n,p=c.parentNode;cu(p),p.append(c),e.items.clear()}Br(t,!l)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function Br(e,t=!0){for(var n=0;n<e.length;n++)Z(e[n],t)}var Go;function Uo(e,t,n,r,a,o=null){var s=e,i=new Map,l=null,c=fo(()=>{var m=n();return dr(m)?m:m==null?[]:xn(m)}),p,u=!0;function d(){f.fallback=l,Du(f,p,s,t,r),l!==null&&(p.length===0?(l.f&Ye)===0?Fr(l):(l.f^=Ye,mn(l,null,s)):gt(l,()=>{l=null}))}var v=fn(()=>{p=x(c);for(var m=p.length,w=new Set,g=F,S=Mo(),b=0;b<m;b+=1){var k=p[b],_=r(k,b);if(y){var J=r(k,b);_!==J&&ol(String(b),String(_),String(J))}var C=u?null:i.get(_);C?(C.v&&$t(C.v,k),C.i&&$t(C.i,b),S&&g.unskip_effect(C.e)):(C=Iu(i,u?s:Go??(Go=at()),k,_,b,a,t,n),u||(C.e.f|=Ye),i.set(_,C)),w.add(_)}if(m===0&&o&&!l&&(u?l=oe(()=>o(s)):(l=oe(()=>o(Go??(Go=at()))),l.f|=Ye)),m>w.size&&(y?Bu(p,r):Ka("","","")),!u)if(S){for(const[Ge,pe]of i)w.has(Ge)||g.skip_effect(pe.e);g.oncommit(d),g.ondiscard(()=>{})}else d();x(c)}),f={effect:v,items:i,outrogroups:null,fallback:l};u=!1}function vn(e){for(;e!==null&&(e.f&Me)===0;)e=e.next;return e}function Du(e,t,n,r,a){var Ge;var o=t.length,s=e.items,i=vn(e.effect.first),l,c=null,p=[],u=[],d,v,f,m;for(m=0;m<o;m+=1){if(d=t[m],v=a(d,m),f=s.get(v).e,e.outrogroups!==null)for(const pe of e.outrogroups)pe.pending.delete(f),pe.done.delete(f);if((f.f&Ye)!==0)if(f.f^=Ye,f===i)mn(f,null,n);else{var w=c?c.next:i;f===e.effect.last&&(e.effect.last=f.prev),f.prev&&(f.prev.next=f.next),f.next&&(f.next.prev=f.prev),st(e,c,f),st(e,f,w),mn(f,w,n),c=f,p=[],u=[],i=vn(c.next);continue}if((f.f&ue)!==0&&Fr(f),f!==i){if(l!==void 0&&l.has(f)){if(p.length<u.length){var g=u[0],S;c=g.prev;var b=p[0],k=p[p.length-1];for(S=0;S<p.length;S+=1)mn(p[S],g,n);for(S=0;S<u.length;S+=1)l.delete(u[S]);st(e,b.prev,k.next),st(e,c,b),st(e,k,g),i=g,c=k,m-=1,p=[],u=[]}else l.delete(f),mn(f,i,n),st(e,f.prev,f.next),st(e,f,c===null?e.effect.first:c.next),st(e,c,f),c=f;continue}for(p=[],u=[];i!==null&&i!==f;)(l??(l=new Set)).add(i),u.push(i),i=vn(i.next);if(i===null)continue}(f.f&Ye)===0&&p.push(f),c=f,i=vn(f.next)}if(e.outrogroups!==null){for(const pe of e.outrogroups)pe.pending.size===0&&(Br(xn(pe.done)),(Ge=e.outrogroups)==null||Ge.delete(pe));e.outrogroups.size===0&&(e.outrogroups=null)}if(i!==null||l!==void 0){var _=[];if(l!==void 0)for(f of l)(f.f&ue)===0&&_.push(f);for(;i!==null;)(i.f&ue)===0&&i!==e.fallback&&_.push(i),i=vn(i.next);var J=_.length;if(J>0){var C=null;Ou(e,_,C)}}}function Iu(e,t,n,r,a,o,s,i){var l=(s&gl)!==0?(s&bl)===0?ru(n,!1,!1):vt(n):null,c=(s&yl)!==0?vt(a):null;return y&&l&&(l.trace=()=>{i()[(c==null?void 0:c.v)??a]}),{v:l,i:c,e:oe(()=>(o(t,l??n,c??a,i),()=>{e.delete(r)}))}}function mn(e,t,n){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end,o=t&&(t.f&Ye)===0?t.nodes.start:n;r!==null;){var s=cn(r);if(o.before(r),r===a)return;r=s}}function st(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function Bu(e,t){const n=new Map,r=e.length;for(let a=0;a<r;a++){const o=t(e[a],a);if(n.has(o)){const s=String(n.get(o)),i=String(a);let l=String(o);l.startsWith("[object ")&&(l=null),Ka(s,i,l)}n.set(o,a)}}function te(e,t,...n){var r=new Dr(e);fn(()=>{const a=t()??null;y&&a==null&&cl(),r.ensure(a,a&&(o=>a(o,...n)))},Xe)}function Vu(e,t,n,r,a,o){var s=null,i=e,l=new Dr(i,!1);fn(()=>{const c=t()||null;var p=Cl;if(c===null){l.ensure(null,null);return}return l.ensure(c,u=>{if(c){if(s=ko(c,p),_n(s,s),r){var d=s.appendChild(at());r(s,d)}N.nodes.end=s,u.before(s)}}),()=>{}},Xe),Pr(()=>{})}function ju(e,t){var n=void 0,r;Ao(()=>{n!==(n=t())&&(r&&(Z(r),r=null),n&&(r=oe(()=>{qo(()=>n(e))})))})}function Xo(e){var t,n,r="";if(typeof e=="string"||typeof e=="number")r+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(n=Xo(e[t]))&&(r&&(r+=" "),r+=n)}else for(n in e)e[n]&&(r&&(r+=" "),r+=n);return r}function Hu(){for(var e,t,n=0,r="",a=arguments.length;n<a;n++)(e=arguments[n])&&(t=Xo(e))&&(r&&(r+=" "),r+=t);return r}function Yo(e){return typeof e=="object"?Hu(e):e??""}const Ko=[...` 	
\r\f \v\uFEFF`];function Wu(e,t,n){var r=e==null?"":""+e;if(n){for(var a of Object.keys(n))if(n[a])r=r?r+" "+a:a;else if(r.length)for(var o=a.length,s=0;(s=r.indexOf(a,s))>=0;){var i=s+o;(s===0||Ko.includes(r[s-1]))&&(i===r.length||Ko.includes(r[i]))?r=(s===0?"":r.substring(0,s))+r.substring(i+1):s=i}}return r===""?null:r}function Qo(e,t=!1){var n=t?" !important;":";",r="";for(var a of Object.keys(e)){var o=e[a];o!=null&&o!==""&&(r+=" "+a+": "+o+n)}return r}function Vr(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Gu(e,t){if(t){var n="",r,a;if(Array.isArray(t)?(r=t[0],a=t[1]):r=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,i=!1,l=[];r&&l.push(...Object.keys(r).map(Vr)),a&&l.push(...Object.keys(a).map(Vr));var c=0,p=-1;const m=e.length;for(var u=0;u<m;u++){var d=e[u];if(i?d==="/"&&e[u-1]==="*"&&(i=!1):o?o===d&&(o=!1):d==="/"&&e[u+1]==="*"?i=!0:d==='"'||d==="'"?o=d:d==="("?s++:d===")"&&s--,!i&&o===!1&&s===0){if(d===":"&&p===-1)p=u;else if(d===";"||u===m-1){if(p!==-1){var v=Vr(e.substring(c,p).trim());if(!l.includes(v)){d!==";"&&u++;var f=e.substring(c,u).trim();n+=" "+f+";"}}c=u+1,p=-1}}}}return r&&(n+=Qo(r)),a&&(n+=Qo(a,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function Zo(e,t,n,r,a,o){var s=e.__className;if(s!==n||s===void 0){var i=Wu(n,r,o);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=n}else if(o&&a!==o)for(var l in o){var c=!!o[l];(a==null||c!==!!a[l])&&e.classList.toggle(l,c)}return o}function jr(e,t={},n,r){for(var a in n){var o=n[a];t[a]!==o&&(n[a]==null?e.style.removeProperty(a):e.style.setProperty(a,o,r))}}function Uu(e,t,n,r){var a=e.__style;if(a!==t){var o=Gu(t,r);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else r&&(Array.isArray(r)?(jr(e,n==null?void 0:n[0],r[0]),jr(e,n==null?void 0:n[1],r[1],"important")):jr(e,n,r));return r}function Hr(e,t,n=!1){if(e.multiple){if(t==null)return;if(!dr(t))return Fl();for(var r of e.options)r.selected=t.includes(Jo(r));return}for(r of e.options){var a=Jo(r);if(ou(a,t)){r.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function Xu(e){var t=new MutationObserver(()=>{Hr(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Pr(()=>{t.disconnect()})}function Jo(e){return"__value"in e?e.__value:e.value}const gn=Symbol("class"),yn=Symbol("style"),zo=Symbol("is custom element"),es=Symbol("is html"),Yu=Xa?"option":"OPTION",Ku=Xa?"select":"SELECT";function Qu(e,t){var n=Wr(e);n.checked!==(n.checked=t??void 0)&&(e.checked=t)}function Zu(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function q(e,t,n,r){var a=Wr(e);a[t]!==(a[t]=n)&&(t==="loading"&&(e[nl]=n),n==null?e.removeAttribute(t):typeof n!="string"&&rs(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function Ju(e,t,n,r,a=!1,o=!1){var s=Wr(e),i=s[zo],l=!s[es],c=t||{},p=e.nodeName===Yu;for(var u in t)u in n||(n[u]=null);n.class?n.class=Yo(n.class):n[gn]&&(n.class=null),n[yn]&&(n.style??(n.style=null));var d=rs(e);for(const b in n){let k=n[b];if(p&&b==="value"&&k==null){e.value=e.__value="",c[b]=k;continue}if(b==="class"){var v=e.namespaceURI==="http://www.w3.org/1999/xhtml";Zo(e,v,k,r,t==null?void 0:t[gn],n[gn]),c[b]=k,c[gn]=n[gn];continue}if(b==="style"){Uu(e,k,t==null?void 0:t[yn],n[yn]),c[b]=k,c[yn]=n[yn];continue}var f=c[b];if(!(k===f&&!(k===void 0&&e.hasAttribute(b)))){c[b]=k;var m=b[0]+b[1];if(m!=="$$")if(m==="on"){const _={},J="$$"+b;let C=b.slice(2);var w=Su(C);if(Mu(C)&&(C=C.slice(0,-7),_.capture=!0),!w&&f){if(k!=null)continue;e.removeEventListener(C,c[J],_),c[J]=null}if(w)pn(C,e,k),Vo([C]);else if(k!=null){let Ge=function(pe){c[b].call(this,pe)};c[J]=Pu(C,e,Ge,_)}}else if(b==="style")q(e,b,k);else if(b==="autofocus")fu(e,!!k);else if(!i&&(b==="__value"||b==="value"&&k!=null))e.value=e.__value=k;else if(b==="selected"&&p)Zu(e,k);else{var g=b;l||(g=Au(g));var S=g==="defaultValue"||g==="defaultChecked";if(k==null&&!i&&!S)if(s[b]=null,g==="value"||g==="checked"){let _=e;const J=t===void 0;if(g==="value"){let C=_.defaultValue;_.removeAttribute(g),_.defaultValue=C,_.value=_.__value=J?C:null}else{let C=_.defaultChecked;_.removeAttribute(g),_.defaultChecked=C,_.checked=J?C:!1}}else e.removeAttribute(b);else S||d.includes(g)&&(i||typeof k!="string")?(e[g]=k,g in s&&(s[g]=W)):typeof k!="function"&&q(e,g,k)}}}return c}function ts(e,t,n=[],r=[],a=[],o,s=!1,i=!1){co(a,n,r,l=>{var c=void 0,p={},u=e.nodeName===Ku,d=!1;if(Ao(()=>{var f=t(...l.map(x)),m=Ju(e,c,f,o,s,i);d&&u&&"value"in f&&Hr(e,f.value);for(let g of Object.getOwnPropertySymbols(p))f[g]||Z(p[g]);for(let g of Object.getOwnPropertySymbols(f)){var w=f[g];g.description===Pl&&(!c||w!==c[g])&&(p[g]&&Z(p[g]),p[g]=oe(()=>ju(e,()=>w))),m[g]=w}c=m}),u){var v=e;qo(()=>{Hr(v,c.value,!0),Xu(v)})}d=!0})}function Wr(e){return e.__attributes??(e.__attributes={[zo]:e.nodeName.includes("-"),[es]:e.namespaceURI===Qa})}var ns=new Map;function rs(e){var t=e.getAttribute("is")||e.nodeName,n=ns.get(t);if(n)return n;ns.set(t,n=[]);for(var r,a=e,o=Element.prototype;o!==a;){r=Qi(a);for(var s in r)r[s].set&&n.push(s);a=Va(a)}return n}let Hn=!1;function zu(e){var t=Hn;try{return Hn=!1,[e(),Hn]}finally{Hn=t}}const ec={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return y&&dl(`${e.name}.${String(t)}`),!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function ne(e,t,n){return new Proxy(y?{props:e,exclude:t,name:n,other:{},to_proxy:[]}:{props:e,exclude:t},ec)}const tc={get(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(nn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r)return r[t]}},set(e,t,n){let r=e.props.length;for(;r--;){let a=e.props[r];nn(a)&&(a=a());const o=Ie(a,t);if(o&&o.set)return o.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(nn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r){const a=Ie(r,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===Ze||t===Ga)return!1;for(let n of e.props)if(nn(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(nn(n)&&(n=n()),!!n){for(const r in n)t.includes(r)||t.push(r);for(const r of Object.getOwnPropertySymbols(n))t.includes(r)||t.push(r)}return t}};function re(...e){return new Proxy({props:e},tc)}function Bt(e,t,n,r){var S;var a=(n&kl)!==0,o=(n&Sl)!==0,s=r,i=!0,l=()=>(i&&(i=!1,s=o?Tr(r):r),s),c;if(a){var p=Ze in e||Ga in e;c=((S=Ie(e,t))==null?void 0:S.set)??(p&&t in e?b=>e[t]=b:void 0)}var u,d=!1;a?[u,d]=zu(()=>e[t]):u=e[t],u===void 0&&r!==void 0&&(u=l(),c&&(fl(t),c(u)));var v;if(v=()=>{var b=e[t];return b===void 0?l():(i=!0,b)},(n&Ml)===0)return v;if(c){var f=e.$$legacy;return(function(b,k){return arguments.length>0?((!k||f||d)&&c(k?v():b),b):v()})}var m=!1,w=((n&wl)!==0?Dn:fo)(()=>(m=!1,v()));y&&(w.label=t),a&&x(w);var g=N;return(function(b,k){if(arguments.length>0){const _=k?x(w):a?Ot(b):b;return rt(w,_),m=!0,s!==void 0&&(s=_),b}return ot&&m||(g.f&Ve)!==0?w.v:x(w)})}if(y){let e=function(t){if(!(t in globalThis)){let n;Object.defineProperty(globalThis,t,{configurable:!0,get:()=>{if(n!==void 0)return n;hl(t)},set:r=>{n=r}})}};e("$state"),e("$effect"),e("$derived"),e("$inspect"),e("$props"),e("$bindable")}function nc(e){L===null&&Ya("onMount"),pu(()=>{const t=Tr(e);if(typeof t=="function")return t})}const rc="5";typeof window<"u"&&((hs=window.__svelte??(window.__svelte={})).v??(hs.v=new Set)).add(rc);/**
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
 */const ac={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const oc=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const sc=Symbol("lucide-context"),ic=()=>Dl(sc);var lc=xu("<svg><!><!></svg>");function ae(e,t){B(t,!0);const n=ic()??{},r=Bt(t,"color",19,()=>n.color??"currentColor"),a=Bt(t,"size",19,()=>n.size??24),o=Bt(t,"strokeWidth",19,()=>n.strokeWidth??2),s=Bt(t,"absoluteStrokeWidth",19,()=>n.absoluteStrokeWidth??!1),i=Bt(t,"iconNode",19,()=>[]),l=ne(t,["$$slots","$$events","$$legacy","name","color","size","strokeWidth","absoluteStrokeWidth","iconNode","children"]),c=Mr(()=>s()?Number(o())*24/Number(a()):o());var p=lc();ts(p,v=>({...ac,...v,...l,width:a(),height:a(),stroke:r(),"stroke-width":x(c),class:["lucide-icon lucide",n.class,t.name&&`lucide-${t.name}`,t.class]}),[()=>!t.children&&!oc(l)&&{"aria-hidden":"true"}]);var u=je(p);Uo(u,17,i,$u,(v,f)=>{var m=Mr(()=>el(x(f),2));let w=()=>x(m)[0],g=()=>x(m)[1];var S=ee(),b=Q(S);Vu(b,w,!0,(k,_)=>{ts(k,()=>({...g()}))}),D(v,S)});var d=z(u);te(d,()=>t.children??U),D(e,p),V()}function uc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];ae(e,re({name:"chart-line"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function cc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 12 18z"}],["path",{d:"M2 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 2 18z"}]];ae(e,re({name:"fast-forward"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function fc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]];ae(e,re({name:"folder-open"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function dc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["rect",{x:"14",y:"3",width:"5",height:"18",rx:"1"}],["rect",{x:"5",y:"3",width:"5",height:"18",rx:"1"}]];ae(e,re({name:"pause"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function hc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"}]];ae(e,re({name:"play"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function pc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];ae(e,re({name:"refresh-cw"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function _c(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 12 18z"}],["path",{d:"M22 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 22 18z"}]];ae(e,re({name:"rewind"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function vc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]];ae(e,re({name:"scissors"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function mc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];ae(e,re({name:"sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function gc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]];ae(e,re({name:"timer-reset"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function yc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"}]];ae(e,re({name:"undo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function bc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}]];ae(e,re({name:"volume-1"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function wc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}],["path",{d:"M19.364 18.364a9 9 0 0 0 0-12.728"}]];ae(e,re({name:"volume-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function Mc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]];ae(e,re({name:"volume-x"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}function kc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72"}],["path",{d:"m14 7 3 3"}],["path",{d:"M5 6v4"}],["path",{d:"M19 14v4"}],["path",{d:"M10 2v2"}],["path",{d:"M7 8H3"}],["path",{d:"M21 16h-4"}],["path",{d:"M11 3H9"}]];ae(e,re({name:"wand-sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),D(a,s)},$$slots:{default:!0}})),V()}var Sc=Vn('<span aria-hidden="true"><!></span>');function as(e,t){B(t,!0);const n=Bt(t,"className",3,""),r=Mr(()=>["aqe-button-icon",n()].filter(Boolean).join(" "));var a=Sc(),o=je(a);{var s=_=>{uc(_,{size:14,strokeWidth:2})},i=_=>{cc(_,{size:14,strokeWidth:2})},l=_=>{fc(_,{size:14,strokeWidth:2})},c=_=>{dc(_,{size:14,strokeWidth:2})},p=_=>{hc(_,{size:14,strokeWidth:2})},u=_=>{pc(_,{size:14,strokeWidth:2})},d=_=>{_c(_,{size:14,strokeWidth:2})},v=_=>{vc(_,{size:14,strokeWidth:2})},f=_=>{mc(_,{size:14,strokeWidth:2})},m=_=>{gc(_,{size:14,strokeWidth:2})},w=_=>{yc(_,{size:14,strokeWidth:2})},g=_=>{bc(_,{size:14,strokeWidth:2})},S=_=>{wc(_,{size:14,strokeWidth:2})},b=_=>{Mc(_,{size:14,strokeWidth:2})},k=_=>{kc(_,{size:14,strokeWidth:2})};Ir(o,_=>{t.icon==="chart-line"?_(s):t.icon==="fast-forward"?_(i,1):t.icon==="folder-open"?_(l,2):t.icon==="pause"?_(c,3):t.icon==="play"?_(p,4):t.icon==="refresh-cw"?_(u,5):t.icon==="rewind"?_(d,6):t.icon==="scissors"?_(v,7):t.icon==="sparkles"?_(f,8):t.icon==="timer-reset"?_(m,9):t.icon==="undo-2"?_(w,10):t.icon==="volume-1"?_(g,11):t.icon==="volume-2"?_(S,12):t.icon==="volume-x"?_(b,13):t.icon==="wand-sparkles"&&_(k,14)})}In(()=>Zo(a,1,Yo(x(r)))),D(e,a),V()}var qc=Vn('<label class="aqe-repeat-toggle" title="Repeat selected region, or the whole graph when no region is selected."><input class="aqe-repeat-checkbox" type="checkbox"/> <span>Repeat</span></label>'),Ac=Vn('<button type="button" class="aqe-button"><!> <!> <span class="aqe-button-label"> </span></button> <!>',1),Ec=Vn('<div class="aqe-controls"><!> <span class="aqe-status"></span> <div class="aqe-visualizer" data-anchor-ms="0" data-cursor-ms="0" data-progress-ms="0" data-graph-active="false" data-graph-busy="false" data-has-track="false" data-playback-state="stopped" data-playback-engine="" data-playback-start-ms="0" data-playback-end-ms="0" data-playback-region-mode="full" data-resume-requires-restart="false" data-selection-active="false" data-selection-start-ms="" data-selection-end-ms="" data-selection-draft-active="false" data-selection-draft-start-ms="" data-selection-draft-end-ms="" hidden=""><audio class="aqe-audio-clock" preload="metadata" hidden=""></audio> <svg class="aqe-visualizer-svg" role="img" aria-label="Audio pitch and intensity visualization"><rect class="aqe-selection" width="0" visibility="hidden"></rect><path class="aqe-intensity" d=""></path><g class="aqe-pitch"></g><g class="aqe-labels"></g><g class="aqe-x-axis"></g><line class="aqe-selection-edge aqe-selection-start" visibility="hidden"></line><line class="aqe-selection-edge aqe-selection-end" visibility="hidden"></line><line class="aqe-cursor"></line></svg> <div class="aqe-visualizer-meta"><span class="aqe-spinner" hidden="" aria-hidden="true"></span> <span class="aqe-cursor-label">0 ms</span> <span class="aqe-visualizer-status"></span></div></div></div>');function Cc(e,t){var b;B(t,!0),nc(()=>{const k=$(t.target.ord);k&&(Mi(k),xi(k),Ai(k))});var n=Ec(),r=je(n);Uo(r,17,()=>T,k=>k.command,(k,_)=>{var J=Ac(),C=Q(J),Ge=je(C);as(Ge,{className:"aqe-button-icon-default",get icon(){return x(_).icon}});var pe=z(Ge,2);{var Yc=Ne=>{as(Ne,{className:"aqe-button-icon-active",get icon(){return x(_).activeIcon}})};Ir(pe,Ne=>{x(_).activeIcon&&Ne(Yc)})}var Kc=z(pe,2),Qc=je(Kc),Zc=z(C,2);{var Jc=Ne=>{var _s;var ps=qc(),Qr=je(ps);Qu(Qr,((_s=window.__AQE_EDITOR_CONFIG__)==null?void 0:_s.repeatPlaybackByDefault)===!0),In(()=>q(Qr,"data-testid",`aqe-repeat-${t.target.ord}`)),pn("change",Qr,zc=>Ci(t.target.ord,zc.currentTarget.checked)),D(Ne,ps)};Ir(Zc,Ne=>{x(_).command==="aqe:play"&&Ne(Jc)})}In(Ne=>{q(C,"data-aqe-command",x(_).command),q(C,"data-aqe-button-state",x(_).command==="aqe:play"?"play":x(_).command==="aqe:analyze"?"graph":"default"),q(C,"data-testid",Ne),q(C,"title",x(_).title),Tu(Qc,x(_).label)},[()=>qn(t.target.ord,x(_).command)]),pn("mousedown",C,Ne=>Ne.preventDefault()),pn("click",C,()=>wi(x(_).command,t.target.node,t.target.ord)),D(k,J)});var a=z(r,2),o=z(a,2);q(o,"data-repeat-enabled",((b=window.__AQE_EDITOR_CONFIG__)==null?void 0:b.repeatPlaybackByDefault)===!0?"true":"false");var s=je(o),i=z(s,2),l=je(i),c=z(l),p=z(c),u=z(p,2),d=z(u),v=z(d),f=z(v),m=z(i,2),w=je(m),g=z(w,2),S=z(g,2);In(()=>{q(n,"data-aqe-field-ord",t.target.ord),q(n,"data-aqe-source-filename",t.target.sourceFilename),q(n,"data-testid",`aqe-controls-${t.target.ord}`),q(a,"data-testid",`aqe-status-${t.target.ord}`),q(o,"data-aqe-field-ord",t.target.ord),q(o,"data-testid",`aqe-graph-${t.target.ord}`),q(s,"data-testid",`aqe-audio-clock-${t.target.ord}`),q(i,"data-testid",`aqe-graph-svg-${t.target.ord}`),q(i,"viewBox",`0 0 ${M.width} ${M.height}`),q(l,"data-testid",`aqe-selection-${t.target.ord}`),q(l,"x",M.left),q(l,"y",M.top),q(l,"height",M.height-M.top-M.bottom),q(c,"data-testid",`aqe-intensity-${t.target.ord}`),q(p,"data-testid",`aqe-pitch-${t.target.ord}`),q(u,"data-testid",`aqe-x-axis-${t.target.ord}`),q(d,"data-testid",`aqe-selection-start-${t.target.ord}`),q(d,"x1",M.left),q(d,"x2",M.left),q(d,"y1",M.top),q(d,"y2",M.height-M.bottom),q(v,"data-testid",`aqe-selection-end-${t.target.ord}`),q(v,"x1",M.left),q(v,"x2",M.left),q(v,"y1",M.top),q(v,"y2",M.height-M.bottom),q(f,"data-testid",`aqe-cursor-${t.target.ord}`),q(f,"x1",M.left),q(f,"x2",M.left),q(f,"y1",M.top),q(f,"y2",M.height-M.bottom),q(w,"data-testid",`aqe-graph-spinner-${t.target.ord}`),q(g,"data-testid",`aqe-progress-label-${t.target.ord}`),q(S,"data-testid",`aqe-graph-status-${t.target.ord}`)}),pn("pointerdown",i,k=>$i(k,t.target.ord)),D(e,n),V()}Vo(["mousedown","click","change","pointerdown"]);const Vt=new Map;function Pc(e){const t=Vt.get(e.ord);if(t){if(document.body.contains(t.host)||os(e,t.host),Gr(e.ord,t.host),!e.sourceFilename||t.sourceFilename===e.sourceFilename)return t;const o=$(e.ord);if((o==null?void 0:o.dataset.graphBusy)==="true"||(o==null?void 0:o.dataset.hasTrack)==="true"){const s=o.dataset.sourceFilename||e.sourceFilename;t.sourceFilename=s;const i=document.querySelector(`.aqe-controls[data-aqe-field-ord="${e.ord}"]`);return i&&(i.dataset.aqeSourceFilename=s),Gr(e.ord,t.host),t}}Nc(e.ord);const n=document.createElement("div");n.className="aqe-mount-host",os(e,n);const a={component:Ru(Cc,{target:n,props:{target:e}}),host:n,ord:e.ord,sourceFilename:e.sourceFilename};return Vt.set(e.ord,a),Gr(e.ord,n),a}function Nc(e){const t=Vt.get(e);t&&(Wo(t.component),t.host.remove(),Vt.delete(e)),document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>n.remove())}function Fc(){for(const e of Vt.values())Wo(e.component),e.host.remove();Vt.clear(),xc()}function os(e,t){const n=e.node.closest(".field-container")||e.node.closest(".field")||e.node.parentElement||e.node;n.parentElement?n.after(t):e.node.after(t)}function Gr(e,t){document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>{t.contains(n)||n.remove()}),document.querySelectorAll(".aqe-mount-host").forEach(n=>{n!==t&&!n.querySelector(".aqe-controls")&&n.remove()})}function xc(){document.querySelectorAll(".aqe-mount-host").forEach(e=>e.remove()),document.querySelectorAll(".aqe-controls").forEach(e=>e.remove())}function Tc(){window.__aqeGraphStateForTest=Oc,window.__aqeInstallAudioPlaybackTestDriverForTest=Rc,window.__aqeSetCursorByClientXForTest=$c,window.__aqeSetCursorForTest=Lc}function Rc(e){const t=$(e),n=we(t);return!t||!n?!1:(n.__aqeTestDriverInstalled=!0,n.pause=function(){n.__aqeTestPlaying=!1,n.__aqeTestFrame&&(window.cancelAnimationFrame(n.__aqeTestFrame),n.__aqeTestFrame=null)},n.play=function(){n.__aqeTestPlaying=!0,n.__aqeTestLastNow=performance.now();const a=()=>{if(!n.__aqeTestPlaying)return;const o=performance.now(),s=Number(t.dataset.durationMs||"0")/1e3,i=Math.max(0,(o-Number(n.__aqeTestLastNow||o))/1e3);if(n.__aqeTestLastNow=o,n.currentTime=Math.min(s,(Number(n.currentTime)||0)+i),s&&n.currentTime>=s){n.__aqeTestPlaying=!1,n.dispatchEvent(new Event("ended"));return}n.__aqeTestFrame=window.requestAnimationFrame(a)};return n.__aqeTestFrame=window.requestAnimationFrame(a),Promise.resolve()},!0)}function Lc(e,t,n){const r=$(e);return r?(r.hidden=!1,r.dataset.graphActive="true",ut(r,t,!!n),!0):!1}function $c(e,t,n){var i;const r=$(e),a=(r==null?void 0:r.querySelector(".aqe-visualizer-svg"))??null;if(!r||!a)return null;const o=Number(r.dataset.durationMs||"0"),s=Jt({clientX:t},a,o);return ut(r,s,!!n),{cursorMs:Number(r.dataset.cursorMs||"0"),cursorX:Number(((i=r.querySelector(".aqe-cursor"))==null?void 0:i.getAttribute("x1"))||"0"),bounds:ya(a)}}function Oc(e){var l,c,p,u;const t=$(e),n=aa(e),r=oa(e);if(!t)return null;const a=An().flatMap(d=>Array.from(d.querySelectorAll(".aqe-button-icon svg"))),o=we(t),s=Na(t),i=Fa(t);return{active:t.dataset.graphActive==="true",busy:t.dataset.graphBusy==="true",hidden:!!t.hidden,hasTrack:t.dataset.hasTrack==="true",durationMs:Number(t.dataset.durationMs||"0"),anchorMs:Number(t.dataset.anchorMs||"0"),cursorMs:Number(t.dataset.cursorMs||"0"),progressMs:Number(t.dataset.progressMs||"0"),sourceFilename:t.dataset.sourceFilename||"",graphButtonLabel:ss(n),graphButtonState:(n==null?void 0:n.dataset.aqeButtonState)||"",playButtonLabel:ss(r),playButtonState:(r==null?void 0:r.dataset.aqeButtonState)||"",playbackState:Dc(t),selectionActive:s!==null,selectionStartMs:(s==null?void 0:s.startMs)??null,selectionEndMs:(s==null?void 0:s.endMs)??null,selectionDraftActive:i!==null,selectionDraftStartMs:(i==null?void 0:i.startMs)??null,selectionDraftEndMs:(i==null?void 0:i.endMs)??null,repeatEnabled:t.dataset.repeatEnabled==="true",repeatCheckboxDisabled:!!((l=sa(e))!=null&&l.disabled),playbackStartMs:Number(t.dataset.playbackStartMs||"0"),playbackEndMs:Number(t.dataset.playbackEndMs||"0"),playbackRegionMode:t.dataset.playbackRegionMode==="selection"?"selection":"full",resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true",audioClockSrc:o&&o.getAttribute("src")||"",audioClockCurrentMs:o?Math.round((Number(o.currentTime)||0)*1e3):0,audioClockReady:!!(o&&t.__aqeAudioClockAvailable),audioClockFallback:!!t.__aqeAudioClockFallback,audioClockMuted:!!(o&&o.muted),audioPlaybackTestDriver:!!(o&&o.__aqeTestDriverInstalled),playbackEngine:tn(t),progressClockMode:Ic(t),xAxisLabels:Array.from(t.querySelectorAll(".aqe-x-label")).map(d=>d.textContent||""),pitchPaths:t.querySelectorAll(".aqe-pitch-path").length,intensity:((c=t.querySelector(".aqe-intensity"))==null?void 0:c.getAttribute("d"))||"",cursorX:Number(((p=t.querySelector(".aqe-cursor"))==null?void 0:p.getAttribute("x1"))||"0"),spinnerVisible:t.querySelector(".aqe-spinner")?!((u=t.querySelector(".aqe-spinner"))!=null&&u.hidden):!1,allButtonsDisabled:An().every(d=>d.disabled),anyButtonDisabled:An().some(d=>d.disabled),buttonIconCount:a.length,buttonIconStrokeValues:a.map(d=>d.getAttribute("stroke")||getComputedStyle(d).stroke||"")}}function Dc(e){const t=e.dataset.playbackState;return ca(t)?t:"stopped"}function Ic(e){const t=e.dataset.progressClockMode;return t==="audio"||t==="manual"||t==="stopped"?t:"stopped"}function ss(e){var t;return((t=e==null?void 0:e.querySelector(".aqe-button-label"))==null?void 0:t.textContent)||(e==null?void 0:e.textContent)||""}function Bc(){window.__aqeSetBusy=Fn,window.__aqeSetStatus=Pa,window.__aqeSetVisualizer=Di,window.__aqeSetVisualizerStatus=Ii,window.__aqeResetGraphAfterEdit=Oi,window.__aqeSetPlaybackState=Wi,window.__aqeGetPlaybackRequest=Gi,window.__aqeStopEditorPlayback=Ui,window.__aqeGetCursorMs=Xi,window.__aqeGetCursorIntent=Yi,window.__aqePrepareForNewNote=Ra,window.__aqePopFrontendLog=ws,Tc()}const Vc=/\[sound:([^\]]+)\]/i,jc=/\.(mp3|wav|ogg)$/i;let bn=[];function Hc(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){is(),window.__AQE_EDITOR_CONFIG__=e,Bc(),Ra(),window.__aqeEditorDispose=is,le.info("editor runtime initialized",{audioFieldIndices:e.audioFieldIndices});const t=()=>Wc(e);window.__aqeScan=t,Xr(t,0),Xr(t,250),Xr(t,1e3)}function is(){bn.forEach(e=>window.clearTimeout(e)),bn=[],Fc()}function Wc(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){if(e.audioFieldIndices.length){const n=Uc(e.audioFieldIndices);n.forEach(r=>ls(r)),le.debug("scan mounted explicit fields",{count:n.length}),ur();return}let t=0;Gc().forEach((n,r)=>{const a=Ur(n);a&&(ls({node:n,ord:Xc(n,r),sourceFilename:a}),t+=1)}),le.debug("scan mounted detected fields",{count:t}),ur()}function Gc(){const e=Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]')),t=new Set;return e.filter(n=>t.has(n)?!1:(t.add(n),!!(n.textContent||n.innerHTML)))}function Uc(e){return e.map(t=>{const n=document.querySelector(`.field-container[data-index="${t}"]`);if(!n)return null;const r=n.querySelector('[contenteditable="true"]')||n,a=Ur(r)||Ur(n);return{ord:t,node:r,sourceFilename:a}}).filter(t=>t!==null)}function Xc(e,t){const n=["data-field-ord","data-ord","data-index"];for(const a of n){const o=e.getAttribute(a);if(o!==null&&/^\d+$/.test(o))return Number(o)}const r=/(\d+)/.exec(String(e.id||""));return r?Number(r[1]):t}function Ur(e){const t=e.innerHTML||e.textContent||"",n=Vc.exec(t),r=n==null?void 0:n[1];return r&&jc.test(r)?r:""}function ls(e){Pc(e)}function Xr(e,t){const n=window.setTimeout(()=>{bn=bn.filter(r=>r!==n),e()},t);bn.push(n)}Hc()})();
