/* Local-only companion for FB Liked Media Downloader.
 * yt-dlp discovers Facebook DASH tracks and FFmpeg muxes them into one MP4.
 */
const http = require('http');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const HOST = '127.0.0.1';
const PORT = Number(process.env.FB_MEDIA_HELPER_PORT || 48765);
const OUTPUT_DIR = process.env.FB_MEDIA_OUTPUT_DIR || path.join(os.homedir(), 'Desktop', 'FB_Liked_Media', 'video');
const YT_DLP = process.env.YT_DLP_PATH || 'C:\\Python311\\Scripts\\yt-dlp.exe';
const FFMPEG_DIR = process.env.FFMPEG_DIR || 'C:\\ffmpeg\\bin';

function reply(res, status, payload, origin = '') {
  const headers = { 'Content-Type': 'application/json; charset=utf-8' };
  if (origin.startsWith('chrome-extension://')) {
    headers['Access-Control-Allow-Origin'] = origin;
    headers['Access-Control-Allow-Headers'] = 'Content-Type, X-FB-Media-Helper';
    headers['Vary'] = 'Origin';
  }
  res.writeHead(status, headers);
  res.end(JSON.stringify(payload));
}

function validFacebookReel(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && /(^|\.)facebook\.com$/i.test(url.hostname) && /^\/reel\/[A-Za-z0-9]+/.test(url.pathname);
  } catch {
    return false;
  }
}

function safeName(value) {
  const base = path.basename(String(value || 'reel.mp4')).replace(/[^a-zA-Z0-9._-]/g, '_');
  return base.toLowerCase().endsWith('.mp4') ? base : `${base}.mp4`;
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { windowsHide: true });
    let output = '';
    child.stdout.on('data', chunk => { output += chunk.toString(); });
    child.stderr.on('data', chunk => { output += chunk.toString(); });
    child.on('error', reject);
    child.on('close', code => code === 0 ? resolve(output) : reject(new Error(output.slice(-2000) || `exit ${code}`)));
  });
}

async function downloadReel(sourceUrl, filename) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const outputPath = path.join(OUTPUT_DIR, safeName(filename));
  const args = [
    '--no-playlist', '--no-update', '--no-warnings', '--no-continue',
    '--ffmpeg-location', FFMPEG_DIR,
    '--merge-output-format', 'mp4',
    '--format', 'bestvideo*+bestaudio/best',
    '--output', outputPath,
    '--', sourceUrl
  ];
  await run(YT_DLP, args);
  const stat = fs.statSync(outputPath);
  if (stat.size < 50 * 1024) throw new Error('Muxed video is unexpectedly small.');
  const durationText = await run(path.join(FFMPEG_DIR, 'ffprobe.exe'), ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nokey=1:noprint_wrappers=1', outputPath]);
  const duration = Number.parseFloat(durationText);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error('FFmpeg could not verify the output MP4.');
  return { path: outputPath, duration };
}

const server = http.createServer((req, res) => {
  const origin = req.headers.origin || '';
  if (req.method === 'OPTIONS') {
    if (!origin.startsWith('chrome-extension://')) return reply(res, 403, { success: false, error: 'Chrome extension origin required.' });
    return reply(res, 204, {}, origin);
  }
  if (req.method === 'GET' && req.url === '/health') return reply(res, 200, { success: true, outputDir: OUTPUT_DIR }, origin);
  if (req.method !== 'POST' || req.url !== '/download' || !origin.startsWith('chrome-extension://') || req.headers['x-fb-media-helper'] !== 'local-addon-v1') {
    return reply(res, 404, { success: false, error: 'Not found.' }, origin);
  }
  let body = '';
  req.on('data', chunk => {
    body += chunk;
    if (body.length > 16 * 1024) req.destroy();
  });
  req.on('end', async () => {
    try {
      const { sourceUrl, filename } = JSON.parse(body);
      if (!validFacebookReel(sourceUrl)) return reply(res, 400, { success: false, error: 'Only a Facebook Reel URL is allowed.' }, origin);
      const result = await downloadReel(sourceUrl, filename);
      reply(res, 200, { success: true, ...result }, origin);
    } catch (error) {
      console.error('[FB helper]', error.message);
      reply(res, 500, { success: false, error: error.message }, origin);
    }
  });
});

server.on('error', error => {
  if (error.code === 'EADDRINUSE') {
    console.error(`Facebook Media Helper is already running at http://${HOST}:${PORT}`);
  } else {
    console.error('Facebook Media Helper failed to start:', error.message);
  }
  process.exitCode = 1;
});

server.listen(PORT, HOST, () => {
  console.log(`FB media helper listening on http://${HOST}:${PORT}`);
  console.log(`Output: ${OUTPUT_DIR}`);
});
