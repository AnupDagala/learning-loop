// Runs the shipped frontend logic against the real HTTP server in a minimal DOM
// adapter. It checks rendering/data flow, not browser layout, accessibility or CSP.
const vm=require('node:vm');const fs=require('node:fs');const path=require('node:path');const {webcrypto}=require('node:crypto');
const url=process.env.TEST_URL||'http://127.0.0.1:8765';
let cookie='',html='',checks=0;const inputs=new Map();const nodes=new Map();
const node=id=>{if(!nodes.has(id))nodes.set(id,{addEventListener(){},classList:{toggle(){}},focus(){},showModal(){},close(){},checked:false,disabled:false,hidden:true,textContent:''});return nodes.get(id);};
const app={get innerHTML(){return html;},set innerHTML(v){html=v;},querySelector(s){if(s==='h1')return node('h1');const m=s.match(/input\[name="q(\d+)"\]:checked/);return m&&inputs.has(Number(m[1]))?{value:inputs.get(Number(m[1]))}:null;}};
const document={querySelector(s){return s==='#app'?app:node(s);},getElementById:node};
const context=vm.createContext({document,window:{scrollTo(){}},crypto:webcrypto,console,Date,setTimeout(){},fetch:async(p,options={})=>{const headers={...(options.headers||{}),...(cookie?{Cookie:cookie}:{})};const r=await fetch(url+p,{...options,headers});if(r.headers.get('set-cookie'))cookie=r.headers.get('set-cookie').split(';')[0];return r;}});
const check=(cond,msg)=>{if(!cond)throw new Error(msg);checks++;};const run=code=>vm.runInContext(code,context);
(async()=>{
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8'),context);
 for(let i=0;i<100&&!html.includes('Choose your focus');i++)await new Promise(r=>setTimeout(r,10));
 check(html.includes('Choose your focus'),'Homepage bootstraps from API: '+html+' '+node('#error').textContent);
 await run('start(state.lessons[0])');check(html.includes('Equality has two parts'),'Lesson renders');run('quiz()');check(html.includes('Check my understanding'),'Practice renders');
 inputs.set(0,0);inputs.set(1,0);inputs.set(2,2);check(JSON.stringify(run('answers(lesson)'))==='[0,0,2]','Frontend collects checked answers');
 await run("(async()=>{state.latest=await api('/api/submit',{attempt_id:attemptId,lesson_id:lesson.id,journey_id:journey,answers:answers(lesson)});await openFeedback(state.latest);})()");
 check(html.includes('Your mistakes have a next step.'),'Graded feedback renders');check(html.includes('Reasonable classification'),'Gap rendered');
 await run("(async()=>{state.plan=await api('/api/plan',{attempt_id:state.latest.attempt_id});home();})()");check(html.includes('Open revision'),'Saved plan on home');
 run('revision()');check(html.includes('Complete revision'),'Revision renders');inputs.set(0,1);
 const review=await run("api('/api/review',{answers:answers(lesson)})");check(review.score===3,'Frontend to server revision grades');
 await run("(async()=>{dataset='synthetic';await insights();})()");check(html.includes('Synthetic illustration'),'Synthetic warning renders');check(html.includes('120'),'Synthetic totals render');
 await run("(async()=>{dataset='local';await insights();})()");check(html.includes('No mature D1 cohorts yet'),'Immature retention not rendered as zero');
 check(run("esc('<img onerror=alert(1)>')")==='&lt;img onerror=alert(1)&gt;','Dynamic text escapes markup');
 console.log(`${checks} frontend/API smoke checks passed (VM DOM adapter; not a browser)`);
 fs.writeFileSync(path.join(__dirname,'../docs/evidence/frontend-smoke.txt'),`${checks} frontend/API smoke checks passed.\nUses Node VM and minimal DOM adapter against live local HTTP server.\nBrowser layout, accessibility and CSP remain unverified.\n`);
})().catch(e=>{console.error(e);process.exit(1);});
