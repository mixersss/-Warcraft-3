import {VOICE_CUES} from './voice-cues.js';
// Exactly two reusable voice channels, one per fighter. A new cue interrupts that
// fighter's previous cue; no growing queues during rapid skills or rematches.
export class Voices{
 constructor({onDuck=()=>{},onError=()=>{}}={}){this.enabled=true;this.onDuck=onDuck;this.onError=onError;this.channels=[0,1].map(()=>({audio:new Audio(),token:0,active:false}));for(const c of this.channels){c.audio.volume=.88;c.audio.preload='auto';}this.lastCue=null;this.failures=0;}
 duck(){this.onDuck(this.channels.some(c=>c.active));}
 stop(side=null){for(const c of side===null?this.channels:[this.channels[side]]){c.token++;c.audio.onended=null;c.audio.onerror=null;c.audio.pause();c.active=false;}this.duck();}
 setEnabled(enabled){this.enabled=enabled;if(!enabled)this.stop();}
 play(hero,index,side){if(!this.enabled)return false;const cue=VOICE_CUES[hero]?.[index];if(!cue)return false;const c=this.channels[side];this.stop(side);const token=++c.token;this.lastCue={hero,index,side,files:cue.files.slice()};let part=0;
  const finish=()=>{if(token!==c.token)return;c.active=false;this.duck();};
  const fail=()=>{if(token!==c.token||!c.active)return;this.failures++;finish();this.onError();};
  const next=()=>{if(token!==c.token||!this.enabled)return;if(part>=cue.files.length){finish();return;}c.audio.src=cue.files[part++];c.audio.onended=next;c.audio.onerror=fail;c.active=true;this.duck();const promise=c.audio.play();if(promise)promise.catch(fail);};next();return true;
 }
}
