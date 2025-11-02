export type ArtifactType = 'model' | 'dataset' | 'code';

const HF = new Set(['huggingface.co', 'hf.co']);
const CODE = new Set([
  'github.com', 'gitlab.com', 'bitbucket.org',
  'raw.githubusercontent.com', 'gitlabusercontent.com',
]);
const MODEL_EXTS = [
  '.pt', '.safetensors', '.bin', '.onnx', '.pb', '.tflite',
  '.ckpt', '.gguf', '.ggml', '.zip', '.tar', '.tar.gz', '.whl',
];

export function inferArtifactType(input: string): ArtifactType {
  let u: URL;
  try { u = new URL(input); } catch { throw new Error('URL must be http(s)'); }
  if (!/^https?:$/.test(u.protocol)) throw new Error('URL must be http(s)');

  const host = u.hostname.toLowerCase();
  const path = u.pathname.replace(/^\/+|\/+$/g, '');

  if (HF.has(host)) {
    const first = path.split('/')[0] ?? '';
    return first === 'datasets' ? 'dataset' : 'model';
  }
  if (CODE.has(host)) return 'code';
  if (MODEL_EXTS.some(ext => path.endsWith(ext))) return 'model';

  throw new Error('Could not infer artifact type from URL');
}
