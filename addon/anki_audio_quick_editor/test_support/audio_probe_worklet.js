class AqeAudibleProbe extends AudioWorkletProcessor {
  process(inputs) {
    const channels = inputs[0] || [];
    const frames = channels[0]?.length || 0;
    if (!frames) return true;
    const mono = new Float32Array(frames);
    for (let index = 0; index < frames; index += 1) {
      let sum = 0;
      for (const channel of channels) sum += channel[index] || 0;
      mono[index] = channels.length ? sum / channels.length : 0;
    }
    this.port.postMessage(mono, [mono.buffer]);
    return true;
  }
}

registerProcessor("aqe-audible-probe", AqeAudibleProbe);
