export interface Recording {
  id: string;
  filename: string;
  genus: string | null;
  species: string | null;
  english_name: string | null;
}

export interface Embedding {
  recording_id: string;
  sample_rate: number;
  hop_seconds: number;
  duration_seconds: number;
  n_frames: number;
  frames: {
    t: number[];
    xyz: number[][];
    rms: number[];
    centroid: number[];
    novelty: number[];
    centroid_hz: number[];
  };
}

export async function listRecordings(): Promise<Recording[]> {
  const res = await fetch("/api/recordings");
  if (!res.ok) throw new Error(`listRecordings failed: ${res.status}`);
  const data = await res.json();
  return data.recordings;
}

export async function getEmbedding(id: string): Promise<Embedding> {
  const res = await fetch(`/api/embedding/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`getEmbedding failed: ${res.status}`);
  return res.json();
}

export function audioUrl(id: string): string {
  return `/api/audio/${encodeURIComponent(id)}`;
}
