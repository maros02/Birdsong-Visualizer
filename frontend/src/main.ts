import { createScene } from "./scene";
import { listRecordings, getEmbedding, audioUrl, type Embedding, type Recording } from "./api";
import { TrailView } from "./trail";

/** Main loop for frontend. */
const canvas = document.getElementById("canvas") as HTMLCanvasElement;
const selRecording = document.getElementById("recording") as HTMLSelectElement;
const btnPlay = document.getElementById("play") as HTMLButtonElement;
const btnReset = document.getElementById("reset") as HTMLButtonElement;
const fadeInput = document.getElementById("fade") as HTMLInputElement;
const fadeVal = document.getElementById("fadeVal") as HTMLSpanElement;
const autoRotateInput = document.getElementById("autoRotate") as HTMLInputElement;
const statusEl = document.getElementById("status") as HTMLDivElement;

const { renderer, scene, camera, controls } = createScene(canvas);

const trail = new TrailView();
scene.add(trail.group);

let embedding: Embedding | null = null;
const audio = new Audio();
audio.preload = "auto";
audio.crossOrigin = "anonymous";

function setStatus(msg: string): void {
  statusEl.textContent = msg;
}

async function loadRecording(id: string): Promise<void> {
  setStatus(`Loading ${id}…`);
  btnPlay.disabled = true;
  try {
    embedding = await getEmbedding(id);
    trail.setEmbedding(embedding);
    audio.src = audioUrl(id);
    audio.currentTime = 0;
    setStatus(`${embedding.n_frames} frames, ${embedding.duration_seconds.toFixed(1)}s`);
    btnPlay.disabled = false;
  } catch (err) {
    setStatus(`Error: ${(err as Error).message}`);
  }
}

async function init(): Promise<void> {
  setStatus("Fetching recordings…");
  let recordings: Recording[] = [];
  try {
    recordings = await listRecordings();
  } catch (err) {
    setStatus(`Error: ${(err as Error).message}`);
    return;
  }
  if (recordings.length === 0) {
    setStatus("No recordings found.");
    return;
  }
  selRecording.innerHTML = "";
  for (const r of recordings) {
    const opt = document.createElement("option");
    opt.value = r.id;
    const label = r.english_name ? `${r.english_name} (${r.id})` : r.id;
    opt.textContent = label;
    selRecording.appendChild(opt);
  }
  await loadRecording(recordings[0].id);
}

selRecording.addEventListener("change", () => {
  audio.pause();
  btnPlay.textContent = "Play";
  loadRecording(selRecording.value);
});

fadeInput.addEventListener("input", () => {
  const s = parseFloat(fadeInput.value);
  fadeVal.textContent = s.toFixed(1);
  trail.setFadeSeconds(s);
});
trail.setFadeSeconds(parseFloat(fadeInput.value));

autoRotateInput.addEventListener("change", () => {
  controls.autoRotate = autoRotateInput.checked;
});

btnPlay.addEventListener("click", () => {
  if (audio.paused) {
    audio.play().catch((err) => setStatus(`Play failed: ${err.message}`));
    btnPlay.textContent = "Pause";
  } else {
    audio.pause();
    btnPlay.textContent = "Play";
  }
});

btnReset.addEventListener("click", () => {
  audio.pause();
  audio.currentTime = 0;
  trail.reset();
  btnPlay.textContent = "Play";
});

audio.addEventListener("ended", () => {
  btnPlay.textContent = "Play";
});

function loop(): void {
  requestAnimationFrame(loop);
  controls.update();
  const t = audio.currentTime;
  trail.update(t);
  renderer.render(scene, camera);
}

init();
loop();
