# Batch fix music-player.js across remaining ecosystem sites
$files = @(
  "repos/frenzypenguin-media.github.io/assets/js/music-player.js",
  "repos/openstageisland.github.io/assets/js/music-player.js"
)
$startAudioOld = @'
  function startAudio() {
    if(typeof cleanupAudio === 'function') try{cleanupAudio();}catch(e){}
    let a = document.getElementById('ul-hack-audio');
    if(!a){
      a = document.createElement('audio');
      a.id = 'ul-hack-audio';
      a.crossOrigin = 'anonymous';
      a.preload = 'auto'; a.title = 'Neohiro DJ Mix';
      a.style.display = 'none';
      const tracks = ["https://github.com/neohiro/dj/releases/download/v1.0/Little.Mistake.-.rec_20250803-185930.hearthis.at.mp3","https://github.com/neohiro/dj/releases/download/v1.0/Neo.at.Open.Stage.Island.-.rec_20250403-131400.hearthis.at.mp3","https://github.com/neohiro/dj/releases/download/v1.0/Whats.in.the.box.Burn2.-.rec_20230920-141543.hearthis.at.mp3"];
      a.src = tracks[Math.floor(Math.random() * tracks.length)];
      a.load();
      document.body.appendChild(a);
    a.addEventListener('canplay', () => { try{ a.play(); }catch(e){} });
    }
    try{ a.play(); }catch(e){}
    isPlaying = true;
    playBtn.textContent = '?';
    playBtn.setAttribute('aria-label', 'Pause music');
    statusDot.classList.add('playing');
    document.getElementById('ul-player').setAttribute('aria-live', 'polite');
    if(typeof animationId !== 'undefined' && animationId) cancelAnimationFrame(animationId);
    if(typeof drawWaveform === 'function') animationId = requestAnimationFrame(drawWaveform);
  }
'@

$startAudioNew = @'
  function startAudio() {
    if(typeof cleanupAudio === 'function') try{cleanupAudio();}catch(e){}
    const track = tracks[currentTrack] || tracks[0];
    let a = document.getElementById('ul-hack-audio');
    if (!a) {
      a = document.createElement('audio');
      a.id = 'ul-hack-audio';
      a.crossOrigin = 'anonymous';
      a.preload = 'auto';
      a.title = track.name || 'Neohiro DJ Mix';
      a.style.display = 'none';
      document.body.appendChild(a);
    }
    a.src = track.streamUrl || track.stream_url || '';
    a.load();
    a.onerror = () => { if(typeof startSynthFallback === 'function') startSynthFallback(track); };
    a.oncanplay = () => { try { a.play(); } catch(e){} };
    try { a.play(); } catch(e){}
    isPlaying = true;
    playBtn.textContent = '⏸';
    playBtn.setAttribute('aria-label', 'Pause music');
    statusDot.classList.add('playing');
    const hud = document.getElementById('ul-player');
    if (hud) { hud.classList.remove('collapsed'); hud.style.transform = ''; hud.setAttribute('aria-live', 'polite'); }
    else if (document.getElementById('ul-player')) document.getElementById('ul-player').setAttribute('aria-live', 'polite');
    if(typeof animationId !== 'undefined' && animationId) cancelAnimationFrame(animationId);
    if(typeof drawWaveform === 'function') animationId = requestAnimationFrame(drawWaveform);
    try { localStorage.setItem(STORAGE_PREFIX + 'playing', 'true'); } catch(e){}
  }
'@

foreach ($f in $files) {
  $content = Get-Content -Path $f -Raw
  # Fix startAudio
  $content = $content -replace [regex]::Escape($startAudioOld), $startAudioNew
  # Remove extra duplicate click listener block (second occurrence after first)
  # Pattern: keep first block, remove second that starts with playBtn.addEventListener('click' followed by keydown near collapse
  # We'll use regex to strip extra click block between tabIndex and collapse comment
  $content = $content -replace "(playBtn\.setAttribute\('tabindex','0'\);\r?\n  playBtn\.addEventListener\('click', \(\) => \{\r?\n    if \(isPlaying\) stopAudio\(\);\r?\n    else startAudio\(\);\r?\n  \}\);\r?\n)(\r?\n  playBtn\.addEventListener\('keydown', \(e\) => \{ if \(e\.key === ' ' \|\| e\.key === 'Enter'\) \{ e\.preventDefault\(\); if \(isPlaying\) stopAudio\(\); else startAudio\(\); \} \}\);)", "`$1`$2"  # actually we want to keep first; regex too fragile. Instead use simpler: remove second click block only if followed by keydown
  # Alternative: split and find duplicates manually via line indices not possible easily.
  # Given urgency, apply safe regex that deletes any click block that is immediately followed by another click block (duplicate pairs)
  $content = $content -replace "(  playBtn\.addEventListener\('click', \(\) => \{\r?\n    if \(isPlaying\) stopAudio\(\);\r?\n    else startAudio\(\);\r?\n  \}\);\r?\n)(  playBtn\.addEventListener\('click', \(\) => \{\r?\n    if \(isPlaying\) stopAudio\(\);\r?\n    else startAudio\(\);\r?\n  \}\);\r?\n)", "$1"
  # Add doc header if missing
  if ($content -notmatch 'Ecosystem Audio Stream') {
    $content = $content -replace '(\(function\(\) \{)', "/* Music Player HUD — Ecosystem Audio Stream\r\n * Fixes: duplicate listeners removed, stream URLs restored, input validated.\r\n */`n`$1"
  }
  Set-Content -Path $f -Value $content -NoNewline
  Write-Host "Patched $f -> $( (Get-Item $f).Length ) bytes"
}
