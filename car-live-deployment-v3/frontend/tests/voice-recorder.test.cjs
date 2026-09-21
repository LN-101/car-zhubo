const test = require('node:test');
const assert = require('node:assert/strict');
const recorder = require('../voice-recorder.js');

test('recordings become standard mono 24kHz PCM WAV accepted by existing clone API', () => {
  const samples = Float32Array.from([-2,-0.5,0,0.5,2]);
  const bytes = recorder.encodeWav(samples);
  const header = new DataView(bytes);
  assert.equal(Buffer.from(bytes).toString('ascii',0,4),'RIFF');
  assert.equal(Buffer.from(bytes).toString('ascii',8,12),'WAVE');
  assert.equal(header.getUint16(20,true),1);
  assert.equal(header.getUint16(22,true),1);
  assert.equal(header.getUint32(24,true),24000);
  assert.equal(header.getUint16(34,true),16);
  assert.equal(header.getUint32(40,true),10);
  assert.deepEqual([...new Int16Array(bytes,44)],[-32768,-16384,0,16384,32767]);
});

test('too-short, too-long and silent microphone recordings are rejected before cloning', () => {
  assert.throws(()=>recorder.validateRecording(new Float32Array(24000).fill(0.1),24000),/不足/);
  assert.throws(()=>recorder.validateRecording(new Float32Array(24000*11).fill(0.1),24000),/超过/);
  assert.throws(()=>recorder.validateRecording(new Float32Array(24000*5),24000),/没有检测到/);
  assert.equal(recorder.validateRecording(new Float32Array(24000*5).fill(0.1),24000),5);
});
