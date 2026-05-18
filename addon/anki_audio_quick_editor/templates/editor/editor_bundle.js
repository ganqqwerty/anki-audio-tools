var od=Object.defineProperty;var oi=O=>{throw TypeError(O)};var sd=(O,I,Z)=>I in O?od(O,I,{enumerable:!0,configurable:!0,writable:!0,value:Z}):O[I]=Z;var je=(O,I,Z)=>sd(O,typeof I!="symbol"?I+"":I,Z),Pa=(O,I,Z)=>I.has(O)||oi("Cannot "+Z);var h=(O,I,Z)=>(Pa(O,I,"read from private field"),Z?Z.call(O):I.get(O)),F=(O,I,Z)=>I.has(O)?oi("Cannot add the same private member more than once"):I instanceof WeakSet?I.add(O):I.set(O,Z),N=(O,I,Z,Wn)=>(Pa(O,I,"write to private field"),Wn?Wn.call(O,Z):I.set(O,Z),Z),ne=(O,I,Z)=>(Pa(O,I,"access private method"),Z);(function(){"use strict";var Js,zs,ei,rn,an,xt,on,Ln,$n,Rt,et,sn,me,Fa,Ca,xa,si,Ae,Aa,Ge,Tt,he,He,ve,De,tt,Dt,vt,ln,un,cn,Ve,_r,J,id,ld,ud,Ra,wr,Mr,Ta,ti,Oe,We,ge,Ot,In,Bn,mr,ni;const O=[{activeIcon:"pause",command:"aqe:play",icon:"play",iconOnly:!0,label:"Play",title:"Play or pause current audio"},{activeIcon:"refresh-cw",command:"aqe:analyze",icon:"chart-line",iconOnly:!0,label:"Graph",title:"Analyze and show pitch/intensity graph"},{command:"aqe:show-file",icon:"folder-open",label:"Folder",title:"Show current audio file in folder"},{command:"aqe:trim-left",icon:"scissors",label:"-L",title:"Trim 100 ms from left"},{command:"aqe:trim-right",icon:"scissors",label:"-R",title:"Trim 100 ms from right"},{command:"aqe:remove-pauses",icon:"timer-reset",label:"Shorten Pauses",title:"Speed up long internal pauses"},{command:"aqe:slower",icon:"rewind",label:"Slower",title:"Decrease speed"},{command:"aqe:faster",icon:"fast-forward",label:"Faster",title:"Increase speed"},{command:"aqe:volume-down",icon:"volume-1",iconOnly:!0,label:"Volume -",title:"Decrease volume"},{command:"aqe:volume-up",icon:"volume-2",iconOnly:!0,label:"Volume +",title:"Increase volume"},{command:"aqe:undo",icon:"undo-2",iconOnly:!0,label:"Undo",title:"Restore the previous generated audio reference"},{command:"aqe:redo",icon:"redo-2",iconOnly:!0,label:"Redo",title:"Restore the most recently undone audio reference"},{command:"aqe:settings",icon:"settings",iconOnly:!0,label:"Settings",title:"Open Audio Quick Editor settings"}],I=[{command:"aqe:denoise-standard",icon:"volume-x",label:"Standard",title:"Denoise speech with DeepFilterNet"},{command:"aqe:rnnoise",icon:"waves",label:"RNNoise",title:"Denoise speech with RNNoise"}],Z=new Set(["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:remove-pauses","aqe:denoise-standard","aqe:rnnoise","aqe:volume-down","aqe:volume-up"]),Wn={"aqe:play":"play","aqe:analyze":"graph","aqe:show-file":"show-file","aqe:delete-selection":"delete-selection","aqe:trim-left":"trim-left","aqe:trim-right":"trim-right","aqe:remove-pauses":"remove-pauses","aqe:denoise-standard":"denoise-standard","aqe:rnnoise":"rnnoise","aqe:slower":"slower","aqe:faster":"faster","aqe:volume-down":"volume-down","aqe:volume-up":"volume-up","aqe:undo":"undo","aqe:redo":"redo","aqe:settings":"settings"};function qr(e,t){return`aqe-button-${e}-${Wn[t]}`}function Da(e){return e==="aqe:denoise-standard"?"Denoising with Standard...":e==="aqe:rnnoise"?"Denoising with RNNoise...":e==="aqe:delete-selection"?"Deleting region...":"Processing..."}function Ue(e){return document.querySelector(`.aqe-controls[data-aqe-field-ord="${e}"]`)}function D(e){return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${e}"]`)}function Oa(e,t){const n=Ue(e);return(n==null?void 0:n.querySelector(`[data-aqe-command="${t}"]`))??null}function La(e){return Oa(e,"aqe:analyze")}function $a(e){return Oa(e,"aqe:play")}function Ia(e){const t=Ue(e);return(t==null?void 0:t.querySelector(".aqe-repeat-button"))??null}function jn(){return Array.from(document.querySelectorAll(".aqe-button"))}function Sr(){return Array.from(document.querySelectorAll(".aqe-visualizer"))}const Ba=[];let Un=null,Kn=null;function Xn(e){globalThis.pycmd!==void 0&&globalThis.pycmd(e)}function It(e,t){Xn(`focus:${e}`),Xn(t)}function ii(e){Un=e,Xn("aqe:analyze-field")}function li(e){Ba.push(e),Xn("aqe:frontend-log")}function ui(){return Ba.shift()??null}function ci(e){window.__aqePendingPlaybackRequest=e,window.__aqeLastPlaybackRequest=e}function fi(){if(!window.__aqePendingPlaybackRequest)return null;const e=window.__aqePendingPlaybackRequest;return window.__aqePendingPlaybackRequest=null,e}function di(){if(!Un)return null;const e=Un;return Un=null,e}function hi(e){Kn=e}function pi(){if(!Kn)return null;const e=Kn;return Kn=null,e}function _i(e){window.__aqeLastCursorIntent=e}function mi(e){return encodeURIComponent(e||"").replaceAll("%2F","/")}function Ee(e){return(e==null?void 0:e.querySelector(".aqe-audio-clock"))??null}function kr(e){e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!1,e.__aqeAudioClockLastSeekedMs=0,e.dataset.progressClockMode="stopped"}function fn(e){const t=Ee(e);if(!(!t||typeof t.pause!="function"))try{t.pause()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Ar(e){const t=Ee(e);if(kr(e),!!t){fn(e),t.removeAttribute("src"),t.src="";try{t.load()}catch{e.__aqeAudioClockFallback=!0}}}function vi(e,t){const n=Ee(e);if(kr(e),!n){e.__aqeAudioClockFallback=!0;return}if(fn(e),!t){Ar(e);return}n.setAttribute("src",mi(t));try{n.load()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function gi(e,t={}){const n=Ee(e);!n||n.__aqeClockHandlersInstalled||(n.__aqeClockHandlersInstalled=!0,n.addEventListener("loadedmetadata",()=>{n.getAttribute("src")&&(e.__aqeAudioClockAvailable=!0,e.__aqeAudioClockFallback=!1)}),n.addEventListener("error",()=>{var r;e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,e.dataset.playbackState==="playing"&&e.dataset.progressClockMode==="audio"&&((r=t.onErrorDuringPlayback)==null||r.call(t))}),n.addEventListener("ended",()=>{var r;e.dataset.playbackState==="playing"&&((r=t.onEndedDuringPlayback)==null||r.call(t))}),n.addEventListener("seeked",()=>{e.__aqeAudioClockLastSeekedMs=Math.round((Number(n.currentTime)||0)*1e3)}))}function Yn(e){const t=Ee(e);return!t||!(e!=null&&e.__aqeAudioClockAvailable)||!t.getAttribute("src")?!1:t.readyState===void 0||t.readyState>=1}function Qn(e,t,n){const r=Ee(e);if(!r)return!1;const a=Math.max(0,Math.min(Number(t)||0,n||0));try{return r.currentTime=a/1e3,e.__aqeAudioClockLastSeekedMs=Math.round(a),!0}catch{return e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,!1}}var dn=(e=>(e.Debug="debug",e.Error="error",e.Info="info",e.Unknown="unknown",e.Warn="warn",e))(dn||{});function yi(e){return e==="error"?console.error:console.warn}function bi(e){return e==="debug"?dn.Debug:e==="warn"?dn.Warn:e==="error"?dn.Error:dn.Info}function Er(e,t=0){const n=wi(e);return n!==void 0?n:Array.isArray(e)?Mi(e,t):e!==null&&typeof e=="object"?qi(e,t):Si(e)}function wi(e){if(e===void 0)return"[undefined]";if(e===null)return null;if(typeof e=="boolean"||typeof e=="number"||typeof e=="string")return e}function Mi(e,t){return t>=4?"[array]":e.map(n=>Er(n,t+1))}function qi(e,t){if(t>=4)return"[object]";const n={};for(const[r,a]of Object.entries(e))n[r]=Er(a,t+1);return n}function Si(e){return typeof e=="bigint"?e.toString():typeof e=="symbol"?e.description?`Symbol(${e.description})`:"Symbol()":typeof e=="function"?`[function ${e.name||"anonymous"}]`:"[unserializable]"}function ki(e,t,n){const r={level:bi(e),message:t};return n!==void 0&&(r.context=Er(n)),r}function Ai(e,t){function n(r,a,o){const s=yi(r);o===void 0?s(`[${e}] ${a}`):s(`[${e}] ${a}`,o);try{t(ki(r,a,o))}catch{}}return{debug:(r,a)=>n("debug",r,a),error:(r,a)=>n("error",r,a),info:(r,a)=>n("info",r,a),warn:(r,a)=>n("warn",r,a)}}const le=Ai("editor",li),hn=[],Zn=new Set;let Jn=null,zn=null,er=!1;function Ei(){hn.length=0,Zn.clear(),Jn=null,zn=null,er=!1}function Ni(e,t){for(const n of e){if(!n.sourceFilename)continue;const r=Pi(n);if(Zn.has(r))continue;const a=D(n.ord);if((a==null?void 0:a.dataset.hasTrack)==="true"&&a.dataset.sourceFilename===n.sourceFilename){Zn.add(r);continue}Zn.add(r),hn.push({key:r,ord:n.ord,sourceFilename:n.sourceFilename})}tr(t)}function tr(e){if(!(Jn!==null||e.anyBusy()))for(;hn.length;){const t=hn.shift();if(!t)return;const n=D(t.ord);if(!n){Ha(t,e);return}const r=Ue(t.ord);if(!r){Ha(t,e);return}if((r.dataset.aqeSourceFilename||t.sourceFilename)===t.sourceFilename&&!(n.dataset.hasTrack==="true"&&n.dataset.sourceFilename===t.sourceFilename)){Jn=t.key,zn=t.ord,e.requestDefaultGraph({ord:t.ord,sourceFilename:t.sourceFilename});return}}}function Ga(e,t){zn===e&&(Jn=null,zn=null,queueMicrotask(()=>tr(t)))}function Pi(e){return`${e.ord}\0${e.sourceFilename}`}function Ha(e,t){hn.unshift(e),!er&&(er=!0,window.setTimeout(()=>{er=!1,tr(t)},0))}function Fi(e,t){return Math.max(t.startMs,Math.min(Number(e)||0,t.endMs))}function Ci(e){let t="start";e.playbackState==="playing"&&(t="pause"),e.playbackState==="paused"&&(t=e.resumeRequiresRestart?"start":"resume");let n=e.anchorMs;return t==="start"&&e.region.mode==="selection"&&(n=e.region.startMs),t==="pause"&&(n=Va(e.currentProgressMs,e.cursorMs,n)),t==="resume"&&(n=Va(e.currentProgressMs,e.cursorMs,n),e.region.mode==="selection"&&(n<e.region.startMs||n>e.region.endMs)&&(t="start",n=e.region.startMs)),{action:t,cursorMs:Math.round(n),endMs:Math.round(e.region.endMs),engine:e.engine,loop:e.repeat,ord:e.ord,regionMode:e.region.mode}}function Va(e,t,n){return Number(e||t||n||0)}function xi(e){return{analyzerName:e.analyzerName,durationMs:Number(e.durationMs)||0,pitchMaxHz:e.pitchMaxHz,pitchMinHz:e.pitchMinHz,points:e.points.map(Ri),sourceFilename:e.sourceFilename}}function Ri(e){const t=typeof e[0]=="number"?e[0]:0,n=typeof e[1]=="number"?e[1]:null,r=typeof e[2]=="number"?e[2]:null,a=typeof e[3]=="boolean"?e[3]:!1;return[t,n,r,a]}function Nr(e){return e==="playing"||e==="paused"||e==="stopped"}const Wa=50,Ti=4;function ja(){return{active:!1,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:null,startMs:null}}function Ua(e,t){return Math.max(0,Math.min(Number(e)||0,Math.max(0,Number(t)||0)))}function nr(e,t,n,r=Wa){const a=Ua(Math.min(e,t),n),o=Ua(Math.max(e,t),n);return!n||o-a<r?null:{startMs:Math.round(a),endMs:Math.round(o)}}function Di(e,t){if(!e.active||e.startMs===null||e.endMs===null)return null;const n=nr(e.startMs,e.endMs,t);return n?{...n,mode:"selection"}:null}function Oi(e,t){if(!e.draftActive||e.draftStartMs===null||e.draftEndMs===null)return null;const n=nr(e.draftStartMs,e.draftEndMs,t);return n?{...n,mode:"selection"}:null}function Li(e,t,n,r){const a=nr(t,n,r);return a?{...e,active:!0,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:a.endMs,startMs:a.startMs}:Ii(e)}function $i(e,t,n,r){const a=nr(t,n,r);return a?{...e,draftActive:!0,draftEndMs:a.endMs,draftStartMs:a.startMs}:Ka(e)}function Ii(e){return{...Ka(e),active:!1,endMs:null,startMs:null}}function Ka(e){return{...e,draftActive:!1,draftEndMs:null,draftStartMs:null}}function Xa(e,t,n,r){return Math.abs(t.clientX-e.clientX)<Ti||Math.abs(r-n)<Wa}const M={width:620,height:150,left:44,right:10,top:10,bottom:34};function Ya(){return M.width-M.left-M.right}function Qa(){return M.height-M.top-M.bottom}function rt(e,t){return t?M.left+Math.max(0,Math.min(1,e/t))*Ya():M.left}function Bi(e,t,n){if(!e||!t||!n||n<=t)return M.height-M.bottom;const r=Math.max(0,Math.min(1,(e-t)/(n-t)));return M.top+(1-r)*Qa()}function Za(e,t){return t&&t<2e3?`${Math.round(e)} ms`:`${(e/1e3).toFixed(2)}s`}function Gi(e,t){if(!e.length||!t)return"";const n=M.height-M.bottom,r=e[0];if(!r)return"";const a=`M ${rt(r[0],t).toFixed(2)} ${n.toFixed(2)}`,o=e.map(l=>{const c=rt(l[0],t).toFixed(2),f=Math.max(0,Math.min(1,l[2]??0)),u=(n-f*Qa()).toFixed(2);return`L ${c} ${u}`}).join(" "),s=e.at(-1)??r,i=`L ${rt(s[0],t).toFixed(2)} ${n.toFixed(2)} Z`;return`${a} ${o} ${i}`}function Hi(e,t,n,r){const a=[];let o=[];for(const s of e){const i=s[1];if(!(s[3]===!0&&i!==null&&i!==void 0)){o.length&&a.push(o),o=[];continue}o.push([rt(s[0],t),Bi(i,n,r)])}return o.length&&a.push(o),a}function Vi(e,t){const n=e.querySelector(".aqe-pitch");if(n){n.textContent="";for(const r of Hi(t.points,t.durationMs,t.pitchMinHz,t.pitchMaxHz)){if(r.length<2)continue;const a=document.createElementNS("http://www.w3.org/2000/svg","path");a.setAttribute("class","aqe-pitch-path"),a.setAttribute("d",r.map((o,s)=>{const i=o[0]??0,l=o[1]??0;return`${s?"L":"M"} ${i.toFixed(2)} ${l.toFixed(2)}`}).join(" ")),n.appendChild(a)}}}function Wi(e,t){const n=e.querySelector(".aqe-labels");if(!n)return;n.textContent="";const r=t.pitchMaxHz||500,a=t.pitchMinHz||75;for(const o of[[r,M.top+10],[a,M.height-M.bottom]]){const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","aqe-hz-label"),s.setAttribute("x","2"),s.setAttribute("y",String(o[1])),s.textContent=`${Math.round(o[0])} Hz`,n.appendChild(s)}}function ji(e,t){const n=e.querySelector(".aqe-x-axis");if(!n)return;n.textContent="";const r=[0,t/2,t].filter((a,o,s)=>o===0||a!==s[o-1]);for(const a of r){const o=rt(a,t),s=document.createElementNS("http://www.w3.org/2000/svg","line");s.setAttribute("class","aqe-x-tick"),s.setAttribute("x1",o.toFixed(2)),s.setAttribute("x2",o.toFixed(2)),s.setAttribute("y1",String(M.height-M.bottom)),s.setAttribute("y2",String(M.height-M.bottom+4));const i=document.createElementNS("http://www.w3.org/2000/svg","text");i.setAttribute("class","aqe-x-label"),i.setAttribute("x",o.toFixed(2)),i.setAttribute("y",String(M.height-8)),i.textContent=Za(a,t),n.append(s,i)}}function Ja(e){const t=e.getBoundingClientRect(),n=Number(t.width)||M.width,r=Number(t.height)||M.height,a=Math.min(n/M.width,r/M.height)||1;return{left:t.left+M.left*a,width:Ya()*a}}function pn(e,t,n){const r=Ja(t);return Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*n}function Ui(e){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="true",e.dataset.hasTrack="false",e.dataset.durationMs="0",e.dataset.sourceFilename="",e.dataset.anchorMs="0",e.dataset.cursorMs="0",e.dataset.progressMs="0",e.dataset.resumeRequiresRestart="false",e.dataset.playbackEngine="",e.dataset.playbackStartMs="0",e.dataset.playbackEndMs="0",e.dataset.playbackRegionMode="full",za(e)}function Ki(e,t){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="false",e.dataset.hasTrack="true",e.dataset.durationMs=String(t.durationMs||0),e.dataset.analyzerName=t.analyzerName||"",e.dataset.sourceFilename=t.sourceFilename||"";const n=e.querySelector(".aqe-intensity");n&&n.setAttribute("d",Gi(t.points,t.durationMs)),Vi(e,t),Wi(e,t),ji(e,t.durationMs||0)}function Xi(e,t,n="info"){const r=e.querySelector(".aqe-visualizer-status"),a=e.querySelector(".aqe-spinner"),o=n==="processing";e.dataset.graphBusy=o?"true":"false",a&&(a.hidden=!o),r&&(r.textContent=t||"",r.dataset.kind=n||"info")}function Yi(e,t,n){const r=e.querySelector(".aqe-selection"),a=e.querySelector(".aqe-selection-start"),o=e.querySelector(".aqe-selection-end"),s=n??t,i=Number(e.dataset.durationMs||"0");if(!r||!a||!o||!s||!i){r==null||r.setAttribute("width","0"),r==null||r.setAttribute("visibility","hidden"),r==null||r.classList.remove("aqe-selection-draft"),a==null||a.setAttribute("visibility","hidden"),o==null||o.setAttribute("visibility","hidden");return}const l=rt(s.startMs,i),c=rt(s.endMs,i);r.setAttribute("visibility","visible"),r.classList.toggle("aqe-selection-draft",n!==null),r.setAttribute("x",l.toFixed(2)),r.setAttribute("y",String(M.top)),r.setAttribute("width",Math.max(0,c-l).toFixed(2)),r.setAttribute("height",String(M.height-M.top-M.bottom)),a.setAttribute("visibility","visible"),o.setAttribute("visibility","visible");for(const[f,u]of[[a,l],[o,c]])f.setAttribute("x1",u.toFixed(2)),f.setAttribute("x2",u.toFixed(2)),f.setAttribute("y1",String(M.top)),f.setAttribute("y2",String(M.height-M.bottom))}function Qi(e,t,n){const r=rt(t,n),a=e.querySelector(".aqe-cursor");a&&(a.setAttribute("x1",r.toFixed(2)),a.setAttribute("x2",r.toFixed(2)));const o=e.querySelector(".aqe-cursor-label");o&&(o.textContent=Za(t,n))}function za(e){var t;(t=e.querySelector(".aqe-intensity"))==null||t.setAttribute("d",""),Pr(e,".aqe-pitch"),Pr(e,".aqe-labels"),Pr(e,".aqe-x-axis")}function Zi(e){const t=e.querySelector(".aqe-cursor");t&&(t.setAttribute("x1",String(M.left)),t.setAttribute("x2",String(M.left)));const n=e.querySelector(".aqe-cursor-label");n&&(n.textContent="0 ms")}function Ji(e,t){return{analyzerName:t.analyzerName,durationMs:t.durationMs,ord:e,points:t.points.length,sourceFilename:t.sourceFilename}}function Pr(e,t){const n=e.querySelector(t);n&&(n.textContent="")}function _n(e){return!e||e.dataset.selectionActive!=="true"?null:Di({active:e.dataset.selectionActive==="true",startMs:Number(e.dataset.selectionStartMs||"0"),endMs:Number(e.dataset.selectionEndMs||"0")},Number(e.dataset.durationMs||"0"))}function Fr(e){return!e||e.dataset.selectionDraftActive!=="true"?null:Oi({draftActive:e.dataset.selectionDraftActive==="true",draftStartMs:Number(e.dataset.selectionDraftStartMs||"0"),draftEndMs:Number(e.dataset.selectionDraftEndMs||"0")},Number(e.dataset.durationMs||"0"))}function eo(e){const t=_n(e);return t||{startMs:0,endMs:Number(e.dataset.durationMs||"0")||0,mode:"full"}}function Bt(e,t={}){e.dataset.selectionDraftActive="false",e.dataset.selectionDraftStartMs="",e.dataset.selectionDraftEndMs="",t.redraw!==!1&&rr(e)}function zi(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=$i(ja(),t,n,a);return!o.draftActive||o.draftStartMs===null||o.draftEndMs===null?(Bt(e,r),!1):(e.dataset.selectionDraftActive="true",e.dataset.selectionDraftStartMs=String(o.draftStartMs),e.dataset.selectionDraftEndMs=String(o.draftEndMs),r.redraw!==!1&&rr(e),!0)}function el(e,t,n={}){const r=Fr(e);return r?(Bt(e,{redraw:!1}),tl(e,r.startMs,r.endMs,t,n)):(Bt(e),!1)}function to(e,t={}){if(e.dataset.selectionActive="false",e.dataset.selectionStartMs="",e.dataset.selectionEndMs="",Bt(e,{redraw:!1}),rr(e),t.resetPlaybackRegion!==!1){const n=eo(e);e.dataset.playbackStartMs=String(Math.round(n.startMs)),e.dataset.playbackEndMs=String(Math.round(n.endMs)),e.dataset.playbackRegionMode=n.mode}}function tl(e,t,n,r,a={}){const o=Number(e.dataset.durationMs||"0"),s=Li(ja(),t,n,o);return!s.active||s.startMs===null||s.endMs===null?(to(e),!1):(Bt(e,{redraw:!1}),e.dataset.selectionActive="true",e.dataset.selectionStartMs=String(s.startMs),e.dataset.selectionEndMs=String(s.endMs),e.dataset.playbackStartMs=String(s.startMs),e.dataset.playbackEndMs=String(s.endMs),e.dataset.playbackRegionMode="selection",rr(e),a.updateCursor!==!1&&r.setCursor(e,s.startMs,!1),!0)}function rr(e){const t=Fr(e),n=t??_n(e);Yi(e,n,t)}function nl(){return document.body.dataset.aqeBusy==="true"}function rl(e){var t;return((t=Ue(e))==null?void 0:t.querySelector(".aqe-delete-region-button"))??null}function no(e,t){return e.startMs<=0&&e.endMs>=t}function ro(e,t){return!!e&&e.endMs>e.startMs&&!no(e,t)}function mn(e){const t=Number(e.dataset.aqeFieldOrd||"0"),n=rl(t);if(!n)return;const r=_n(e),a=Number(e.dataset.durationMs||"0"),o=r!==null,s=ro(r,a);n.hidden=!o,n.disabled=nl()||!s,n.dataset.aqeButtonState=s?"default":"unavailable",n.title=s?"Delete selected region":"Cannot delete the whole audio clip",n.setAttribute("aria-disabled",n.disabled?"true":"false")}function al(){Sr().forEach(mn)}function ao(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=Number(e.dataset.durationMs||"0")||0,a=_n(e);if(!a||!ro(a,r))return a&&no(a,r)&&le.warn("region delete rejected whole clip",{ord:n,sourceFilename:e.dataset.sourceFilename||"",selectionStartMs:a.startMs,selectionEndMs:a.endMs,durationMs:r,trigger:t}),null;const o=e.dataset.sourceFilename||"";if(!o)return null;const s=e.dataset.playbackState;return{ord:n,sourceFilename:o,selectionStartMs:Math.round(a.startMs),selectionEndMs:Math.round(a.endMs),cursorMs:Math.round(Number(e.dataset.cursorMs||"0")||0),durationMs:Math.round(r),trigger:t,playbackActive:Nr(s)&&s!=="stopped"}}function ol(e,t,n,r,a){e.preventDefault();const o=a.playbackStateFor(t),s=t.querySelector(".aqe-visualizer-svg"),i=Number(t.dataset.durationMs||"0");if(!s||!i)return;o==="playing"&&a.stopProgressClock(t);const l=f=>{a.setCursor(t,oo(f,s,i,t,a),!1)},c=f=>{window.removeEventListener("pointermove",l),window.removeEventListener("pointerup",c);const u=o==="playing";o==="paused"&&(t.dataset.resumeRequiresRestart="true");const d=oo(f,s,i,t,a),m=u&&a.audioClockReady(t)?"html":"";a.setCursor(t,d,r,{previousPlaybackState:o,restartPlayback:u,engine:m}),a.audioClockReady(t)&&a.seekAudioClock(t,d),u&&m==="html"&&a.startEditorHtmlPlayback(t,a.playbackRequestForStart(t,n,d,"html"))};l(e),window.addEventListener("pointermove",l),window.addEventListener("pointerup",c)}function sl(e,t,n,r){e.preventDefault();const a=t.querySelector(".aqe-visualizer-svg"),o=Number(t.dataset.durationMs||"0");if(!a||!o)return;const s=r.playbackStateFor(t),i=r.currentProgressMs(t)??Number(t.dataset.cursorMs||"0"),l={clientX:e.clientX},c=pn(e,a,o);let f=!1,u=A=>{},d=A=>{},m=()=>{},p=A=>{};const w=()=>{window.removeEventListener("pointermove",u),window.removeEventListener("pointerup",d),window.removeEventListener("pointercancel",m),window.removeEventListener("keydown",p),window.removeEventListener("blur",m),a.removeEventListener("lostpointercapture",m)},_=()=>{f||s!=="playing"||(f=!0,r.stopProgressClock(t,{clearEngine:!1}),r.setCursor(t,i,!1,{updateAnchor:!1}))},v=()=>{s==="playing"&&f&&r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,i,"html"))};u=A=>{const y=pn(A,a,o);if(Xa(l,A,c,y)){r.clearSelectionDraft(t);return}_(),r.setSelectionDraft(t,c,y)},d=A=>{w();const y=pn(A,a,o);if(Xa(l,A,c,y)){r.clearSelection(t),v();return}_(),r.draftSelectionForVisualizer(t)||r.setSelectionDraft(t,c,y,{redraw:!1});const q=r.commitSelectionDraft(t);if(s==="paused"&&(t.dataset.resumeRequiresRestart="true"),q&&s==="playing"){const k=r.selectionForVisualizer(t);r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,(k==null?void 0:k.startMs)??c,"html"))}},m=()=>{w(),r.clearSelectionDraft(t),v()},p=A=>{A.key==="Escape"&&m()},window.addEventListener("pointermove",u),window.addEventListener("pointerup",d),window.addEventListener("pointercancel",m),window.addEventListener("keydown",p),window.addEventListener("blur",m),a.addEventListener("lostpointercapture",m)}function il(e,t,n){const r=n.visualizerForOrd(t);if(r){if(e.shiftKey){sl(e,r,t,n);return}ol(e,r,t,!0,n)}}function oo(e,t,n,r,a){const o=pn(e,t,n),s=a.selectionForVisualizer(r);return s&&r.dataset.repeatEnabled==="true"?Fi(o,s):o}function yt(e){e.__aqePlaybackTimer&&(window.cancelAnimationFrame(e.__aqePlaybackTimer),e.__aqePlaybackTimer=null)}function so(e){const t=Number(e.dataset.durationMs||"0"),n=performance.now()-Number(e.dataset.playStartedAt||"0");return Math.min(t,Number(e.dataset.playStartMs||"0")+n)}function io(e){const t=Ee(e);if(!t)return null;const n=Number(e.dataset.durationMs||"0");return Math.min(n,(Number(t.currentTime)||0)*1e3)}function lo(e){return e.dataset.progressClockMode==="audio"?io(e):e.dataset.progressClockMode==="manual"?so(e):Number(e.dataset.progressMs||e.dataset.cursorMs||"0")}function Cr(e,t,n,r={}){return t<dl(e,n)?!1:n.repeatEnabledFor(e)?(hl(e,n,r),!0):(ll(e,n),!0)}function ll(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=t.effectivePlaybackRegion(e),a=e.dataset.playbackRegionMode==="selection"?r.startMs:Number(e.dataset.anchorMs||"0");Rr(e,t),t.setCursor(e,a,!1,{updateAnchor:!1}),Yn(e)&&Qn(e,a,Number(e.dataset.durationMs||"0")),t.clearStatus(n),window.__aqeActiveField=n,t.focusAndSendCommand(n,"aqe:play-ended")}function xr(e,t){const n=()=>{if(e.dataset.playbackState!=="playing")return;const r=io(e);if(r===null){Ke(e,Number(e.dataset.cursorMs||"0"),t);return}t.setCursor(e,r,!1,{updateAnchor:!1}),!Cr(e,r,t)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(n))};e.__aqePlaybackTimer=window.requestAnimationFrame(n)}function Ke(e,t,n){if(yt(e),fn(e),!Number(e.dataset.durationMs||"0"))return;const a=uo(e,t);e.__aqeAudioClockFallback=!0,e.dataset.playbackState="playing",e.dataset.progressClockMode="manual",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),Tr(e,a,n),n.setPlaybackButtonLabel(e,"Pause");const o=()=>{if(e.dataset.playbackState!=="playing")return;const s=so(e);n.setCursor(e,s,!1,{updateAnchor:!1}),!Cr(e,s,n)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(o))};e.__aqePlaybackTimer=window.requestAnimationFrame(o)}function ul(e,t,n,r={}){var i;const a=Ee(e);if(!a||!Qn(e,t,Number(e.dataset.durationMs||"0"))||typeof a.play!="function"){if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}Ke(e,t,n);return}e.dataset.progressClockMode="audio",e.__aqeAudioClockFallback=!1;const o=()=>{var l;if(r.manualFallback===!1){(l=r.onAudioPlayFailed)==null||l.call(r);return}Ke(e,t,n)},s=()=>{var l;e.dataset.playbackState==="playing"&&(yt(e),e.dataset.progressClockMode="audio",le.info("html audio playback started",{ord:e.dataset.aqeFieldOrd}),xr(e,n),(l=r.onAudioStarted)==null||l.call(r))};Promise.resolve(a.play()).then(s).catch(()=>{e.dataset.playbackState==="playing"&&(le.warn("html audio play rejected; using manual clock",{ord:e.dataset.aqeFieldOrd}),o())})}function cl(e,t,n,r={}){var i;const a=r.engine||e.dataset.playbackEngine||"";if(Rr(e,n,{clearEngine:!1}),n.stopOtherPlayback(e),!Number(e.dataset.durationMs||"0"))return;const s=uo(e,t);if(e.dataset.playbackEngine=a,e.dataset.playbackState="playing",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(s),Tr(e,s,n),n.setCursor(e,s,!1,{updateAnchor:!1}),n.setPlaybackButtonLabel(e,"Pause"),le.info("playback clock selected",{engine:a||"auto",startMs:s}),a==="native"){Ke(e,s,n);return}if(Yn(e)){ul(e,s,n,r);return}if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}Ke(e,s,n)}function fl(e,t){const n=lo(e);n!==null&&t.setCursor(e,n,!1,{updateAnchor:!1}),yt(e),fn(e),e.dataset.playbackState="paused",e.dataset.progressClockMode="stopped",t.setPlaybackButtonLabel(e,"Play")}function Rr(e,t,n={}){yt(e),fn(e),e.dataset.playbackState="stopped",e.dataset.progressClockMode="stopped",e.dataset.resumeRequiresRestart="false",n.clearEngine!==!1&&(e.dataset.playbackEngine=""),n.clearAudio&&Ar(e),t.setPlaybackButtonLabel(e,"Play")}function Tr(e,t,n,r=n.effectivePlaybackRegion(e)){e.dataset.playbackStartMs=String(Math.round(t)),e.dataset.playbackEndMs=String(Math.round(r.endMs)),e.dataset.playbackRegionMode=r.mode}function dl(e,t){const n=t.effectivePlaybackRegion(e),r=Number(e.dataset.playbackEndMs||"0")||n.endMs;return Math.max(n.startMs,Math.min(r,Number(e.dataset.durationMs||"0")||0))}function hl(e,t,n={}){const r=t.effectivePlaybackRegion(e),a=r.startMs;if(Tr(e,a,t,r),e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),t.setCursor(e,a,!1,{updateAnchor:!1}),e.dataset.progressClockMode!=="audio"||!Yn(e)){Ke(e,a,t);return}if(!Qn(e,a,Number(e.dataset.durationMs||"0"))){Ke(e,a,t);return}if(!n.forceAudioPlay){yt(e),xr(e,t);return}const o=Ee(e);!o||typeof o.play!="function"||(yt(e),Promise.resolve(o.play()).then(()=>{e.dataset.playbackState==="playing"&&xr(e,t)}).catch(()=>{e.dataset.playbackState==="playing"&&Ke(e,a,t)}))}function uo(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function co(){return document.body.dataset.aqeBusy==="true"}function fo(){var e;return((e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.repeatPlaybackByDefault)===!0}function pl(e){for(const t of Sr())t!==e&&Vt(t)!=="stopped"&&at(t)}function _l(){for(const e of Sr())Vt(e)!=="stopped"&&at(e)}function Gt(e,t,n="",r=""){document.body.dataset.aqeBusy=t?"true":"false",document.querySelectorAll(".aqe-controls").forEach(s=>{s.dataset.busy=t?"true":"false"}),jn().forEach(s=>{s.disabled=!!t}),al(),t||queueMicrotask(()=>tr(Gr()));const a=Ue(e),o=a==null?void 0:a.querySelector(".aqe-status");o&&(o.textContent=n||"",o.dataset.kind=t?"processing":"info",o.title=r||"")}function ho(e,t="info"){const n=Number(window.__aqeActiveField??0),r=Ue(n),a=r==null?void 0:r.querySelector(".aqe-status");a&&(a.textContent=e||"",a.dataset.kind=t||"info")}function ml(e){const t=Ue(e),n=t==null?void 0:t.querySelector(".aqe-status");n&&(n.textContent="",n.dataset.kind="info",n.title="")}function Ht(e,t,n){var o;const r=t==="aqe:play"?$a(e):t==="aqe:analyze"?La(e):((o=Ue(e))==null?void 0:o.querySelector(`[data-aqe-command="${t}"]`))??null;if(!r)return;const a=r.querySelector(".aqe-button-label");a?a.textContent=n:r.textContent=n,t==="aqe:play"&&(r.dataset.aqeButtonState=n==="Pause"?"pause":"play"),t==="aqe:analyze"&&(r.dataset.aqeButtonState=n==="Redraw"?"redraw":"graph")}function po(e,t,n){if(!co()){if(typeof t.focus=="function"&&t.focus(),window.__aqeActiveField=n,le.info("command dispatched",{command:e,ord:n}),e==="aqe:analyze"){go(n,!0);return}e==="aqe:play"&&$l(n)||(Z.has(e)&&(_l(),Gt(n,!0,Da(e))),It(n,e))}}function vl(e){kr(e)}function gl(e){yt(e)}function yl(e){Ar(e)}function bl(e,t){vi(e,t)}function wl(e){gi(e,{onErrorDuringPlayback(){le.warn("audio clock failed during playback",{ord:e.dataset.aqeFieldOrd}),Ll(e,Number(e.dataset.cursorMs||"0"))},onEndedDuringPlayback(){Ol(e,Number(e.dataset.durationMs||"0"),{forceAudioPlay:!0})}})}function Dr(e){return Yn(e)}function Ml(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function _o(e){return _n(e)}function mo(e){return Fr(e)}function Or(e){return eo(e)}function Lr(e,t){e.dataset.repeatEnabled=t?"true":"false";const n=Number(e.dataset.aqeFieldOrd||"0"),r=Ia(n);r&&(r.ariaPressed=t?"true":"false",r.dataset.aqeButtonState=t?"active":"default")}function ql(e,t){const n=D(e);return n?(Lr(n,t),!0):!1}function Sl(e,t={}){Bt(e,t)}function kl(e,t,n,r={}){return zi(e,t,n,r)}function Al(e,t={}){const n=el(e,Pl(),t);return mn(e),n}function vn(e,t={}){to(e,t),mn(e)}function El(e){e.dataset.playbackStartMs="0",e.dataset.playbackEndMs=String(Number(e.dataset.durationMs||"0")||0),e.dataset.playbackRegionMode="full",Lr(e,fo()),vn(e,{resetPlaybackRegion:!1})}function Nl(){return{audioClockReady:Dr,clearSelection:vn,clearSelectionDraft:Sl,commitSelectionDraft:Al,currentProgressMs:Mo,draftSelectionForVisualizer:mo,playbackRequestForStart:Fl,playbackStateFor:Vt,seekAudioClock:vo,selectionForVisualizer:_o,setCursor:bt,setSelectionDraft:kl,startEditorHtmlPlayback:Ao,stopProgressClock:at,visualizerForOrd:D}}function Pl(){return{setCursor:bt}}function $r(e){return e.dataset.repeatEnabled==="true"}function gn(){return{clearStatus:ml,effectivePlaybackRegion:Or,focusAndSendCommand:It,playbackEngineFor:yn,repeatEnabledFor:$r,setCursor:bt,setPlaybackButtonLabel:Dl,stopOtherPlayback:pl}}function Fl(e,t,n,r=yn(e)){const a=Or(e);return{ord:t,action:"start",cursorMs:Math.round(Ml(e,n)),endMs:Math.round(a.endMs),engine:r,loop:$r(e),regionMode:a.mode}}function vo(e,t){return Qn(e,t,Number(e.dataset.durationMs||"0"))}function bt(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Math.max(0,Math.min(Number(t)||0,a||0));if(e.dataset.cursorMs=String(Math.round(o)),e.dataset.progressMs=String(Math.round(o)),r.updateAnchor!==!1&&(e.dataset.anchorMs=String(Math.round(o))),Qi(e,o,a),n){window.__aqeActiveField=Number(e.dataset.aqeFieldOrd||"0");const s={cursorMs:Math.round(o),previousPlaybackState:r.previousPlaybackState||Vt(e),restartPlayback:!!r.restartPlayback};r.engine&&(s.engine=r.engine),_i(s),le.info("cursor committed",s),It(window.__aqeActiveField,"aqe:set-cursor")}}function Cl(e,t){var n;(n=D(t))==null||n.focus(),il(e,t,Nl())}function go(e,t){bo(e)&&(window.__aqeActiveField=e,le.info("graph requested",{notifyPython:t,ord:e}),Gt(e,!0,"Analyzing...",""),It(e,"aqe:analyze"))}function yo(e){bo(e.ord)&&(le.info("default graph requested",e),Gt(e.ord,!0,"Analyzing...",""),ii(e))}function bo(e){const t=D(e);return t?(at(t,{clearAudio:!0}),Ui(t),vn(t),bt(t,0,!1),Ht(e,"aqe:analyze","Redraw"),Br(e,"Analyzing...","processing"),!0):!1}function xl(e){return window.__aqePendingGraphRedrawField=e,Ir()}function Ir(){const e=window.__aqePendingGraphRedrawField;if(typeof e!="number")return!1;const t=D(e);return t?(t.dataset.graphBusy==="true"||t.dataset.hasTrack==="true"||go(e,!0),!0):!1}function Br(e,t,n="info"){const r=D(e);r&&Xi(r,t,n)}function Rl(e,t,n){const r=D(e);if(!r||!t)return;const a=xi(t);Ki(r,a),r.dataset.anchorMs=String(n||0),window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null),vn(r),r.dataset.playbackStartMs="0",r.dataset.playbackEndMs=String(a.durationMs||0),r.dataset.playbackRegionMode="full",bl(r,a.sourceFilename||""),Ht(e,"aqe:analyze","Redraw"),bt(r,n||0,!1),Dr(r)&&vo(r,n||0),Br(e,a.analyzerName||"","info"),Gt(e,!1,"",""),Ga(e,Gr()),le.info("graph rendered",Ji(e,a))}function Tl(e,t,n="info"){n!=="processing"&&window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null);const r=D(e);r&&(r.hidden=!1,r.dataset.graphActive="true",n==="processing"&&(r.dataset.hasTrack="false"),Ht(e,"aqe:analyze","Redraw")),Br(e,t,n),n!=="processing"&&Ga(e,Gr())}function Gr(){return{anyBusy:co,requestDefaultGraph:yo}}function wo(){document.body.dataset.aqeBusy="false",window.__aqeActiveField=null,window.__aqeLastCursorIntent=null,document.querySelectorAll(".aqe-controls").forEach(e=>{e.dataset.busy="false",e.dataset.aqeSourceFilename="",e.querySelectorAll(".aqe-button").forEach(o=>{o.disabled=!1,o.dataset.aqeCommand==="aqe:analyze"&&Ht(Number(e.dataset.aqeFieldOrd||"0"),"aqe:analyze","Graph"),o.dataset.aqeCommand==="aqe:play"&&Ht(Number(e.dataset.aqeFieldOrd||"0"),"aqe:play","Play")});const t=e.querySelector(".aqe-status");t&&(t.textContent="",t.dataset.kind="info",t.title="");const n=e.querySelector(".aqe-visualizer");if(!n)return;gl(n),yl(n),n.hidden=!0,n.dataset.anchorMs="0",n.dataset.cursorMs="0",n.dataset.progressMs="0",n.dataset.graphActive="false",n.dataset.graphBusy="false",n.dataset.hasTrack="false",n.dataset.playbackState="stopped",n.dataset.playbackEngine="",n.dataset.resumeRequiresRestart="false",n.dataset.durationMs="0",n.dataset.sourceFilename="",n.dataset.analyzerName="",n.dataset.playStartedAt="0",n.dataset.playStartMs="0",n.dataset.playbackStartMs="0",n.dataset.playbackEndMs="0",n.dataset.playbackRegionMode="full",n.dataset.progressClockMode="stopped",Lr(n,fo()),vn(n),za(n),Zi(n);const r=n.querySelector(".aqe-visualizer-status");r&&(r.textContent="",r.dataset.kind="info");const a=n.querySelector(".aqe-spinner");a&&(a.hidden=!0)})}function Dl(e,t){const n=Number(e.dataset.aqeFieldOrd||"0");Ht(n,"aqe:play",t)}function Mo(e){return lo(e)}function Ol(e,t,n={}){return Cr(e,t,gn(),n)}function Ll(e,t){Ke(e,t,gn())}function qo(e,t,n={}){cl(e,t,gn(),n)}function So(e){fl(e,gn())}function at(e,t={}){Rr(e,gn(),t)}function ko(e){const t=D(e);return t?Ci({anchorMs:Number(t.dataset.anchorMs||t.dataset.cursorMs||"0"),currentProgressMs:Mo(t),cursorMs:Number(t.dataset.cursorMs||"0"),engine:yn(t),ord:e,playbackState:Vt(t),region:Or(t),repeat:$r(t),resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true"}):{ord:e,action:"start",cursorMs:0}}function yn(e){if(!e||e.dataset.hasTrack!=="true")return"native";const t=e.dataset.playbackEngine||"";return e.dataset.playbackState!=="stopped"&&(t==="html"||t==="native")?t:Dr(e)?"html":"native"}function Hr(e){const t=D(e.ord);t&&(t.dataset.playbackEngine=e.engine||""),ci(e),window.__aqeActiveField=e.ord,le.info("playback request queued",e),It(e.ord,"aqe:play")}function Ao(e,t){return qo(e,t.cursorMs,{engine:"html",manualFallback:!1,onAudioStarted(){Hr(t)},onAudioPlayFailed(){if(le.warn("html playback failed; falling back to native",{ord:t.ord}),at(e),t.regionMode==="selection"||t.loop){window.__aqeActiveField=t.ord,ho("Selected repeat playback needs browser audio.","warning");return}Hr({...t,engine:"native"})}}),!0}function $l(e){const t=D(e);if(!t||yn(t)!=="html")return!1;const n={...ko(e),engine:"html"};return n.action==="pause"?(So(t),n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0"),Hr(n),!0):(n.action==="resume"&&(n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0")),Ao(t,n))}function Il(e,t,n){const r=D(e);r&&((t==="playing"||t==="paused")&&(r.dataset.resumeRequiresRestart="false"),t==="playing"?qo(r,n,{engine:r.dataset.playbackEngine==="html"||r.dataset.playbackEngine==="native"?r.dataset.playbackEngine:""}):t==="paused"?So(r):at(r))}function Bl(){const e=fi();if(e)return e;const t=Number(window.__aqeActiveField||"0"),n=ko(t),r=D(t);return r&&(r.dataset.playbackEngine=n.engine||""),n}function Gl(e){const t=D(e);return t?(at(t),!0):!1}function Hl(){const e=Number(window.__aqeActiveField||"0"),t=D(e);return t?Number(t.dataset.cursorMs||"0"):0}function Vl(){const e=Number(window.__aqeActiveField||"0"),t=D(e),n=t?Number(t.dataset.cursorMs||"0"):0;return window.__aqeLastCursorIntent||{cursorMs:n,previousPlaybackState:t?Vt(t):"stopped",restartPlayback:!1}}function Vt(e){const t=e.dataset.playbackState;return Nr(t)?t:"stopped"}const Eo=(zs=(Js=globalThis.process)==null?void 0:Js.env)==null?void 0:zs.NODE_ENV,b=Eo&&!Eo.toLowerCase().startsWith("prod");var Vr=Array.isArray,Wl=Array.prototype.indexOf,wt=Array.prototype.includes,ar=Array.from,Mt=Object.defineProperty,Xe=Object.getOwnPropertyDescriptor,jl=Object.getOwnPropertyDescriptors,Ul=Object.prototype,Kl=Array.prototype,No=Object.getPrototypeOf,Po=Object.isExtensible;function bn(e){return typeof e=="function"}const B=()=>{};function Xl(e){for(var t=0;t<e.length;t++)e[t]()}function Fo(){var e,t,n=new Promise((r,a)=>{e=r,t=a});return{promise:n,resolve:e,reject:t}}function Yl(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const r of e)if(n.push(r),n.length===t)break;return n}const re=2,wn=4,or=8,Wr=1<<24,Ye=16,Ne=32,qt=64,jr=128,we=512,z=1024,ae=2048,Pe=4096,pe=8192,Qe=16384,St=32768,ot=65536,sr=1<<17,Co=1<<18,Wt=1<<19,Ql=1<<20,Ze=1<<25,st=65536,Ur=1<<21,ir=1<<22,it=1<<23,lt=Symbol("$state"),xo=Symbol("legacy props"),Zl=Symbol(""),Ro=Symbol("proxy path"),kt=new class extends Error{constructor(){super(...arguments);je(this,"name","StaleReactionError");je(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}},To=!!((ei=globalThis.document)!=null&&ei.contentType)&&globalThis.document.contentType.includes("xml");function Do(e){if(b){const t=new Error(`lifecycle_outside_component
\`${e}(...)\` can only be used during component initialisation
https://svelte.dev/e/lifecycle_outside_component`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/lifecycle_outside_component")}function Jl(){if(b){const e=new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/async_derived_orphan")}function zl(){if(b){const e=new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/derived_references_self")}function Oo(e,t,n){if(b){const r=new Error(`each_key_duplicate
${n?`Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}`:`Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_duplicate")}function eu(e,t,n){if(b){const r=new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_volatile")}function tu(e){if(b){const t=new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_in_teardown")}function nu(){if(b){const e=new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function ru(e){if(b){const t=new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_orphan")}function au(){if(b){const e=new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function ou(){if(b){const e=new Error("invalid_snippet\nCould not `{@render}` snippet due to the expression being `null` or `undefined`. Consider using optional chaining `{@render snippet?.()}`\nhttps://svelte.dev/e/invalid_snippet");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/invalid_snippet")}function su(e){if(b){const t=new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_invalid_value")}function iu(e){if(b){const t=new Error(`props_rest_readonly
Rest element properties of \`$props()\` such as \`${e}\` are readonly
https://svelte.dev/e/props_rest_readonly`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_rest_readonly")}function lu(e){if(b){const t=new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/rune_outside_svelte")}function uu(){if(b){const e=new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function cu(){if(b){const e=new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_prototype_fixed")}function fu(){if(b){const e=new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function du(){if(b){const e=new Error("svelte_boundary_reset_onerror\nA `<svelte:boundary>` `reset` function cannot be called while an error is still being handled\nhttps://svelte.dev/e/svelte_boundary_reset_onerror");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const hu=1,pu=2,Lo=4,_u=8,mu=16,vu=1,gu=4,yu=8,bu=16,wu=1,Mu=2,ee=Symbol(),qu=Symbol("filename"),$o="http://www.w3.org/1999/xhtml",Su="http://www.w3.org/2000/svg",ku="@attach";var Mn="font-weight: bold",qn="font-weight: normal";function Au(){b?console.warn(`%c[svelte] lifecycle_double_unmount
%cTried to unmount a component that was not mounted
https://svelte.dev/e/lifecycle_double_unmount`,Mn,qn):console.warn("https://svelte.dev/e/lifecycle_double_unmount")}function Eu(){b?console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value",Mn,qn):console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function Kr(e){b?console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`,Mn,qn):console.warn("https://svelte.dev/e/state_proxy_equality_mismatch")}function Nu(){b?console.warn(`%c[svelte] state_proxy_unmount
%cTried to unmount a state proxy, rather than a component
https://svelte.dev/e/state_proxy_unmount`,Mn,qn):console.warn("https://svelte.dev/e/state_proxy_unmount")}function Pu(){b?console.warn("%c[svelte] svelte_boundary_reset_noop\n%cA `<svelte:boundary>` `reset` function only resets the boundary the first time it is called\nhttps://svelte.dev/e/svelte_boundary_reset_noop",Mn,qn):console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Io(e){return e===this.v}function Fu(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Bo(e){return!Fu(e,this.v)}let Cu=!1;function Ie(e,t){return e.label=t,Go(e.v,t),e}function Go(e,t){var n;return(n=e==null?void 0:e[Ro])==null||n.call(e,t),e}function xu(e){const t=new Error,n=Ru();return n.length===0?null:(n.unshift(`
`),Mt(t,"stack",{value:n.join(`
`)}),Mt(t,"name",{value:e}),t)}function Ru(){const e=Error.stackTraceLimit;Error.stackTraceLimit=1/0;const t=new Error().stack;if(Error.stackTraceLimit=e,!t)return[];const n=t.split(`
`),r=[];for(let a=0;a<n.length;a++){const o=n[a],s=o.replaceAll("\\","/");if(o.trim()!=="Error"){if(o.includes("validate_each_keys"))return[];s.includes("svelte/src/internal")||s.includes("node_modules/.vite")||r.push(o)}}return r}let H=null;function jt(e){H=e}let Ut=null;function lr(e){Ut=e}let Sn=null;function Ho(e){Sn=e}function Tu(e){return Du("getContext").get(e)}function L(e,t=!1,n){H={p:H,i:!1,c:null,e:null,s:e,x:null,l:null},b&&(H.function=n,Sn=n)}function $(e){var t=H,n=t.e;if(n!==null){t.e=null;for(var r of n)fs(r)}return t.i=!0,H=t.p,b&&(Sn=(H==null?void 0:H.function)??null),{}}function Vo(){return!0}function Du(e){return H===null&&Do(e),H.c??(H.c=new Map(Ou(H)||void 0))}function Ou(e){let t=e.p;for(;t!==null;){const n=t.c;if(n!==null)return n;t=t.p}return null}let Kt=[];function Lu(){var e=Kt;Kt=[],Xl(e)}function Je(e){if(Kt.length===0){var t=Kt;queueMicrotask(()=>{t===Kt&&Lu()})}Kt.push(e)}const Xr=new WeakMap;function Wo(e){var t=C;if(t===null)return P.f|=it,e;if(b&&e instanceof Error&&!Xr.has(e)&&Xr.set(e,$u(e,t)),(t.f&St)===0&&(t.f&wn)===0)throw b&&!t.parent&&e instanceof Error&&jo(e),e;ut(e,t)}function ut(e,t){for(;t!==null;){if((t.f&jr)!==0){if((t.f&St)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw b&&e instanceof Error&&jo(e),e}function $u(e,t){var s,i,l;const n=Xe(e,"message");if(!(n&&!n.configurable)){for(var r=ra?"  ":"	",a=`
${r}in ${((s=t.fn)==null?void 0:s.name)||"<unknown>"}`,o=t.ctx;o!==null;)a+=`
${r}in ${(i=o.function)==null?void 0:i[qu].split("/").pop()}`,o=o.p;return{message:e.message+`
${a}
`,stack:(l=e.stack)==null?void 0:l.split(`
`).filter(c=>!c.includes("svelte/src/internal")).join(`
`)}}}function jo(e){const t=Xr.get(e);t&&(Mt(e,"message",{value:t.message}),Mt(e,"stack",{value:t.stack}))}const Iu=-7169;function X(e,t){e.f=e.f&Iu|t}function Yr(e){(e.f&we)!==0||e.deps===null?X(e,z):X(e,Pe)}function Uo(e){if(e!==null)for(const t of e)(t.f&re)===0||(t.f&st)===0||(t.f^=st,Uo(t.deps))}function Ko(e,t,n){(e.f&ae)!==0?t.add(e):(e.f&Pe)!==0&&n.add(e),Uo(e.deps),X(e,z)}const ur=new Set;let R=null,oe=null,Me=[],Qr=null,Zr=!1;const ka=class ka{constructor(){F(this,me);je(this,"current",new Map);je(this,"previous",new Map);F(this,rn,new Set);F(this,an,new Set);F(this,xt,0);F(this,on,0);F(this,Ln,null);F(this,$n,new Set);F(this,Rt,new Set);F(this,et,new Map);je(this,"is_fork",!1);F(this,sn,!1)}skip_effect(t){h(this,et).has(t)||h(this,et).set(t,{d:[],m:[]})}unskip_effect(t){var n=h(this,et).get(t);if(n){h(this,et).delete(t);for(var r of n.d)X(r,ae),Ce(r);for(r of n.m)X(r,Pe),Ce(r)}}process(t){var a;Me=[],this.apply();var n=[],r=[];for(const o of t)ne(this,me,Ca).call(this,o,n,r);if(ne(this,me,Fa).call(this)){ne(this,me,xa).call(this,r),ne(this,me,xa).call(this,n);for(const[o,s]of h(this,et))Zo(o,s)}else{for(const o of h(this,rn))o();h(this,rn).clear(),h(this,xt)===0&&ne(this,me,si).call(this),R=null,Xo(r),Xo(n),(a=h(this,Ln))==null||a.resolve()}oe=null}capture(t,n){n!==ee&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&it)===0&&(this.current.set(t,t.v),oe==null||oe.set(t,t.v))}activate(){R=this,this.apply()}deactivate(){R===this&&(R=null,oe=null)}flush(){if(this.activate(),Me.length>0){if(Bu(),R!==null&&R!==this)return}else h(this,xt)===0&&this.process([]);this.deactivate()}discard(){for(const t of h(this,an))t(this);h(this,an).clear()}increment(t){N(this,xt,h(this,xt)+1),t&&N(this,on,h(this,on)+1)}decrement(t){N(this,xt,h(this,xt)-1),t&&N(this,on,h(this,on)-1),!h(this,sn)&&(N(this,sn,!0),Je(()=>{N(this,sn,!1),ne(this,me,Fa).call(this)?Me.length>0&&this.flush():this.revive()}))}revive(){for(const t of h(this,$n))h(this,Rt).delete(t),X(t,ae),Ce(t);for(const t of h(this,Rt))X(t,Pe),Ce(t);this.flush()}oncommit(t){h(this,rn).add(t)}ondiscard(t){h(this,an).add(t)}settled(){return(h(this,Ln)??N(this,Ln,Fo())).promise}static ensure(){if(R===null){const t=R=new ka;ur.add(R),Je(()=>{R===t&&t.flush()})}return R}apply(){}};rn=new WeakMap,an=new WeakMap,xt=new WeakMap,on=new WeakMap,Ln=new WeakMap,$n=new WeakMap,Rt=new WeakMap,et=new WeakMap,sn=new WeakMap,me=new WeakSet,Fa=function(){return this.is_fork||h(this,on)>0},Ca=function(t,n,r){t.f^=z;for(var a=t.first;a!==null;){var o=a.f,s=(o&(Ne|qt))!==0,i=s&&(o&z)!==0,l=i||(o&pe)!==0||h(this,et).has(a);if(!l&&a.fn!==null){s?a.f^=z:(o&wn)!==0?n.push(a):Pn(a)&&((o&Ye)!==0&&h(this,Rt).add(a),zt(a));var c=a.first;if(c!==null){a=c;continue}}for(;a!==null;){var f=a.next;if(f!==null){a=f;break}a=a.parent}}},xa=function(t){for(var n=0;n<t.length;n+=1)Ko(t[n],h(this,$n),h(this,Rt))},si=function(){var a;if(ur.size>1){this.previous.clear();var t=oe,n=!0;for(const o of ur){if(o===this){n=!1;continue}const s=[];for(const[l,c]of this.current){if(o.current.has(l))if(n&&c!==o.current.get(l))o.current.set(l,c);else continue;s.push(l)}if(s.length===0)continue;const i=[...o.current.keys()].filter(l=>!this.current.has(l));if(i.length>0){var r=Me;Me=[];const l=new Set,c=new Map;for(const f of s)Yo(f,i,l,c);if(Me.length>0){R=o,o.apply();for(const f of Me)ne(a=o,me,Ca).call(a,f,[],[]);o.deactivate()}Me=r}}R=null,oe=t}ur.delete(this)};let ct=ka;function Bu(){Zr=!0;var e=b?new Set:null;try{for(var t=0;Me.length>0;){var n=ct.ensure();if(t++>1e3){if(b){var r=new Map;for(const o of n.current.keys())for(const[s,i]of o.updated??[]){var a=r.get(s);a||(a={error:i.error,count:0},r.set(s,a)),a.count+=i.count}for(const o of r.values())o.error&&console.error(o.error)}Gu()}if(n.process(Me),ft.clear(),b)for(const o of n.current.keys())e.add(o)}}finally{if(Me=[],Zr=!1,Qr=null,b)for(const o of e)o.updated=null}}function Gu(){try{au()}catch(e){b&&Mt(e,"stack",{value:""}),ut(e,Qr)}}let Fe=null;function Xo(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var r=e[n++];if((r.f&(Qe|pe))===0&&Pn(r)&&(Fe=new Set,zt(r),r.deps===null&&r.first===null&&r.nodes===null&&r.teardown===null&&r.ac===null&&_s(r),(Fe==null?void 0:Fe.size)>0)){ft.clear();for(const a of Fe){if((a.f&(Qe|pe))!==0)continue;const o=[a];let s=a.parent;for(;s!==null;)Fe.has(s)&&(Fe.delete(s),o.push(s)),s=s.parent;for(let i=o.length-1;i>=0;i--){const l=o[i];(l.f&(Qe|pe))===0&&zt(l)}}Fe.clear()}}Fe=null}}function Yo(e,t,n,r){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const a of e.reactions){const o=a.f;(o&re)!==0?Yo(a,t,n,r):(o&(ir|Ye))!==0&&(o&ae)===0&&Qo(a,t,r)&&(X(a,ae),Ce(a))}}function Qo(e,t,n){const r=n.get(e);if(r!==void 0)return r;if(e.deps!==null)for(const a of e.deps){if(wt.call(t,a))return!0;if((a.f&re)!==0&&Qo(a,t,n))return n.set(a,!0),!0}return n.set(e,!1),!1}function Ce(e){var t=Qr=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(wn|or|Wr))!==0&&(e.f&St)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var r=t.f;if(Zr&&t===C&&(r&Ye)!==0&&(r&Co)===0&&(r&St)!==0)return;if((r&(qt|Ne))!==0){if((r&z)===0)return;t.f^=z}}Me.push(t)}function Zo(e,t){if(!((e.f&Ne)!==0&&(e.f&z)!==0)){(e.f&ae)!==0?t.d.push(e):(e.f&Pe)!==0&&t.m.push(e),X(e,z);for(var n=e.first;n!==null;)Zo(n,t),n=n.next}}function Hu(e){let t=0,n=At(0),r;return b&&Ie(n,"createSubscriber version"),()=>{oa()&&(E(n),hc(()=>(t===0&&(r=ca(()=>e(()=>kn(n)))),t+=1,()=>{Je(()=>{t-=1,t===0&&(r==null||r(),r=void 0,kn(n))})})))}}var Vu=ot|Wt;function Wu(e,t,n,r){new ju(e,t,n,r)}class ju{constructor(t,n,r,a){F(this,J);je(this,"parent");je(this,"is_pending",!1);je(this,"transform_error");F(this,Ae);F(this,Aa,null);F(this,Ge);F(this,Tt);F(this,he);F(this,He,null);F(this,ve,null);F(this,De,null);F(this,tt,null);F(this,Dt,0);F(this,vt,0);F(this,ln,!1);F(this,un,new Set);F(this,cn,new Set);F(this,Ve,null);F(this,_r,Hu(()=>(N(this,Ve,At(h(this,Dt))),b&&Ie(h(this,Ve),"$effect.pending()"),()=>{N(this,Ve,null)})));var o;N(this,Ae,t),N(this,Ge,n),N(this,Tt,s=>{var i=C;i.b=this,i.f|=jr,r(s)}),this.parent=C.b,this.transform_error=a??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),N(this,he,Nn(()=>{ne(this,J,Ra).call(this)},Vu))}defer_effect(t){Ko(t,h(this,un),h(this,cn))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!h(this,Ge).pending}update_pending_count(t){ne(this,J,Ta).call(this,t),N(this,Dt,h(this,Dt)+t),!(!h(this,Ve)||h(this,ln))&&(N(this,ln,!0),Je(()=>{N(this,ln,!1),h(this,Ve)&&Yt(h(this,Ve),h(this,Dt))}))}get_effect_pending(){return h(this,_r).call(this),E(h(this,Ve))}error(t){var n=h(this,Ge).onerror;let r=h(this,Ge).failed;if(!n&&!r)throw t;h(this,He)&&(se(h(this,He)),N(this,He,null)),h(this,ve)&&(se(h(this,ve)),N(this,ve,null)),h(this,De)&&(se(h(this,De)),N(this,De,null));var a=!1,o=!1;const s=()=>{if(a){Pu();return}a=!0,o&&du(),h(this,De)!==null&&Nt(h(this,De),()=>{N(this,De,null)}),ne(this,J,Mr).call(this,()=>{ct.ensure(),ne(this,J,Ra).call(this)})},i=l=>{try{o=!0,n==null||n(l,s),o=!1}catch(c){ut(c,h(this,he)&&h(this,he).parent)}r&&N(this,De,ne(this,J,Mr).call(this,()=>{ct.ensure();try{return fe(()=>{var c=C;c.b=this,c.f|=jr,r(h(this,Ae),()=>l,()=>s)})}catch(c){return ut(c,h(this,he).parent),null}}))};Je(()=>{var l;try{l=this.transform_error(t)}catch(c){ut(c,h(this,he)&&h(this,he).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,c=>ut(c,h(this,he)&&h(this,he).parent)):i(l)})}}Ae=new WeakMap,Aa=new WeakMap,Ge=new WeakMap,Tt=new WeakMap,he=new WeakMap,He=new WeakMap,ve=new WeakMap,De=new WeakMap,tt=new WeakMap,Dt=new WeakMap,vt=new WeakMap,ln=new WeakMap,un=new WeakMap,cn=new WeakMap,Ve=new WeakMap,_r=new WeakMap,J=new WeakSet,id=function(){try{N(this,He,fe(()=>h(this,Tt).call(this,h(this,Ae))))}catch(t){this.error(t)}},ld=function(t){const n=h(this,Ge).failed;n&&N(this,De,fe(()=>{n(h(this,Ae),()=>t,()=>()=>{})}))},ud=function(){const t=h(this,Ge).pending;t&&(this.is_pending=!0,N(this,ve,fe(()=>t(h(this,Ae)))),Je(()=>{var n=N(this,tt,document.createDocumentFragment()),r=ze();n.append(r),N(this,He,ne(this,J,Mr).call(this,()=>(ct.ensure(),fe(()=>h(this,Tt).call(this,r))))),h(this,vt)===0&&(h(this,Ae).before(n),N(this,tt,null),Nt(h(this,ve),()=>{N(this,ve,null)}),ne(this,J,wr).call(this))}))},Ra=function(){try{if(this.is_pending=this.has_pending_snippet(),N(this,vt,0),N(this,Dt,0),N(this,He,fe(()=>{h(this,Tt).call(this,h(this,Ae))})),h(this,vt)>0){var t=N(this,tt,document.createDocumentFragment());gs(h(this,He),t);const n=h(this,Ge).pending;N(this,ve,fe(()=>n(h(this,Ae))))}else ne(this,J,wr).call(this)}catch(n){this.error(n)}},wr=function(){this.is_pending=!1;for(const t of h(this,un))X(t,ae),Ce(t);for(const t of h(this,cn))X(t,Pe),Ce(t);h(this,un).clear(),h(this,cn).clear()},Mr=function(t){var n=C,r=P,a=H;Re(h(this,he)),qe(h(this,he)),jt(h(this,he).ctx);try{return t()}catch(o){return Wo(o),null}finally{Re(n),qe(r),jt(a)}},Ta=function(t){var n;if(!this.has_pending_snippet()){this.parent&&ne(n=this.parent,J,Ta).call(n,t);return}N(this,vt,h(this,vt)+t),h(this,vt)===0&&(ne(this,J,wr).call(this),h(this,ve)&&Nt(h(this,ve),()=>{N(this,ve,null)}),h(this,tt)&&(h(this,Ae).before(h(this,tt)),N(this,tt,null)))};function Jo(e,t,n,r){const a=cr;var o=e.filter(u=>!u.settled);if(n.length===0&&o.length===0){r(t.map(a));return}var s=C,i=Uu(),l=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(u=>u.promise)):null;function c(u){i();try{r(u)}catch(d){(s.f&Qe)===0&&ut(d,s)}Jr()}if(n.length===0){l.then(()=>c(t.map(a)));return}function f(){i(),Promise.all(n.map(u=>Yu(u))).then(u=>c([...t.map(a),...u])).catch(u=>ut(u,s))}l?l.then(f):f()}function Uu(){var e=C,t=P,n=H,r=R;if(b)var a=Ut;return function(s=!0){Re(e),qe(t),jt(n),s&&(r==null||r.activate()),b&&lr(a)}}function Jr(e=!0){Re(null),qe(null),jt(null),e&&(R==null||R.deactivate()),b&&lr(null)}function Ku(){var e=C.b,t=R,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}const Xu=new Set;function cr(e){var t=re|ae,n=P!==null&&(P.f&re)!==0?P:null;return C!==null&&(C.f|=Wt),{ctx:H,deps:null,effects:null,equals:Io,f:t,fn:e,reactions:null,rv:0,v:ee,wv:0,parent:n??C,ac:null}}function Yu(e,t,n){C===null&&Jl();var a=void 0,o=At(ee);b&&(o.label=t);var s=!P,i=new Map;return dc(()=>{var d;var l=Fo();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(Jr)}catch(m){l.reject(m),Jr()}var c=R;if(s){var f=Ku();(d=i.get(c))==null||d.reject(kt),i.delete(c),i.set(c,l)}const u=(m,p=void 0)=>{if(c.activate(),p)p!==kt&&(o.f|=it,Yt(o,p));else{(o.f&it)!==0&&(o.f^=it),Yt(o,m);for(const[w,_]of i){if(i.delete(w),w===c)break;_.reject(kt)}}f&&f()};l.promise.then(u,m=>u(null,m||"unknown"))}),sa(()=>{for(const l of i.values())l.reject(kt)}),b&&(o.f|=ir),new Promise(l=>{function c(f){function u(){f===a?l(o):c(a)}f.then(u,u)}c(a)})}function zr(e){const t=cr(e);return bs(t),t}function zo(e){const t=cr(e);return t.equals=Bo,t}function es(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)se(t[n])}}let ea=[];function Qu(e){for(var t=e.parent;t!==null;){if((t.f&re)===0)return(t.f&Qe)===0?t:null;t=t.parent}return null}function ta(e){var t,n=C;if(Re(Qu(e)),b){let r=Xt;rs(new Set);try{wt.call(ea,e)&&zl(),ea.push(e),e.f&=~st,es(e),t=ua(e)}finally{Re(n),rs(r),ea.pop()}}else try{e.f&=~st,es(e),t=ua(e)}finally{Re(n)}return t}function ts(e){var t=ta(e);if(!e.equals(t)&&(e.wv=qs(),(!(R!=null&&R.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){X(e,z);return}pt||(oe!==null?(oa()||R!=null&&R.is_fork)&&oe.set(e,t):Yr(e))}function Zu(e){var t,n;if(e.effects!==null)for(const r of e.effects)(r.teardown||r.ac)&&((t=r.teardown)==null||t.call(r),(n=r.ac)==null||n.abort(kt),r.teardown=B,r.ac=null,Fn(r,0),ia(r))}function ns(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&zt(t)}let Xt=new Set;const ft=new Map;function rs(e){Xt=e}let na=!1;function Ju(){na=!0}function At(e,t){var n={f:0,v:e,reactions:null,equals:Io,rv:0,wv:0};return n}function dt(e,t){const n=At(e);return bs(n),n}function zu(e,t=!1,n=!0){const r=At(e);return t||(r.equals=Bo),r}function ht(e,t,n=!1){P!==null&&(!xe||(P.f&sr)!==0)&&Vo()&&(P.f&(re|Ye|ir|sr))!==0&&(Se===null||!wt.call(Se,e))&&fu();let r=n?Qt(t):t;return b&&Go(r,e.label),Yt(e,r)}function Yt(e,t){var a;if(!e.equals(t)){var n=e.v;pt?ft.set(e,t):ft.set(e,n),e.v=t;var r=ct.ensure();if(r.capture(e,n),b){if(C!==null){e.updated??(e.updated=new Map);const o=(((a=e.updated.get(""))==null?void 0:a.count)??0)+1;if(e.updated.set("",{error:null,count:o}),o>5){const s=xu("updated at");if(s!==null){let i=e.updated.get(s.stack);i||(i={error:s,count:0},e.updated.set(s.stack,i)),i.count++}}}C!==null&&(e.set_during_effect=!0)}if((e.f&re)!==0){const o=e;(e.f&ae)!==0&&ta(o),Yr(o)}e.wv=qs(),os(e,ae),C!==null&&(C.f&z)!==0&&(C.f&(Ne|qt))===0&&(ke===null?mc([e]):ke.push(e)),!r.is_fork&&Xt.size>0&&!na&&as()}return t}function as(){na=!1;for(const e of Xt)(e.f&z)!==0&&X(e,Pe),Pn(e)&&zt(e);Xt.clear()}function kn(e){ht(e,e.v+1)}function os(e,t){var n=e.reactions;if(n!==null)for(var r=n.length,a=0;a<r;a++){var o=n[a],s=o.f;if(b&&(s&sr)!==0){Xt.add(o);continue}var i=(s&ae)===0;if(i&&X(o,t),(s&re)!==0){var l=o;oe==null||oe.delete(l),(s&st)===0&&(s&we&&(o.f|=st),os(l,Pe))}else i&&((s&Ye)!==0&&Fe!==null&&Fe.add(o),Ce(o))}}const ec=/^[a-zA-Z_$][a-zA-Z_$0-9]*$/;function Qt(e){if(typeof e!="object"||e===null||lt in e)return e;const t=No(e);if(t!==Ul&&t!==Kl)return e;var n=new Map,r=Vr(e),a=dt(0),o=Ft,s=f=>{if(Ft===o)return f();var u=P,d=Ft;qe(null),Ms(o);var m=f();return qe(u),Ms(d),m};r&&(n.set("length",dt(e.length)),b&&(e=rc(e)));var i="";let l=!1;function c(f){if(!l){l=!0,i=f,Ie(a,`${i} version`);for(const[u,d]of n)Ie(d,Et(i,u));l=!1}}return new Proxy(e,{defineProperty(f,u,d){(!("value"in d)||d.configurable===!1||d.enumerable===!1||d.writable===!1)&&uu();var m=n.get(u);return m===void 0?s(()=>{var p=dt(d.value);return n.set(u,p),b&&typeof u=="string"&&Ie(p,Et(i,u)),p}):ht(m,d.value,!0),!0},deleteProperty(f,u){var d=n.get(u);if(d===void 0){if(u in f){const m=s(()=>dt(ee));n.set(u,m),kn(a),b&&Ie(m,Et(i,u))}}else ht(d,ee),kn(a);return!0},get(f,u,d){var _;if(u===lt)return e;if(b&&u===Ro)return c;var m=n.get(u),p=u in f;if(m===void 0&&(!p||(_=Xe(f,u))!=null&&_.writable)&&(m=s(()=>{var v=Qt(p?f[u]:ee),A=dt(v);return b&&Ie(A,Et(i,u)),A}),n.set(u,m)),m!==void 0){var w=E(m);return w===ee?void 0:w}return Reflect.get(f,u,d)},getOwnPropertyDescriptor(f,u){var d=Reflect.getOwnPropertyDescriptor(f,u);if(d&&"value"in d){var m=n.get(u);m&&(d.value=E(m))}else if(d===void 0){var p=n.get(u),w=p==null?void 0:p.v;if(p!==void 0&&w!==ee)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return d},has(f,u){var w;if(u===lt)return!0;var d=n.get(u),m=d!==void 0&&d.v!==ee||Reflect.has(f,u);if(d!==void 0||C!==null&&(!m||(w=Xe(f,u))!=null&&w.writable)){d===void 0&&(d=s(()=>{var _=m?Qt(f[u]):ee,v=dt(_);return b&&Ie(v,Et(i,u)),v}),n.set(u,d));var p=E(d);if(p===ee)return!1}return m},set(f,u,d,m){var K;var p=n.get(u),w=u in f;if(r&&u==="length")for(var _=d;_<p.v;_+=1){var v=n.get(_+"");v!==void 0?ht(v,ee):_ in f&&(v=s(()=>dt(ee)),n.set(_+"",v),b&&Ie(v,Et(i,_)))}if(p===void 0)(!w||(K=Xe(f,u))!=null&&K.writable)&&(p=s(()=>dt(void 0)),b&&Ie(p,Et(i,u)),ht(p,Qt(d)),n.set(u,p));else{w=p.v!==ee;var A=s(()=>Qt(d));ht(p,A)}var y=Reflect.getOwnPropertyDescriptor(f,u);if(y!=null&&y.set&&y.set.call(m,d),!w){if(r&&typeof u=="string"){var q=n.get("length"),k=Number(u);Number.isInteger(k)&&k>=q.v&&ht(q,k+1)}kn(a)}return!0},ownKeys(f){E(a);var u=Reflect.ownKeys(f).filter(p=>{var w=n.get(p);return w===void 0||w.v!==ee});for(var[d,m]of n)m.v!==ee&&!(d in f)&&u.push(d);return u},setPrototypeOf(){cu()}})}function Et(e,t){return typeof t=="symbol"?`${e}[Symbol(${t.description??""})]`:ec.test(t)?`${e}.${t}`:/^\d+$/.test(t)?`${e}[${t}]`:`${e}['${t}']`}function An(e){try{if(e!==null&&typeof e=="object"&&lt in e)return e[lt]}catch{}return e}function tc(e,t){return Object.is(An(e),An(t))}const nc=new Set(["copyWithin","fill","pop","push","reverse","shift","sort","splice","unshift"]);function rc(e){return new Proxy(e,{get(t,n,r){var a=Reflect.get(t,n,r);return nc.has(n)?function(...o){Ju();var s=a.apply(this,o);return as(),s}:a}})}function ac(){const e=Array.prototype,t=Array.__svelte_cleanup;t&&t();const{indexOf:n,lastIndexOf:r,includes:a}=e;e.indexOf=function(o,s){const i=n.call(this,o,s);if(i===-1){for(let l=s??0;l<this.length;l+=1)if(An(this[l])===o){Kr("array.indexOf(...)");break}}return i},e.lastIndexOf=function(o,s){const i=r.call(this,o,s??this.length-1);if(i===-1){for(let l=0;l<=(s??this.length-1);l+=1)if(An(this[l])===o){Kr("array.lastIndexOf(...)");break}}return i},e.includes=function(o,s){const i=a.call(this,o,s);if(!i){for(let l=0;l<this.length;l+=1)if(An(this[l])===o){Kr("array.includes(...)");break}}return i},Array.__svelte_cleanup=()=>{e.indexOf=n,e.lastIndexOf=r,e.includes=a}}var ss,ra,is,ls;function oc(){if(ss===void 0){ss=window,ra=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;is=Xe(t,"firstChild").get,ls=Xe(t,"nextSibling").get,Po(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Po(n)&&(n.__t=void 0),b&&(e.__svelte_meta=null,ac())}}function ze(e=""){return document.createTextNode(e)}function Zt(e){return is.call(e)}function En(e){return ls.call(e)}function ue(e,t){return Zt(e)}function G(e,t=!1){{var n=Zt(e);return n instanceof Comment&&n.data===""?En(n):n}}function V(e,t=1,n=!1){let r=e;for(;t--;)r=En(r);return r}function sc(e){e.textContent=""}function us(){return!1}function cs(e,t,n){return document.createElementNS(t??$o,e,void 0)}function ic(e,t){if(t){const n=document.body;e.autofocus=!0,Je(()=>{document.activeElement===n&&e.focus()})}}function aa(e){var t=P,n=C;qe(null),Re(null);try{return e()}finally{qe(t),Re(n)}}function lc(e){C===null&&(P===null&&ru(e),nu()),pt&&tu(e)}function uc(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function Be(e,t,n){var r=C;if(b)for(;r!==null&&(r.f&sr)!==0;)r=r.parent;r!==null&&(r.f&pe)!==0&&(e|=pe);var a={ctx:H,deps:null,nodes:null,f:e|ae|we,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null};if(b&&(a.component_function=Sn),n)try{zt(a)}catch(i){throw se(a),i}else t!==null&&Ce(a);var o=a;if(n&&o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&Wt)===0&&(o=o.first,(e&Ye)!==0&&(e&ot)!==0&&o!==null&&(o.f|=ot)),o!==null&&(o.parent=r,r!==null&&uc(o,r),P!==null&&(P.f&re)!==0&&(e&qt)===0)){var s=P;(s.effects??(s.effects=[])).push(o)}return a}function oa(){return P!==null&&!xe}function sa(e){const t=Be(or,null,!1);return X(t,z),t.teardown=e,t}function cc(e){lc("$effect"),b&&Mt(e,"name",{value:"$effect"});var t=C.f,n=!P&&(t&Ne)!==0&&(t&St)===0;if(n){var r=H;(r.e??(r.e=[])).push(e)}else return fs(e)}function fs(e){return Be(wn|Ql,e,!1)}function fc(e){ct.ensure();const t=Be(qt|Wt,e,!0);return(n={})=>new Promise(r=>{n.outro?Nt(t,()=>{se(t),r(void 0)}):(se(t),r(void 0))})}function ds(e){return Be(wn,e,!1)}function dc(e){return Be(ir|Wt,e,!0)}function hc(e,t=0){return Be(or|t,e,!0)}function Jt(e,t=[],n=[],r=[]){Jo(r,t,n,a=>{Be(or,()=>e(...a.map(E)),!0)})}function Nn(e,t=0){var n=Be(Ye|t,e,!0);return b&&(n.dev_stack=Ut),n}function hs(e,t=0){var n=Be(Wr|t,e,!0);return b&&(n.dev_stack=Ut),n}function fe(e){return Be(Ne|Wt,e,!0)}function ps(e){var t=e.teardown;if(t!==null){const n=pt,r=P;ys(!0),qe(null);try{t.call(null)}finally{ys(n),qe(r)}}}function ia(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const a=n.ac;a!==null&&aa(()=>{a.abort(kt)});var r=n.next;(n.f&qt)!==0?n.parent=null:se(n,t),n=r}}function pc(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&Ne)===0&&se(t),t=n}}function se(e,t=!0){var n=!1;(t||(e.f&Co)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(_c(e.nodes.start,e.nodes.end),n=!0),ia(e,t&&!n),Fn(e,0),X(e,Qe);var r=e.nodes&&e.nodes.t;if(r!==null)for(const o of r)o.stop();ps(e);var a=e.parent;a!==null&&a.first!==null&&_s(e),b&&(e.component_function=null),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function _c(e,t){for(;e!==null;){var n=e===t?null:En(e);e.remove(),e=n}}function _s(e){var t=e.parent,n=e.prev,r=e.next;n!==null&&(n.next=r),r!==null&&(r.prev=n),t!==null&&(t.first===e&&(t.first=r),t.last===e&&(t.last=n))}function Nt(e,t,n=!0){var r=[];ms(e,r,!0);var a=()=>{n&&se(e),t&&t()},o=r.length;if(o>0){var s=()=>--o||a();for(var i of r)i.out(s)}else a()}function ms(e,t,n){if((e.f&pe)===0){e.f^=pe;var r=e.nodes&&e.nodes.t;if(r!==null)for(const i of r)(i.is_global||n)&&t.push(i);for(var a=e.first;a!==null;){var o=a.next,s=(a.f&ot)!==0||(a.f&Ne)!==0&&(e.f&Ye)!==0;ms(a,t,s?n:!1),a=o}}}function la(e){vs(e,!0)}function vs(e,t){if((e.f&pe)!==0){e.f^=pe,(e.f&z)===0&&(X(e,ae),Ce(e));for(var n=e.first;n!==null;){var r=n.next,a=(n.f&ot)!==0||(n.f&Ne)!==0;vs(n,a?t:!1),n=r}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function gs(e,t){if(e.nodes)for(var n=e.nodes.start,r=e.nodes.end;n!==null;){var a=n===r?null:En(n);t.append(n),n=a}}let fr=!1,pt=!1;function ys(e){pt=e}let P=null,xe=!1;function qe(e){P=e}let C=null;function Re(e){C=e}let Se=null;function bs(e){P!==null&&(Se===null?Se=[e]:Se.push(e))}let de=null,_e=0,ke=null;function mc(e){ke=e}let ws=1,Pt=0,Ft=Pt;function Ms(e){Ft=e}function qs(){return++ws}function Pn(e){var t=e.f;if((t&ae)!==0)return!0;if(t&re&&(e.f&=~st),(t&Pe)!==0){for(var n=e.deps,r=n.length,a=0;a<r;a++){var o=n[a];if(Pn(o)&&ts(o),o.wv>e.wv)return!0}(t&we)!==0&&oe===null&&X(e,z)}return!1}function Ss(e,t,n=!0){var r=e.reactions;if(r!==null&&!(Se!==null&&wt.call(Se,e)))for(var a=0;a<r.length;a++){var o=r[a];(o.f&re)!==0?Ss(o,t,!1):t===o&&(n?X(o,ae):(o.f&z)!==0&&X(o,Pe),Ce(o))}}function ua(e){var w;var t=de,n=_e,r=ke,a=P,o=Se,s=H,i=xe,l=Ft,c=e.f;de=null,_e=0,ke=null,P=(c&(Ne|qt))===0?e:null,Se=null,jt(e.ctx),xe=!1,Ft=++Pt,e.ac!==null&&(aa(()=>{e.ac.abort(kt)}),e.ac=null);try{e.f|=Ur;var f=e.fn,u=f();e.f|=St;var d=e.deps,m=R==null?void 0:R.is_fork;if(de!==null){var p;if(m||Fn(e,_e),d!==null&&_e>0)for(d.length=_e+de.length,p=0;p<de.length;p++)d[_e+p]=de[p];else e.deps=d=de;if(oa()&&(e.f&we)!==0)for(p=_e;p<d.length;p++)((w=d[p]).reactions??(w.reactions=[])).push(e)}else!m&&d!==null&&_e<d.length&&(Fn(e,_e),d.length=_e);if(Vo()&&ke!==null&&!xe&&d!==null&&(e.f&(re|Pe|ae))===0)for(p=0;p<ke.length;p++)Ss(ke[p],e);if(a!==null&&a!==e){if(Pt++,a.deps!==null)for(let _=0;_<n;_+=1)a.deps[_].rv=Pt;if(t!==null)for(const _ of t)_.rv=Pt;ke!==null&&(r===null?r=ke:r.push(...ke))}return(e.f&it)!==0&&(e.f^=it),u}catch(_){return Wo(_)}finally{e.f^=Ur,de=t,_e=n,ke=r,P=a,Se=o,jt(s),xe=i,Ft=l}}function vc(e,t){let n=t.reactions;if(n!==null){var r=Wl.call(n,e);if(r!==-1){var a=n.length-1;a===0?n=t.reactions=null:(n[r]=n[a],n.pop())}}if(n===null&&(t.f&re)!==0&&(de===null||!wt.call(de,t))){var o=t;(o.f&we)!==0&&(o.f^=we,o.f&=~st),Yr(o),Zu(o),Fn(o,0)}}function Fn(e,t){var n=e.deps;if(n!==null)for(var r=t;r<n.length;r++)vc(e,n[r])}function zt(e){var t=e.f;if((t&Qe)===0){X(e,z);var n=C,r=fr;if(C=e,fr=!0,b){var a=Sn;Ho(e.component_function);var o=Ut;lr(e.dev_stack??Ut)}try{(t&(Ye|Wr))!==0?pc(e):ia(e),ps(e);var s=ua(e);e.teardown=typeof s=="function"?s:null,e.wv=ws;var i;b&&Cu&&(e.f&ae)!==0&&e.deps}finally{fr=r,C=n,b&&(Ho(a),lr(o))}}}function E(e){var t=e.f,n=(t&re)!==0;if(P!==null&&!xe){var r=C!==null&&(C.f&Qe)!==0;if(!r&&(Se===null||!wt.call(Se,e))){var a=P.deps;if((P.f&Ur)!==0)e.rv<Pt&&(e.rv=Pt,de===null&&a!==null&&a[_e]===e?_e++:de===null?de=[e]:de.push(e));else{(P.deps??(P.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[P]:wt.call(o,P)||o.push(P)}}}if(b&&Xu.delete(e),pt&&ft.has(e))return ft.get(e);if(n){var s=e;if(pt){var i=s.v;return((s.f&z)===0&&s.reactions!==null||As(s))&&(i=ta(s)),ft.set(s,i),i}var l=(s.f&we)===0&&!xe&&P!==null&&(fr||(P.f&we)!==0),c=(s.f&St)===0;Pn(s)&&(l&&(s.f|=we),ts(s)),l&&!c&&(ns(s),ks(s))}if(oe!=null&&oe.has(e))return oe.get(e);if((e.f&it)!==0)throw e.v;return e.v}function ks(e){if(e.f|=we,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&re)!==0&&(t.f&we)===0&&(ns(t),ks(t))}function As(e){if(e.v===ee)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(ft.has(t)||(t.f&re)!==0&&As(t))return!0;return!1}function ca(e){var t=xe;try{return xe=!0,e()}finally{xe=t}}function gc(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const yc=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function bc(e){return yc.includes(e)}const wc={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Mc(e){return e=e.toLowerCase(),wc[e]??e}const qc=["touchstart","touchmove"];function Sc(e){return qc.includes(e)}const Ct=Symbol("events"),Es=new Set,fa=new Set;function kc(e,t,n,r={}){function a(o){if(r.capture||da.call(t,o),!o.cancelBubble)return aa(()=>n==null?void 0:n.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Je(()=>{t.addEventListener(e,a,r)}):t.addEventListener(e,a,r),a}function Te(e,t,n){(t[Ct]??(t[Ct]={}))[e]=n}function Ns(e){for(var t=0;t<e.length;t++)Es.add(e[t]);for(var n of fa)n(e)}let Ps=null;function da(e){var _,v;var t=this,n=t.ownerDocument,r=e.type,a=((_=e.composedPath)==null?void 0:_.call(e))||[],o=a[0]||e.target;Ps=e;var s=0,i=Ps===e&&e[Ct];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[Ct]=t;return}var c=a.indexOf(t);if(c===-1)return;l<=c&&(s=l)}if(o=a[s]||e.target,o!==t){Mt(e,"currentTarget",{configurable:!0,get(){return o||n}});var f=P,u=C;qe(null),Re(null);try{for(var d,m=[];o!==null;){var p=o.assignedSlot||o.parentNode||o.host||null;try{var w=(v=o[Ct])==null?void 0:v[r];w!=null&&(!o.disabled||e.target===o)&&w.call(o,e)}catch(A){d?m.push(A):d=A}if(e.cancelBubble||p===t||p===null)break;o=p}if(d){for(let A of m)queueMicrotask(()=>{throw A});throw d}}finally{e[Ct]=t,delete e.currentTarget,qe(f),Re(u)}}}const ha=((ti=globalThis==null?void 0:globalThis.window)==null?void 0:ti.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Ac(e){return(ha==null?void 0:ha.createHTML(e))??e}function Fs(e){var t=cs("template");return t.innerHTML=Ac(e.replaceAll("<!>","<!---->")),t.content}function Cn(e,t){var n=C;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function en(e,t){var n=(t&wu)!==0,r=(t&Mu)!==0,a,o=!e.startsWith("<!>");return()=>{a===void 0&&(a=Fs(o?e:"<!>"+e),n||(a=Zt(a)));var s=r||ra?document.importNode(a,!0):a.cloneNode(!0);if(n){var i=Zt(s),l=s.lastChild;Cn(i,l)}else Cn(s,s);return s}}function Ec(e,t,n="svg"){var r=!e.startsWith("<!>"),a=`<${n}>${r?e:"<!>"+e}</${n}>`,o;return()=>{if(!o){var s=Fs(a),i=Zt(s);o=Zt(i)}var l=o.cloneNode(!0);return Cn(l,l),l}}function Nc(e,t){return Ec(e,t,"svg")}function W(){var e=document.createDocumentFragment(),t=document.createComment(""),n=ze();return e.append(t,n),Cn(t,n),e}function T(e,t){e!==null&&e.before(t)}function Cs(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function Pc(e,t){return Fc(e,t)}const dr=new Map;function Fc(e,{target:t,anchor:n,props:r={},events:a,context:o,intro:s=!0,transformError:i}){oc();var l=void 0,c=fc(()=>{var f=n??t.appendChild(ze());Wu(f,{pending:()=>{}},m=>{L({});var p=H;o&&(p.c=o),a&&(r.$$events=a),l=e(m,r)||{},$()},i);var u=new Set,d=m=>{for(var p=0;p<m.length;p++){var w=m[p];if(!u.has(w)){u.add(w);var _=Sc(w);for(const y of[t,document]){var v=dr.get(y);v===void 0&&(v=new Map,dr.set(y,v));var A=v.get(w);A===void 0?(y.addEventListener(w,da,{passive:_}),v.set(w,1)):v.set(w,A+1)}}}};return d(ar(Es)),fa.add(d),()=>{var _;for(var m of u)for(const v of[t,document]){var p=dr.get(v),w=p.get(m);--w==0?(v.removeEventListener(m,da),p.delete(m),p.size===0&&dr.delete(v)):p.set(m,w)}fa.delete(d),f!==n&&((_=f.parentNode)==null||_.removeChild(f))}});return pa.set(l,c),l}let pa=new WeakMap;function xs(e,t){const n=pa.get(e);return n?(pa.delete(e),n(t)):(b&&(lt in e?Nu():Au()),Promise.resolve())}class _a{constructor(t,n=!0){je(this,"anchor");F(this,Oe,new Map);F(this,We,new Map);F(this,ge,new Map);F(this,Ot,new Set);F(this,In,!0);F(this,Bn,()=>{var t=R;if(h(this,Oe).has(t)){var n=h(this,Oe).get(t),r=h(this,We).get(n);if(r)la(r),h(this,Ot).delete(n);else{var a=h(this,ge).get(n);a&&(h(this,We).set(n,a.effect),h(this,ge).delete(n),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),r=a.effect)}for(const[o,s]of h(this,Oe)){if(h(this,Oe).delete(o),o===t)break;const i=h(this,ge).get(s);i&&(se(i.effect),h(this,ge).delete(s))}for(const[o,s]of h(this,We)){if(o===n||h(this,Ot).has(o))continue;const i=()=>{if(Array.from(h(this,Oe).values()).includes(o)){var c=document.createDocumentFragment();gs(s,c),c.append(ze()),h(this,ge).set(o,{effect:s,fragment:c})}else se(s);h(this,Ot).delete(o),h(this,We).delete(o)};h(this,In)||!r?(h(this,Ot).add(o),Nt(s,i,!1)):i()}}});F(this,mr,t=>{h(this,Oe).delete(t);const n=Array.from(h(this,Oe).values());for(const[r,a]of h(this,ge))n.includes(r)||(se(a.effect),h(this,ge).delete(r))});this.anchor=t,N(this,In,n)}ensure(t,n){var r=R,a=us();if(n&&!h(this,We).has(t)&&!h(this,ge).has(t))if(a){var o=document.createDocumentFragment(),s=ze();o.append(s),h(this,ge).set(t,{effect:fe(()=>n(s)),fragment:o})}else h(this,We).set(t,fe(()=>n(this.anchor)));if(h(this,Oe).set(r,t),a){for(const[i,l]of h(this,We))i===t?r.unskip_effect(l):r.skip_effect(l);for(const[i,l]of h(this,ge))i===t?r.unskip_effect(l.effect):r.skip_effect(l.effect);r.oncommit(h(this,Bn)),r.ondiscard(h(this,mr))}else h(this,Bn).call(this)}}Oe=new WeakMap,We=new WeakMap,ge=new WeakMap,Ot=new WeakMap,In=new WeakMap,Bn=new WeakMap,mr=new WeakMap;function hr(e,t,n=!1){var r=new _a(e),a=n?ot:0;function o(s,i){r.ensure(s,i)}Nn(()=>{var s=!1;t((i,l=0)=>{s=!0,o(l,i)}),s||o(!1,null)},a)}function Cc(e,t){return t}function xc(e,t,n){for(var r=[],a=t.length,o,s=t.length,i=0;i<a;i++){let u=t[i];Nt(u,()=>{if(o){if(o.pending.delete(u),o.done.add(u),o.pending.size===0){var d=e.outrogroups;ma(ar(o.done)),d.delete(o),d.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var l=r.length===0&&n!==null;if(l){var c=n,f=c.parentNode;sc(f),f.append(c),e.items.clear()}ma(t,!l)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function ma(e,t=!0){for(var n=0;n<e.length;n++)se(e[n],t)}var Rs;function va(e,t,n,r,a,o=null){var s=e,i=new Map,l=(t&Lo)!==0;if(l){var c=e;s=c.appendChild(ze())}var f=null,u=zo(()=>{var v=n();return Vr(v)?v:v==null?[]:ar(v)}),d,m=!0;function p(){_.fallback=f,Rc(_,d,s,t,r),f!==null&&(d.length===0?(f.f&Ze)===0?la(f):(f.f^=Ze,Rn(f,null,s)):Nt(f,()=>{f=null}))}var w=Nn(()=>{d=E(u);for(var v=d.length,A=new Set,y=R,q=us(),k=0;k<v;k+=1){var K=d[k],x=r(K,k);if(b){var ye=r(K,k);x!==ye&&eu(String(k),String(x),String(ye))}var ie=m?null:i.get(x);ie?(ie.v&&Yt(ie.v,K),ie.i&&Yt(ie.i,k),q&&y.unskip_effect(ie.e)):(ie=Tc(i,m?s:Rs??(Rs=ze()),K,x,k,a,t,n),m||(ie.e.f|=Ze),i.set(x,ie)),A.add(x)}if(v===0&&o&&!f&&(m?f=fe(()=>o(s)):(f=fe(()=>o(Rs??(Rs=ze()))),f.f|=Ze)),v>A.size&&(b?Dc(d,r):Oo("","","")),!m)if(q){for(const[nt,g]of i)A.has(nt)||y.skip_effect(g.e);y.oncommit(p),y.ondiscard(()=>{})}else p();E(u)}),_={effect:w,items:i,outrogroups:null,fallback:f};m=!1}function xn(e){for(;e!==null&&(e.f&Ne)===0;)e=e.next;return e}function Rc(e,t,n,r,a){var nt,g,te,Lt,be,Gn,Hn,Vn,vr;var o=(r&_u)!==0,s=t.length,i=e.items,l=xn(e.effect.first),c,f=null,u,d=[],m=[],p,w,_,v;if(o)for(v=0;v<s;v+=1)p=t[v],w=a(p,v),_=i.get(w).e,(_.f&Ze)===0&&((g=(nt=_.nodes)==null?void 0:nt.a)==null||g.measure(),(u??(u=new Set)).add(_));for(v=0;v<s;v+=1){if(p=t[v],w=a(p,v),_=i.get(w).e,e.outrogroups!==null)for(const Le of e.outrogroups)Le.pending.delete(_),Le.done.delete(_);if((_.f&Ze)!==0)if(_.f^=Ze,_===l)Rn(_,null,n);else{var A=f?f.next:l;_===e.effect.last&&(e.effect.last=_.prev),_.prev&&(_.prev.next=_.next),_.next&&(_.next.prev=_.prev),_t(e,f,_),_t(e,_,A),Rn(_,A,n),f=_,d=[],m=[],l=xn(f.next);continue}if((_.f&pe)!==0&&(la(_),o&&((Lt=(te=_.nodes)==null?void 0:te.a)==null||Lt.unfix(),(u??(u=new Set)).delete(_))),_!==l){if(c!==void 0&&c.has(_)){if(d.length<m.length){var y=m[0],q;f=y.prev;var k=d[0],K=d[d.length-1];for(q=0;q<d.length;q+=1)Rn(d[q],y,n);for(q=0;q<m.length;q+=1)c.delete(m[q]);_t(e,k.prev,K.next),_t(e,f,k),_t(e,K,y),l=y,f=K,v-=1,d=[],m=[]}else c.delete(_),Rn(_,l,n),_t(e,_.prev,_.next),_t(e,_,f===null?e.effect.first:f.next),_t(e,f,_),f=_;continue}for(d=[],m=[];l!==null&&l!==_;)(c??(c=new Set)).add(l),m.push(l),l=xn(l.next);if(l===null)continue}(_.f&Ze)===0&&d.push(_),f=_,l=xn(_.next)}if(e.outrogroups!==null){for(const Le of e.outrogroups)Le.pending.size===0&&(ma(ar(Le.done)),(be=e.outrogroups)==null||be.delete(Le));e.outrogroups.size===0&&(e.outrogroups=null)}if(l!==null||c!==void 0){var x=[];if(c!==void 0)for(_ of c)(_.f&pe)===0&&x.push(_);for(;l!==null;)(l.f&pe)===0&&l!==e.fallback&&x.push(l),l=xn(l.next);var ye=x.length;if(ye>0){var ie=(r&Lo)!==0&&s===0?n:null;if(o){for(v=0;v<ye;v+=1)(Hn=(Gn=x[v].nodes)==null?void 0:Gn.a)==null||Hn.measure();for(v=0;v<ye;v+=1)(vr=(Vn=x[v].nodes)==null?void 0:Vn.a)==null||vr.fix()}xc(e,x,ie)}}o&&Je(()=>{var Le,gr;if(u!==void 0)for(_ of u)(gr=(Le=_.nodes)==null?void 0:Le.a)==null||gr.apply()})}function Tc(e,t,n,r,a,o,s,i){var l=(s&hu)!==0?(s&mu)===0?zu(n,!1,!1):At(n):null,c=(s&pu)!==0?At(a):null;return b&&l&&(l.trace=()=>{i()[(c==null?void 0:c.v)??a]}),{v:l,i:c,e:fe(()=>(o(t,l??n,c??a,i),()=>{e.delete(r)}))}}function Rn(e,t,n){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end,o=t&&(t.f&Ze)===0?t.nodes.start:n;r!==null;){var s=En(r);if(o.before(r),r===a)return;r=s}}function _t(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function Dc(e,t){const n=new Map,r=e.length;for(let a=0;a<r;a++){const o=t(e[a],a);if(n.has(o)){const s=String(n.get(o)),i=String(a);let l=String(o);l.startsWith("[object ")&&(l=null),Oo(s,i,l)}n.set(o,a)}}function j(e,t,...n){var r=new _a(e);Nn(()=>{const a=t()??null;b&&a==null&&ou(),r.ensure(a,a&&(o=>a(o,...n)))},ot)}function Oc(e,t,n,r,a,o){var s=null,i=e,l=new _a(i,!1);Nn(()=>{const c=t()||null;var f=Su;if(c===null){l.ensure(null,null);return}return l.ensure(c,u=>{if(c){if(s=cs(c,f),Cn(s,s),r){var d=s.appendChild(ze());r(s,d)}C.nodes.end=s,u.before(s)}}),()=>{}},ot),sa(()=>{})}function Lc(e,t){var n=void 0,r;hs(()=>{n!==(n=t())&&(r&&(se(r),r=null),n&&(r=fe(()=>{ds(()=>n(e))})))})}function Ts(e){var t,n,r="";if(typeof e=="string"||typeof e=="number")r+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(n=Ts(e[t]))&&(r&&(r+=" "),r+=n)}else for(n in e)e[n]&&(r&&(r+=" "),r+=n);return r}function $c(){for(var e,t,n=0,r="",a=arguments.length;n<a;n++)(e=arguments[n])&&(t=Ts(e))&&(r&&(r+=" "),r+=t);return r}function Ds(e){return typeof e=="object"?$c(e):e??""}const Os=[...` 	
\r\f \v\uFEFF`];function Ic(e,t,n){var r=e==null?"":""+e;if(t&&(r=r?r+" "+t:t),n){for(var a of Object.keys(n))if(n[a])r=r?r+" "+a:a;else if(r.length)for(var o=a.length,s=0;(s=r.indexOf(a,s))>=0;){var i=s+o;(s===0||Os.includes(r[s-1]))&&(i===r.length||Os.includes(r[i]))?r=(s===0?"":r.substring(0,s))+r.substring(i+1):s=i}}return r===""?null:r}function Ls(e,t=!1){var n=t?" !important;":";",r="";for(var a of Object.keys(e)){var o=e[a];o!=null&&o!==""&&(r+=" "+a+": "+o+n)}return r}function ga(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Bc(e,t){if(t){var n="",r,a;if(Array.isArray(t)?(r=t[0],a=t[1]):r=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,i=!1,l=[];r&&l.push(...Object.keys(r).map(ga)),a&&l.push(...Object.keys(a).map(ga));var c=0,f=-1;const w=e.length;for(var u=0;u<w;u++){var d=e[u];if(i?d==="/"&&e[u-1]==="*"&&(i=!1):o?o===d&&(o=!1):d==="/"&&e[u+1]==="*"?i=!0:d==='"'||d==="'"?o=d:d==="("?s++:d===")"&&s--,!i&&o===!1&&s===0){if(d===":"&&f===-1)f=u;else if(d===";"||u===w-1){if(f!==-1){var m=ga(e.substring(c,f).trim());if(!l.includes(m)){d!==";"&&u++;var p=e.substring(c,u).trim();n+=" "+p+";"}}c=u+1,f=-1}}}}return r&&(n+=Ls(r)),a&&(n+=Ls(a,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function ya(e,t,n,r,a,o){var s=e.__className;if(s!==n||s===void 0){var i=Ic(n,r,o);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=n}else if(o&&a!==o)for(var l in o){var c=!!o[l];(a==null||c!==!!a[l])&&e.classList.toggle(l,c)}return o}function ba(e,t={},n,r){for(var a in n){var o=n[a];t[a]!==o&&(n[a]==null?e.style.removeProperty(a):e.style.setProperty(a,o,r))}}function Gc(e,t,n,r){var a=e.__style;if(a!==t){var o=Bc(t,r);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else r&&(Array.isArray(r)?(ba(e,n==null?void 0:n[0],r[0]),ba(e,n==null?void 0:n[1],r[1],"important")):ba(e,n,r));return r}function wa(e,t,n=!1){if(e.multiple){if(t==null)return;if(!Vr(t))return Eu();for(var r of e.options)r.selected=t.includes($s(r));return}for(r of e.options){var a=$s(r);if(tc(a,t)){r.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function Hc(e){var t=new MutationObserver(()=>{wa(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),sa(()=>{t.disconnect()})}function $s(e){return"__value"in e?e.__value:e.value}const Tn=Symbol("class"),Dn=Symbol("style"),Is=Symbol("is custom element"),Bs=Symbol("is html"),Vc=To?"option":"OPTION",Wc=To?"select":"SELECT";function jc(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function S(e,t,n,r){var a=Hs(e);a[t]!==(a[t]=n)&&(t==="loading"&&(e[Zl]=n),n==null?e.removeAttribute(t):typeof n!="string"&&Ws(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function Uc(e,t,n,r,a=!1,o=!1){var s=Hs(e),i=s[Is],l=!s[Bs],c=t||{},f=e.nodeName===Vc;for(var u in t)u in n||(n[u]=null);n.class?n.class=Ds(n.class):n[Tn]&&(n.class=null),n[Dn]&&(n.style??(n.style=null));var d=Ws(e);for(const y in n){let q=n[y];if(f&&y==="value"&&q==null){e.value=e.__value="",c[y]=q;continue}if(y==="class"){var m=e.namespaceURI==="http://www.w3.org/1999/xhtml";ya(e,m,q,r,t==null?void 0:t[Tn],n[Tn]),c[y]=q,c[Tn]=n[Tn];continue}if(y==="style"){Gc(e,q,t==null?void 0:t[Dn],n[Dn]),c[y]=q,c[Dn]=n[Dn];continue}var p=c[y];if(!(q===p&&!(q===void 0&&e.hasAttribute(y)))){c[y]=q;var w=y[0]+y[1];if(w!=="$$")if(w==="on"){const k={},K="$$"+y;let x=y.slice(2);var _=bc(x);if(gc(x)&&(x=x.slice(0,-7),k.capture=!0),!_&&p){if(q!=null)continue;e.removeEventListener(x,c[K],k),c[K]=null}if(_)Te(x,e,q),Ns([x]);else if(q!=null){let ye=function(ie){c[y].call(this,ie)};c[K]=kc(x,e,ye,k)}}else if(y==="style")S(e,y,q);else if(y==="autofocus")ic(e,!!q);else if(!i&&(y==="__value"||y==="value"&&q!=null))e.value=e.__value=q;else if(y==="selected"&&f)jc(e,q);else{var v=y;l||(v=Mc(v));var A=v==="defaultValue"||v==="defaultChecked";if(q==null&&!i&&!A)if(s[y]=null,v==="value"||v==="checked"){let k=e;const K=t===void 0;if(v==="value"){let x=k.defaultValue;k.removeAttribute(v),k.defaultValue=x,k.value=k.__value=K?x:null}else{let x=k.defaultChecked;k.removeAttribute(v),k.defaultChecked=x,k.checked=K?x:!1}}else e.removeAttribute(y);else A||d.includes(v)&&(i||typeof q!="string")?(e[v]=q,v in s&&(s[v]=ee)):typeof q!="function"&&S(e,v,q)}}}return c}function Gs(e,t,n=[],r=[],a=[],o,s=!1,i=!1){Jo(a,n,r,l=>{var c=void 0,f={},u=e.nodeName===Wc,d=!1;if(hs(()=>{var p=t(...l.map(E)),w=Uc(e,c,p,o,s,i);d&&u&&"value"in p&&wa(e,p.value);for(let v of Object.getOwnPropertySymbols(f))p[v]||se(f[v]);for(let v of Object.getOwnPropertySymbols(p)){var _=p[v];v.description===ku&&(!c||_!==c[v])&&(f[v]&&se(f[v]),f[v]=fe(()=>Lc(e,()=>_))),w[v]=_}c=w}),u){var m=e;ds(()=>{wa(m,c.value,!0),Hc(m)})}d=!0})}function Hs(e){return e.__attributes??(e.__attributes={[Is]:e.nodeName.includes("-"),[Bs]:e.namespaceURI===$o})}var Vs=new Map;function Ws(e){var t=e.getAttribute("is")||e.nodeName,n=Vs.get(t);if(n)return n;Vs.set(t,n=[]);for(var r,a=e,o=Element.prototype;o!==a;){r=jl(a);for(var s in r)r[s].set&&n.push(s);a=No(a)}return n}let pr=!1;function Kc(e){var t=pr;try{return pr=!1,[e(),pr]}finally{pr=t}}const Xc={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return b&&iu(`${e.name}.${String(t)}`),!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function U(e,t,n){return new Proxy(b?{props:e,exclude:t,name:n,other:{},to_proxy:[]}:{props:e,exclude:t},Xc)}const Yc={get(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(bn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r)return r[t]}},set(e,t,n){let r=e.props.length;for(;r--;){let a=e.props[r];bn(a)&&(a=a());const o=Xe(a,t);if(o&&o.set)return o.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(bn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r){const a=Xe(r,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===lt||t===xo)return!1;for(let n of e.props)if(bn(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(bn(n)&&(n=n()),!!n){for(const r in n)t.includes(r)||t.push(r);for(const r of Object.getOwnPropertySymbols(n))t.includes(r)||t.push(r)}return t}};function Y(...e){return new Proxy({props:e},Yc)}function tn(e,t,n,r){var A;var a=(n&yu)!==0,o=(n&bu)!==0,s=r,i=!0,l=()=>(i&&(i=!1,s=o?ca(r):r),s),c;if(a){var f=lt in e||xo in e;c=((A=Xe(e,t))==null?void 0:A.set)??(f&&t in e?y=>e[t]=y:void 0)}var u,d=!1;a?[u,d]=Kc(()=>e[t]):u=e[t],u===void 0&&r!==void 0&&(u=l(),c&&(su(t),c(u)));var m;if(m=()=>{var y=e[t];return y===void 0?l():(i=!0,y)},(n&gu)===0)return m;if(c){var p=e.$$legacy;return(function(y,q){return arguments.length>0?((!q||p||d)&&c(q?m():y),y):m()})}var w=!1,_=((n&vu)!==0?cr:zo)(()=>(w=!1,m()));b&&(_.label=t),a&&E(_);var v=C;return(function(y,q){if(arguments.length>0){const k=q?E(_):a?Qt(y):y;return ht(_,k),w=!0,s!==void 0&&(s=k),y}return pt&&w||(v.f&Qe)!==0?_.v:E(_)})}if(b){let e=function(t){if(!(t in globalThis)){let n;Object.defineProperty(globalThis,t,{configurable:!0,get:()=>{if(n!==void 0)return n;lu(t)},set:r=>{n=r}})}};e("$state"),e("$effect"),e("$derived"),e("$inspect"),e("$props"),e("$bindable")}function Qc(e){H===null&&Do("onMount"),cc(()=>{const t=ca(e);if(typeof t=="function")return t})}const Zc="5";typeof window<"u"&&((ni=window.__svelte??(window.__svelte={})).v??(ni.v=new Set)).add(Zc);/**
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
 */const Jc={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const zc=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const ef=Symbol("lucide-context"),tf=()=>Tu(ef);var nf=Nc("<svg><!><!></svg>");function Q(e,t){L(t,!0);const n=tf()??{},r=tn(t,"color",19,()=>n.color??"currentColor"),a=tn(t,"size",19,()=>n.size??24),o=tn(t,"strokeWidth",19,()=>n.strokeWidth??2),s=tn(t,"absoluteStrokeWidth",19,()=>n.absoluteStrokeWidth??!1),i=tn(t,"iconNode",19,()=>[]),l=U(t,["$$slots","$$events","$$legacy","name","color","size","strokeWidth","absoluteStrokeWidth","iconNode","children"]),c=zr(()=>s()?Number(o())*24/Number(a()):o());var f=nf();Gs(f,m=>({...Jc,...m,...l,width:a(),height:a(),stroke:r(),"stroke-width":E(c),class:["lucide-icon lucide",n.class,t.name&&`lucide-${t.name}`,t.class]}),[()=>!t.children&&!zc(l)&&{"aria-hidden":"true"}]);var u=ue(f);va(u,17,i,Cc,(m,p)=>{var w=zr(()=>Yl(E(p),2));let _=()=>E(w)[0],v=()=>E(w)[1];var A=W(),y=G(A);Oc(y,_,!0,(q,k)=>{Gs(q,()=>({...v()}))}),T(m,A)});var d=V(u);j(d,()=>t.children??B),T(e,f),$()}function rf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];Q(e,Y({name:"chart-line"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function af(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 9 6 6 6-6"}]];Q(e,Y({name:"chevron-down"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function of(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"}],["path",{d:"M12 17h.01"}]];Q(e,Y({name:"circle-question-mark"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function sf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 12 18z"}],["path",{d:"M2 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 2 18z"}]];Q(e,Y({name:"fast-forward"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function lf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]];Q(e,Y({name:"folder-open"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function uf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["rect",{x:"14",y:"3",width:"5",height:"18",rx:"1"}],["rect",{x:"5",y:"3",width:"5",height:"18",rx:"1"}]];Q(e,Y({name:"pause"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function cf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"}]];Q(e,Y({name:"play"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function ff(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m15 14 5-5-5-5"}],["path",{d:"M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13"}]];Q(e,Y({name:"redo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function df(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Q(e,Y({name:"refresh-cw"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function hf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m2 9 3-3 3 3"}],["path",{d:"M13 18H7a2 2 0 0 1-2-2V6"}],["path",{d:"m22 15-3 3-3-3"}],["path",{d:"M11 6h6a2 2 0 0 1 2 2v10"}]];Q(e,Y({name:"repeat-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function pf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 12 18z"}],["path",{d:"M22 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 22 18z"}]];Q(e,Y({name:"rewind"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function _f(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]];Q(e,Y({name:"scissors"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function mf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Q(e,Y({name:"settings"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function vf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];Q(e,Y({name:"sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function gf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]];Q(e,Y({name:"timer-reset"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function yf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Q(e,Y({name:"trash-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function bf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"}]];Q(e,Y({name:"undo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function wf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}]];Q(e,Y({name:"volume-1"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function Mf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}],["path",{d:"M19.364 18.364a9 9 0 0 0 0-12.728"}]];Q(e,Y({name:"volume-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function qf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]];Q(e,Y({name:"volume-x"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}function Sf(e,t){L(t,!0);/**
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
 */let n=U(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}]];Q(e,Y({name:"waves"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=W(),i=G(s);j(i,()=>t.children??B),T(a,s)},$$slots:{default:!0}})),$()}var kf=en('<span aria-hidden="true"><!></span>');function mt(e,t){L(t,!0);const n=tn(t,"className",3,""),r=zr(()=>["aqe-button-icon",n()].filter(Boolean).join(" "));var a=kf(),o=ue(a);{var s=g=>{rf(g,{size:14,strokeWidth:2})},i=g=>{af(g,{size:14,strokeWidth:2})},l=g=>{of(g,{size:14,strokeWidth:2})},c=g=>{sf(g,{size:14,strokeWidth:2})},f=g=>{lf(g,{size:14,strokeWidth:2})},u=g=>{uf(g,{size:14,strokeWidth:2})},d=g=>{cf(g,{size:14,strokeWidth:2})},m=g=>{ff(g,{size:14,strokeWidth:2})},p=g=>{df(g,{size:14,strokeWidth:2})},w=g=>{hf(g,{size:14,strokeWidth:2})},_=g=>{pf(g,{size:14,strokeWidth:2})},v=g=>{_f(g,{size:14,strokeWidth:2})},A=g=>{mf(g,{size:14,strokeWidth:2})},y=g=>{vf(g,{size:14,strokeWidth:2})},q=g=>{gf(g,{size:14,strokeWidth:2})},k=g=>{yf(g,{size:14,strokeWidth:2})},K=g=>{bf(g,{size:14,strokeWidth:2})},x=g=>{wf(g,{size:14,strokeWidth:2})},ye=g=>{Mf(g,{size:14,strokeWidth:2})},ie=g=>{qf(g,{size:14,strokeWidth:2})},nt=g=>{Sf(g,{size:14,strokeWidth:2})};hr(o,g=>{t.icon==="chart-line"?g(s):t.icon==="chevron-down"?g(i,1):t.icon==="circle-help"?g(l,2):t.icon==="fast-forward"?g(c,3):t.icon==="folder-open"?g(f,4):t.icon==="pause"?g(u,5):t.icon==="play"?g(d,6):t.icon==="redo-2"?g(m,7):t.icon==="refresh-cw"?g(p,8):t.icon==="repeat-2"?g(w,9):t.icon==="rewind"?g(_,10):t.icon==="scissors"?g(v,11):t.icon==="settings"?g(A,12):t.icon==="sparkles"?g(y,13):t.icon==="timer-reset"?g(q,14):t.icon==="trash-2"?g(k,15):t.icon==="undo-2"?g(K,16):t.icon==="volume-1"?g(x,17):t.icon==="volume-2"?g(ye,18):t.icon==="volume-x"?g(ie,19):t.icon==="waves"&&g(nt,20)})}Jt(()=>ya(a,1,Ds(E(r)))),T(e,a),$()}function js(){return document.body.dataset.aqeBusy==="true"}function Us(e,t,n){if(js())return;const r=D(n);if(!r)return;const a=ao(r,e);mn(r),a&&(typeof t.focus=="function"&&t.focus(),at(r,{clearAudio:!0}),hi(a),window.__aqeActiveField=n,le.info("region delete request queued",{ord:n,sourceFilename:a.sourceFilename,selectionStartMs:a.selectionStartMs,selectionEndMs:a.selectionEndMs,durationMs:a.durationMs,trigger:e,playbackActive:a.playbackActive}),Gt(n,!0,Da("aqe:delete-selection")),It(n,"aqe:delete-selection"))}function Af(e,t){if(e.key!=="Backspace")return;const n=D(t);if(!(!n||document.activeElement!==n||js())){if(!ao(n,"backspace")){mn(n);return}e.preventDefault(),Us("backspace",n,t)}}var Ef=en('<button type="button" class="aqe-button aqe-icon-only aqe-repeat-button" title="Repeat selected region, or the whole graph when no region is selected." aria-label="Repeat playback"><!> <span class="aqe-button-label">Repeat</span></button>'),Nf=en('<button type="button" class="aqe-button aqe-menu-item" data-aqe-button-state="default" role="menuitem"><!> <span class="aqe-button-label"> </span></button>'),Pf=en('<details class="aqe-menu"><summary class="aqe-button aqe-menu-summary" title="Denoise audio" aria-label="Denoise audio"><!> <span class="aqe-button-label">Denoise</span> <!></summary> <div class="aqe-menu-items" role="menu"></div></details>'),Ff=en('<button type="button"><!> <!> <span class="aqe-button-label"> </span></button> <!> <!>',1),Cf=en('<div class="aqe-controls"><!> <button type="button" class="aqe-button aqe-delete-region-button" data-aqe-command="aqe:delete-selection" data-aqe-button-state="default" title="Delete selected region" aria-label="Delete selected region" hidden=""><!> <span class="aqe-button-label">Delete Region</span></button> <span class="aqe-status"></span> <details class="aqe-help"><summary class="aqe-help-summary" title="Show editor help"><!> <span>Help</span></summary> <div class="aqe-help-body"><p>Holding Shift on the graph selects a region. Playing with a selected region plays only that region; Repeat loops the selected region, or the full graph when no region is selected.</p> <p>Play starts or pauses audio. Graph shows the pitch and loudness graph. Folder opens the current audio file. -L and -R trim 100 ms from the left or right. Shorten Pauses speeds up long internal pauses. Denoise Standard uses DeepFilterNet, and Denoise RNNoise uses RNNoise. Slower and Faster change speed. Volume - and Volume + change loudness. Undo and Redo move through generated audio edits. Settings opens the add-on settings.</p> <p>In the graph, grey is loudness and lines are pitch of the voice.</p></div></details> <div class="aqe-visualizer" data-anchor-ms="0" data-cursor-ms="0" data-progress-ms="0" data-graph-active="false" data-graph-busy="false" data-has-track="false" data-playback-state="stopped" data-playback-engine="" data-playback-start-ms="0" data-playback-end-ms="0" data-playback-region-mode="full" data-resume-requires-restart="false" data-selection-active="false" data-selection-start-ms="" data-selection-end-ms="" data-selection-draft-active="false" data-selection-draft-start-ms="" data-selection-draft-end-ms="" role="button" aria-label="Audio graph" tabindex="0" hidden=""><audio class="aqe-audio-clock" preload="metadata" hidden=""></audio> <svg class="aqe-visualizer-svg" preserveAspectRatio="xMinYMin meet" role="img" aria-label="Audio pitch and intensity visualization"><rect class="aqe-selection" width="0" visibility="hidden"></rect><path class="aqe-intensity" d=""></path><g class="aqe-pitch"></g><g class="aqe-labels"></g><g class="aqe-x-axis"></g><line class="aqe-selection-edge aqe-selection-start" visibility="hidden"></line><line class="aqe-selection-edge aqe-selection-end" visibility="hidden"></line><line class="aqe-cursor"></line></svg> <div class="aqe-visualizer-meta"><span class="aqe-spinner" hidden="" aria-hidden="true"></span> <span class="aqe-cursor-label">0 ms</span> <span class="aqe-visualizer-status"></span></div></div></div>');function xf(e,t){var nt;L(t,!0);const n=((nt=window.__AQE_EDITOR_CONFIG__)==null?void 0:nt.repeatPlaybackByDefault)===!0;function r(g){const Lt=g.currentTarget.ariaPressed!=="true";ql(t.target.ord,Lt)}Qc(()=>{const g=D(t.target.ord);g&&(vl(g),El(g),wl(g))});var a=Cf(),o=ue(a);va(o,17,()=>O,g=>g.command,(g,te)=>{var Lt=Ff(),be=G(Lt);let Gn;var Hn=ue(be);mt(Hn,{className:"aqe-button-icon-default",get icon(){return E(te).icon}});var Vn=V(Hn,2);{var vr=ce=>{mt(ce,{className:"aqe-button-icon-active",get icon(){return E(te).activeIcon}})};hr(Vn,ce=>{E(te).activeIcon&&ce(vr)})}var Le=V(Vn,2),gr=ue(Le),ri=V(be,2);{var Jf=ce=>{var $e=Ef(),yr=ue($e);mt(yr,{icon:"repeat-2"}),Jt(()=>{S($e,"data-aqe-button-state",n?"active":"default"),S($e,"data-testid",`aqe-repeat-${t.target.ord}`),S($e,"aria-pressed",n?"true":"false")}),Te("mousedown",$e,br=>br.preventDefault()),Te("click",$e,r),T(ce,$e)};hr(ri,ce=>{E(te).command==="aqe:play"&&ce(Jf)})}var zf=V(ri,2);{var ed=ce=>{var $e=Pf(),yr=ue($e),br=ue(yr);mt(br,{icon:"sparkles"});var td=V(br,4);mt(td,{className:"aqe-menu-chevron",icon:"chevron-down"});var nd=V(yr,2);va(nd,21,()=>I,Ea=>Ea.command,(Ea,$t)=>{var gt=Nf(),ai=ue(gt);mt(ai,{get icon(){return E($t).icon}});var rd=V(ai,2),ad=ue(rd);Jt(Na=>{S(gt,"data-aqe-command",E($t).command),S(gt,"data-testid",Na),S(gt,"title",E($t).title),S(gt,"aria-label",E($t).title),Cs(ad,E($t).label)},[()=>qr(t.target.ord,E($t).command)]),Te("mousedown",gt,Na=>Na.preventDefault()),Te("click",gt,()=>po(E($t).command,t.target.node,t.target.ord)),T(Ea,gt)}),Jt(()=>S($e,"data-testid",`aqe-denoise-menu-${t.target.ord}`)),T(ce,$e)};hr(zf,ce=>{E(te).command==="aqe:remove-pauses"&&ce(ed)})}Jt(ce=>{Gn=ya(be,1,"aqe-button",null,Gn,{"aqe-icon-only":E(te).iconOnly===!0}),S(be,"data-aqe-command",E(te).command),S(be,"data-aqe-button-state",E(te).command==="aqe:play"?"play":E(te).command==="aqe:analyze"?"graph":"default"),S(be,"data-testid",ce),S(be,"title",E(te).title),S(be,"aria-label",E(te).title),Cs(gr,E(te).label)},[()=>qr(t.target.ord,E(te).command)]),Te("mousedown",be,ce=>ce.preventDefault()),Te("click",be,()=>po(E(te).command,t.target.node,t.target.ord)),T(g,Lt)});var s=V(o,2),i=ue(s);mt(i,{icon:"trash-2"});var l=V(s,2),c=V(l,2),f=ue(c),u=ue(f);mt(u,{icon:"circle-help"});var d=V(c,2),m=ue(d),p=V(m,2),w=ue(p),_=V(w),v=V(_),A=V(v,2),y=V(A),q=V(y),k=V(q),K=V(p,2),x=ue(K),ye=V(x,2),ie=V(ye,2);Jt(g=>{S(a,"data-aqe-field-ord",t.target.ord),S(a,"data-aqe-source-filename",t.target.sourceFilename),S(a,"data-testid",`aqe-controls-${t.target.ord}`),S(s,"data-testid",g),S(l,"data-testid",`aqe-status-${t.target.ord}`),S(c,"data-testid",`aqe-help-${t.target.ord}`),S(d,"data-aqe-field-ord",t.target.ord),S(d,"data-repeat-enabled",n?"true":"false"),S(d,"data-testid",`aqe-graph-${t.target.ord}`),S(m,"data-testid",`aqe-audio-clock-${t.target.ord}`),S(p,"data-testid",`aqe-graph-svg-${t.target.ord}`),S(p,"viewBox",`0 0 ${M.width} ${M.height}`),S(w,"data-testid",`aqe-selection-${t.target.ord}`),S(w,"x",M.left),S(w,"y",M.top),S(w,"height",M.height-M.top-M.bottom),S(_,"data-testid",`aqe-intensity-${t.target.ord}`),S(v,"data-testid",`aqe-pitch-${t.target.ord}`),S(A,"data-testid",`aqe-x-axis-${t.target.ord}`),S(y,"data-testid",`aqe-selection-start-${t.target.ord}`),S(y,"x1",M.left),S(y,"x2",M.left),S(y,"y1",M.top),S(y,"y2",M.height-M.bottom),S(q,"data-testid",`aqe-selection-end-${t.target.ord}`),S(q,"x1",M.left),S(q,"x2",M.left),S(q,"y1",M.top),S(q,"y2",M.height-M.bottom),S(k,"data-testid",`aqe-cursor-${t.target.ord}`),S(k,"x1",M.left),S(k,"x2",M.left),S(k,"y1",M.top),S(k,"y2",M.height-M.bottom),S(x,"data-testid",`aqe-graph-spinner-${t.target.ord}`),S(ye,"data-testid",`aqe-progress-label-${t.target.ord}`),S(ie,"data-testid",`aqe-graph-status-${t.target.ord}`)},[()=>qr(t.target.ord,"aqe:delete-selection")]),Te("mousedown",s,g=>g.preventDefault()),Te("click",s,()=>Us("button",t.target.node,t.target.ord)),Te("keydown",d,g=>Af(g,t.target.ord)),Te("pointerdown",p,g=>Cl(g,t.target.ord)),T(e,a),$()}Ns(["mousedown","click","keydown","pointerdown"]);const nn=new Map;function Rf(e){const t=nn.get(e.ord);if(t){if(document.body.contains(t.host)||Ks(e,t.host),Ma(e.ord,t.host),!e.sourceFilename||t.sourceFilename===e.sourceFilename)return t;const o=D(e.ord);if((o==null?void 0:o.dataset.graphBusy)==="true"||(o==null?void 0:o.dataset.hasTrack)==="true"){const s=o.dataset.sourceFilename||e.sourceFilename;t.sourceFilename=s;const i=document.querySelector(`.aqe-controls[data-aqe-field-ord="${e.ord}"]`);return i&&(i.dataset.aqeSourceFilename=s),Ma(e.ord,t.host),t}}Tf(e.ord);const n=document.createElement("div");n.className="aqe-mount-host",Ks(e,n);const a={component:Pc(xf,{target:n,props:{target:e}}),host:n,ord:e.ord,sourceFilename:e.sourceFilename};return nn.set(e.ord,a),Ma(e.ord,n),a}function Tf(e){const t=nn.get(e);t&&(xs(t.component),t.host.remove(),nn.delete(e)),document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>n.remove())}function Df(){for(const e of nn.values())xs(e.component),e.host.remove();nn.clear(),Of()}function Ks(e,t){const n=e.node.closest(".field-container")||e.node.closest(".field")||e.node.parentElement||e.node;n.parentElement?n.after(t):e.node.after(t)}function Ma(e,t){document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>{t.contains(n)||n.remove()}),document.querySelectorAll(".aqe-mount-host").forEach(n=>{n!==t&&!n.querySelector(".aqe-controls")&&n.remove()})}function Of(){document.querySelectorAll(".aqe-mount-host").forEach(e=>e.remove()),document.querySelectorAll(".aqe-controls").forEach(e=>e.remove())}function Lf(){window.__aqeGraphStateForTest=Gf,window.__aqeInstallAudioPlaybackTestDriverForTest=$f,window.__aqeSetCursorByClientXForTest=Bf,window.__aqeSetCursorForTest=If}function $f(e){const t=D(e),n=Ee(t);return!t||!n?!1:(n.__aqeTestDriverInstalled=!0,n.pause=function(){n.__aqeTestPlaying=!1,n.__aqeTestFrame&&(window.cancelAnimationFrame(n.__aqeTestFrame),n.__aqeTestFrame=null)},n.play=function(){n.__aqeTestPlaying=!0,n.__aqeTestLastNow=performance.now();const a=()=>{if(!n.__aqeTestPlaying)return;const o=performance.now(),s=Number(t.dataset.durationMs||"0")/1e3,i=Math.max(0,(o-Number(n.__aqeTestLastNow||o))/1e3);if(n.__aqeTestLastNow=o,n.currentTime=Math.min(s,(Number(n.currentTime)||0)+i),s&&n.currentTime>=s){n.__aqeTestPlaying=!1,n.dispatchEvent(new Event("ended"));return}n.__aqeTestFrame=window.requestAnimationFrame(a)};return n.__aqeTestFrame=window.requestAnimationFrame(a),Promise.resolve()},!0)}function If(e,t,n){const r=D(e);return r?(r.hidden=!1,r.dataset.graphActive="true",bt(r,t,!!n),!0):!1}function Bf(e,t,n){var i;const r=D(e),a=(r==null?void 0:r.querySelector(".aqe-visualizer-svg"))??null;if(!r||!a)return null;const o=Number(r.dataset.durationMs||"0"),s=pn({clientX:t},a,o);return bt(r,s,!!n),{cursorMs:Number(r.dataset.cursorMs||"0"),cursorX:Number(((i=r.querySelector(".aqe-cursor"))==null?void 0:i.getAttribute("x1"))||"0"),bounds:Ja(a)}}function Gf(e){var c,f,u,d,m;const t=D(e),n=La(e),r=$a(e),a=((c=Ue(e))==null?void 0:c.querySelector(".aqe-delete-region-button"))??null;if(!t)return null;const o=jn().flatMap(p=>Array.from(p.querySelectorAll(".aqe-button-icon svg"))),s=Ee(t),i=_o(t),l=mo(t);return{active:t.dataset.graphActive==="true",busy:t.dataset.graphBusy==="true",hidden:!!t.hidden,hasTrack:t.dataset.hasTrack==="true",durationMs:Number(t.dataset.durationMs||"0"),anchorMs:Number(t.dataset.anchorMs||"0"),cursorMs:Number(t.dataset.cursorMs||"0"),progressMs:Number(t.dataset.progressMs||"0"),sourceFilename:t.dataset.sourceFilename||"",graphButtonLabel:Xs(n),graphButtonState:(n==null?void 0:n.dataset.aqeButtonState)||"",playButtonLabel:Xs(r),playButtonState:(r==null?void 0:r.dataset.aqeButtonState)||"",playbackState:Hf(t),selectionActive:i!==null,selectionStartMs:(i==null?void 0:i.startMs)??null,selectionEndMs:(i==null?void 0:i.endMs)??null,selectionDraftActive:l!==null,selectionDraftStartMs:(l==null?void 0:l.startMs)??null,selectionDraftEndMs:(l==null?void 0:l.endMs)??null,repeatEnabled:t.dataset.repeatEnabled==="true",repeatControlDisabled:!!((f=Ia(e))!=null&&f.disabled),regionDeleteButtonDisabled:!!(a!=null&&a.disabled),regionDeleteButtonHidden:a?!!a.hidden:!0,playbackStartMs:Number(t.dataset.playbackStartMs||"0"),playbackEndMs:Number(t.dataset.playbackEndMs||"0"),playbackRegionMode:t.dataset.playbackRegionMode==="selection"?"selection":"full",resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true",audioClockSrc:s&&s.getAttribute("src")||"",audioClockCurrentMs:s?Math.round((Number(s.currentTime)||0)*1e3):0,audioClockReady:!!(s&&t.__aqeAudioClockAvailable),audioClockFallback:!!t.__aqeAudioClockFallback,audioClockMuted:!!(s&&s.muted),audioPlaybackTestDriver:!!(s&&s.__aqeTestDriverInstalled),playbackEngine:yn(t),progressClockMode:Vf(t),xAxisLabels:Array.from(t.querySelectorAll(".aqe-x-label")).map(p=>p.textContent||""),pitchPaths:t.querySelectorAll(".aqe-pitch-path").length,intensity:((u=t.querySelector(".aqe-intensity"))==null?void 0:u.getAttribute("d"))||"",cursorX:Number(((d=t.querySelector(".aqe-cursor"))==null?void 0:d.getAttribute("x1"))||"0"),spinnerVisible:t.querySelector(".aqe-spinner")?!((m=t.querySelector(".aqe-spinner"))!=null&&m.hidden):!1,allButtonsDisabled:jn().every(p=>p.disabled),anyButtonDisabled:jn().some(p=>p.disabled),buttonIconCount:o.length,buttonIconStrokeValues:o.map(p=>p.getAttribute("stroke")||getComputedStyle(p).stroke||"")}}function Hf(e){const t=e.dataset.playbackState;return Nr(t)?t:"stopped"}function Vf(e){const t=e.dataset.progressClockMode;return t==="audio"||t==="manual"||t==="stopped"?t:"stopped"}function Xs(e){var t;return((t=e==null?void 0:e.querySelector(".aqe-button-label"))==null?void 0:t.textContent)||(e==null?void 0:e.textContent)||""}function Wf(){window.__aqeSetBusy=Gt,window.__aqeSetStatus=ho,window.__aqeSetVisualizer=Rl,window.__aqeSetVisualizerStatus=Tl,window.__aqeResetGraphAfterEdit=xl,window.__aqeSetPlaybackState=Il,window.__aqeGetPlaybackRequest=Bl,window.__aqeStopEditorPlayback=Gl,window.__aqeGetCursorMs=Hl,window.__aqeGetCursorIntent=Vl,window.__aqePrepareForNewNote=wo,window.__aqePopFrontendLog=ui,window.__aqePopPendingGraphAnalysisRequest=di,window.__aqePopPendingRegionDeleteRequest=pi,Lf()}const jf=/\[sound:([^\]]+)\]/i,Uf=/\.(aac|flac|m4a|mp3|oga|ogg|opus|wav|webm)$/i;let On=[];function Kf(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){Ys(),window.__AQE_EDITOR_CONFIG__=e,Wf(),wo(),Ei(),window.__aqeEditorDispose=Ys,le.info("editor runtime initialized",{audioFieldIndices:e.audioFieldIndices,showGraphByDefault:e.showGraphByDefault===!0});const t=()=>Xf(e);window.__aqeScan=t,Sa(t,0),Sa(t,250),Sa(t,1e3)}function Ys(){On.forEach(e=>window.clearTimeout(e)),On=[],Df()}function Xf(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){if(e.audioFieldIndices.length){const r=Qf(e.audioFieldIndices,e.audioFieldSources);r.forEach(a=>Qs(a)),le.debug("scan mounted explicit fields",{count:r.length}),Ir(),Zs(e,r);return}const t=[];let n=0;Yf().forEach((r,a)=>{const o=qa(r);if(!o)return;const s={node:r,ord:Zf(r,a),sourceFilename:o};Qs(s),t.push(s),n+=1}),le.debug("scan mounted detected fields",{count:n}),Ir(),Zs(e,t)}function Yf(){const e=Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]')),t=new Set;return e.filter(n=>t.has(n)?!1:(t.add(n),!!(n.textContent||n.innerHTML)))}function Qf(e,t={}){return e.map(n=>{const r=document.querySelector(`.field-container[data-index="${n}"]`);if(!r)return null;const a=r.querySelector('[contenteditable="true"]')||r,o=qa(a)||qa(r)||t[n]||"";return{ord:n,node:a,sourceFilename:o}}).filter(n=>n!==null)}function Zf(e,t){const n=["data-field-ord","data-ord","data-index"];for(const a of n){const o=e.getAttribute(a);if(o!==null&&/^\d+$/.test(o))return Number(o)}const r=/(\d+)/.exec(String(e.id||""));return r?Number(r[1]):t}function qa(e){const t=e.innerHTML||e.textContent||"",n=jf.exec(t),r=n==null?void 0:n[1];return r&&Uf.test(r)?r:""}function Qs(e){Rf(e)}function Zs(e,t){e.showGraphByDefault&&Ni(t.map(({ord:n,sourceFilename:r})=>({ord:n,sourceFilename:r})),{anyBusy:()=>document.body.dataset.aqeBusy==="true",requestDefaultGraph:yo})}function Sa(e,t){const n=window.setTimeout(()=>{On=On.filter(r=>r!==n),e()},t);On.push(n)}Kf()})();
