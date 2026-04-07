import * as THREE from "three";
import type { Embedding } from "./api";

/** Trail-view with fade mechanic. */
export class TrailView {
  private readonly line: THREE.Line;
  private readonly positions: Float32Array;
  private readonly colors: Float32Array;
  private readonly baseColors: Float32Array;
  private readonly addedAt: Float32Array; // seconds (playback time) when each vertex was added
  private embedding: Embedding | null = null;
  private lastIdx = -1;
  private fadeSeconds = 1.0;
  private readonly rmsNoiseGate = 0.08; // RMS threshold to avoid jitter

  readonly group = new THREE.Group();

  constructor(maxFrames = 32000) {
    this.positions = new Float32Array(maxFrames * 3);
    this.colors = new Float32Array(maxFrames * 3);
    this.baseColors = new Float32Array(maxFrames * 3);
    this.addedAt = new Float32Array(maxFrames);
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.BufferAttribute(this.positions, 3));
    geom.setAttribute("color", new THREE.BufferAttribute(this.colors, 3));
    geom.setDrawRange(0, 0);
    const mat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    this.line = new THREE.Line(geom, mat);
    this.group.add(this.line);
  }

  setEmbedding(embedding: Embedding): void {
    this.embedding = embedding;
    this.reset();
  }

  reset(): void {
    this.lastIdx = -1;
    this.line.geometry.setDrawRange(0, 0);
  }

  setFadeSeconds(seconds: number): void {
    this.fadeSeconds = Math.max(0.1, seconds);
  }

  update(timeSec: number): void {
    if (!this.embedding) return;
    const { frames, hop_seconds } = this.embedding;
    const idx = Math.min(frames.t.length - 1, Math.floor(timeSec / hop_seconds));
    const maxFrames = this.positions.length / 3;

    // reset if playback jumps back
    if (idx < this.lastIdx) this.reset();

    // append any newly played frames
    if (idx > this.lastIdx) {
      for (let i = this.lastIdx + 1; i <= idx && i < maxFrames; i++) {
        const p = frames.xyz[i];
        const rms = frames.rms[i];
        const c = i * 3;

        // noise gate: when RMS is low, blend with the previous position (smoothen it)
        let x = p[0], y = p[1], z = p[2];
        if (i > 0 && rms < this.rmsNoiseGate) {
          const blend = rms / this.rmsNoiseGate;
          const pc = (i - 1) * 3;
          x = this.positions[pc]     + blend * (x - this.positions[pc]);
          y = this.positions[pc + 1] + blend * (y - this.positions[pc + 1]);
          z = this.positions[pc + 2] + blend * (z - this.positions[pc + 2]);
        }

        this.positions[c] = x;
        this.positions[c + 1] = y;
        this.positions[c + 2] = z;

        const centroid = frames.centroid[i];
        const color = new THREE.Color().setHSL(0.12 + (1 - centroid) * 0.38, 0.7, 0.55);
        this.baseColors[c] = color.r;
        this.baseColors[c + 1] = color.g;
        this.baseColors[c + 2] = color.b;
        this.addedAt[i] = frames.t[i];
      }
      this.lastIdx = idx;
      this.line.geometry.setDrawRange(0, idx + 1);
      (this.line.geometry.getAttribute("position") as THREE.BufferAttribute).needsUpdate = true;
    }

    // recompute faded colors every frame across the visible range
    const end = this.lastIdx + 1;
    for (let i = 0; i < end; i++) {
      const age = timeSec - this.addedAt[i];
      const fade = age <= 0 ? 1 : Math.max(0, 1 - age / this.fadeSeconds);
      const c = i * 3;
      this.colors[c] = this.baseColors[c] * fade;
      this.colors[c + 1] = this.baseColors[c + 1] * fade;
      this.colors[c + 2] = this.baseColors[c + 2] * fade;
    }
    (this.line.geometry.getAttribute("color") as THREE.BufferAttribute).needsUpdate = true;
  }
}
