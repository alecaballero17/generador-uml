import { env, pipeline } from '../assets/vendor/transformers.js';
env.allowRemoteModels=false;
env.allowLocalModels=true;
env.localModelPath='/assets/models/';
env.backends.onnx.wasm.wasmPaths='/assets/vendor/';
env.backends.onnx.wasm.numThreads=1;
let transcriber;
self.onmessage=async event=>{
    try {
        if(!transcriber) {
            self.postMessage({status:'Cargando IA de voz local…'});
            transcriber=await pipeline('automatic-speech-recognition','onnx-community/whisper-tiny',{dtype:'q8',device:'wasm',progress_callback:p=>{ if(p.status==='progress') self.postMessage({status:`Cargando ${p.file}: ${Math.round(p.progress)}%`}); }});
        }
        if(event.data.type==='prepare') {self.postMessage({ready:true});return;}
        self.postMessage({status:'Interpretando audio en este dispositivo…'});
        const result=await transcriber(event.data.audio,{language:event.data.language||'spanish',task:'transcribe',chunk_length_s:20,stride_length_s:3});
        self.postMessage({text:result.text});
    } catch(error) {self.postMessage({error:error.message});}
};
