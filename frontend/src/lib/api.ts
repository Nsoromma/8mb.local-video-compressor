import { env } from '$env/dynamic/public';
// Prefer same-origin when PUBLIC_BACKEND_URL is empty or unset (for baked SPA inside the container)
const RAW = (env.PUBLIC_BACKEND_URL as string | undefined) || '';
const BACKEND = RAW && RAW.trim() !== '' ? RAW.replace(/\/$/, '') : '';

export async function upload(file: File, targetSizeMB: number, audioKbps = 128, auth?: {user: string, pass: string}) {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('target_size_mb', String(targetSizeMB));
  fd.append('audio_bitrate_kbps', String(audioKbps));
  const headers: Record<string,string> = {};
  if (auth) headers['Authorization'] = 'Basic ' + btoa(`${auth.user}:${auth.pass}`);
  const res = await fetch(`${BACKEND}/api/upload`, { method: 'POST', body: fd, headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// XHR-based upload to report client-side progress
export function uploadWithProgress(
  file: File,
  targetSizeMB: number,
  audioKbps = 128,
  opts?: { auth?: { user: string; pass: string }; onProgress?: (percent: number) => void }
): Promise<any> {
  return new Promise((resolve, reject) => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('target_size_mb', String(targetSizeMB));
    fd.append('audio_bitrate_kbps', String(audioKbps));

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BACKEND}/api/upload`);
    if (opts?.auth) {
      xhr.setRequestHeader('Authorization', 'Basic ' + btoa(`${opts.auth.user}:${opts.auth.pass}`));
    }
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && opts?.onProgress) {
        const pct = Math.max(0, Math.min(100, Math.round((e.loaded / e.total) * 100)));
        opts.onProgress(pct);
      }
    };
    xhr.onload = () => {
      try {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText || '{}'));
        } else {
          reject(new Error(xhr.responseText || `HTTP ${xhr.status}`));
        }
      } catch (err: any) {
        reject(err);
      }
    };
    xhr.onerror = () => reject(new Error('Network error'));
    xhr.send(fd);
  });
}

export async function startCompress(payload: any, auth?: {user: string, pass: string}) {
  const headers: Record<string,string> = { 'Content-Type': 'application/json' };
  if (auth) headers['Authorization'] = 'Basic ' + btoa(`${auth.user}:${auth.pass}`);
  const res = await fetch(`${BACKEND}/api/compress`, { method: 'POST', body: JSON.stringify(payload), headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function openProgressStream(taskId: string, auth?: {user: string, pass: string}): EventSource {
  const url = new URL(`${BACKEND}/api/stream/${taskId}`, typeof window !== 'undefined' ? window.location.origin : undefined);
  const es = new EventSource(url.toString());
  return es;
}

export function downloadUrl(taskId: string) {
  return `${BACKEND}/api/jobs/${taskId}/download`;
}

export async function getAvailableCodecs() {
  const res = await fetch(`${BACKEND}/api/codecs/available`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
