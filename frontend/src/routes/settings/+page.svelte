<script lang="ts">
  import { onMount } from 'svelte';

  type AuthSettings = { auth_enabled: boolean; auth_user: string | null };
  type DefaultPresets = {
	target_mb: number;
	video_codec: string;
	audio_codec: string;
	preset: string;
	audio_kbps: number;
	container: string;
	tune: string;
  };

  let saving = false;
  let message = '';
  let error = '';

  // Auth
  let authEnabled = false;
  let username = 'admin';
  let newPassword = '';
  let confirmPassword = '';

  // Presets
  let targetMB = 25;
  let videoCodec = 'av1_nvenc';
  let audioCodec = 'libopus';
  let preset = 'p6';
  let audioKbps = 128;
  let container = 'mp4';
  let tune = 'hq';

  onMount(async () => {
	try {
	  const [authRes, presetsRes] = await Promise.all([
		fetch('/api/settings/auth'),
		fetch('/api/settings/presets')
	  ]);
	  if (authRes.ok) {
		const a: AuthSettings = await authRes.json();
		authEnabled = !!a.auth_enabled;
		username = a.auth_user || 'admin';
	  }
	  if (presetsRes.ok) {
		const p: DefaultPresets = await presetsRes.json();
		targetMB = p.target_mb;
		videoCodec = p.video_codec;
		audioCodec = p.audio_codec;
		preset = p.preset;
		audioKbps = p.audio_kbps;
		container = p.container;
		tune = p.tune;
	  }
	} catch (e) {
	  error = 'Failed to load settings';
	}
  });

  async function saveAuth() {
	error = '';
	message = '';
	if (authEnabled && !username.trim()) {
	  error = 'Username is required when authentication is enabled';
	  return;
	}
	if (authEnabled && newPassword && newPassword !== confirmPassword) {
	  error = 'Passwords do not match';
	  return;
	}
	saving = true;
	try {
	  const payload: any = { auth_enabled: authEnabled, auth_user: username.trim() };
	  if (authEnabled && newPassword) payload.auth_pass = newPassword;
	  const res = await fetch('/api/settings/auth', {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(payload)
	  });
	  if (res.ok) {
		const data = await res.json();
		message = data.message || 'Saved authentication settings';
		newPassword = '';
		confirmPassword = '';
	  } else {
		const data = await res.json();
		error = data.detail || 'Failed to save authentication';
	  }
	} catch (e) {
	  error = 'Failed to save authentication';
	} finally {
	  saving = false;
	}
  }

  async function saveDefaults() {
	error = '';
	message = '';
	if (targetMB < 1) {
	  error = 'Target size must be at least 1 MB';
	  return;
	}
	saving = true;
	try {
	  const res = await fetch('/api/settings/presets', {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
		  target_mb: targetMB,
		  video_codec: videoCodec,
		  audio_codec: audioCodec,
		  preset,
		  audio_kbps: audioKbps,
		  container,
		  tune
		})
	  });
	  if (res.ok) {
		const data = await res.json();
		message = data.message || 'Saved default presets';
	  } else {
		const data = await res.json();
		error = data.detail || 'Failed to save presets';
	  }
	} catch (e) {
	  error = 'Failed to save presets';
	} finally {
	  saving = false;
	}
  }
</script>

<style>
  /* Keep the page dead-simple and avoid any overlays that might block <select> popovers */
  .container { max-width: 760px; margin: 0 auto; padding: 24px; }
  .card { background: #111827; border: 1px solid #374151; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .label { display: block; color: #d1d5db; margin-bottom: 6px; font-size: 14px; }
  .input, .select { width: 100%; padding: 8px 10px; color: #e5e7eb; background: #1f2937; border: 1px solid #374151; border-radius: 8px; }
  .btn { padding: 10px 12px; color: white; background: #2563eb; border: none; border-radius: 8px; cursor: pointer; }
  .btn:disabled { background: #4b5563; cursor: not-allowed; }
  .btn.alt { background: #059669; }
  .title { color: white; font-size: 20px; font-weight: 600; margin-bottom: 10px; }
  .hdr { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .msg { padding: 10px; border-radius: 8px; margin-bottom: 12px; }
  .msg.ok { background: rgba(16,185,129,.15); border: 1px solid #10b981; color: #a7f3d0; }
  .msg.err { background: rgba(239,68,68,.15); border: 1px solid #ef4444; color: #fecaca; }
  .switch { display:flex; align-items:center; gap:8px; }
  .switch input { transform: scale(1.2); }
</style>

<div class="container">
  <div class="hdr">
	<h1 class="title" style="font-size:24px">Settings</h1>
	<a href="/" class="btn" style="text-decoration:none; background:#374151">← Back</a>
  </div>

  {#if message}<div class="msg ok">{message}</div>{/if}
  {#if error}<div class="msg err">{error}</div>{/if}

  <!-- Authentication -->
  <div class="card">
	<div class="title">Authentication</div>
	<div class="switch" style="margin-bottom:12px">
	  <input id="auth_enabled" type="checkbox" bind:checked={authEnabled} />
	  <label class="label" for="auth_enabled" style="margin:0">Require authentication</label>
	</div>

	{#if authEnabled}
	  <div class="row">
		<div>
		  <label class="label" for="username">Username</label>
		  <input id="username" class="input" type="text" bind:value={username} placeholder="admin" />
		</div>
		<div>
		  <label class="label" for="newpass">New password (optional)</label>
		  <input id="newpass" class="input" type="password" bind:value={newPassword} />
		</div>
	  </div>
	  {#if newPassword}
		<div style="margin-top:12px">
		  <label class="label" for="confirmpass">Confirm new password</label>
		  <input id="confirmpass" class="input" type="password" bind:value={confirmPassword} />
		</div>
	  {/if}
	{/if}

	<div style="margin-top:12px">
	  <button class="btn" on:click={saveAuth} disabled={saving}>{saving ? 'Saving…' : 'Save authentication'}</button>
	</div>
  </div>

  <!-- Defaults -->
  <div class="card">
	<div class="title">Default presets</div>
	<div>
	  <label class="label" for="targetmb">Default target size (MB)</label>
	  <input id="targetmb" class="input" type="number" min="1" bind:value={targetMB} />
	</div>

	<div class="row" style="margin-top:12px">
	  <div>
		<label class="label" for="vcodec">Video codec</label>
		<select id="vcodec" class="select" bind:value={videoCodec}>
		  <option value="av1_nvenc">AV1 (NVENC)</option>
		  <option value="hevc_nvenc">HEVC (NVENC)</option>
		  <option value="h264_nvenc">H.264 (NVENC)</option>
		  <option value="libaom-av1">AV1 (CPU)</option>
		  <option value="libx265">HEVC (CPU)</option>
		  <option value="libx264">H.264 (CPU)</option>
		</select>
	  </div>
	  <div>
		<label class="label" for="acodec">Audio codec</label>
		<select id="acodec" class="select" bind:value={audioCodec}>
		  <option value="libopus">Opus</option>
		  <option value="aac">AAC</option>
		</select>
	  </div>
	</div>

	<div class="row" style="margin-top:12px">
	  <div>
		<label class="label" for="preset">Speed/quality preset</label>
		<select id="preset" class="select" bind:value={preset}>
		  <option value="p1">P1 (Fastest)</option>
		  <option value="p2">P2</option>
		  <option value="p3">P3</option>
		  <option value="p4">P4</option>
		  <option value="p5">P5</option>
		  <option value="p6">P6 (Balanced)</option>
		  <option value="p7">P7 (Best quality)</option>
		</select>
	  </div>
	  <div>
		<label class="label" for="kbps">Audio bitrate (kbps)</label>
		<select id="kbps" class="select" bind:value={audioKbps}>
		  <option value={64}>64</option>
		  <option value={96}>96</option>
		  <option value={128}>128</option>
		  <option value={160}>160</option>
		  <option value={192}>192</option>
		  <option value={256}>256</option>
		</select>
	  </div>
	</div>

	<div class="row" style="margin-top:12px">
	  <div>
		<label class="label" for="container">Container</label>
		<select id="container" class="select" bind:value={container}>
		  <option value="mp4">MP4</option>
		  <option value="mkv">MKV</option>
		</select>
	  </div>
	  <div>
		<label class="label" for="tune">Tune</label>
		<select id="tune" class="select" bind:value={tune}>
		  <option value="hq">High Quality</option>
		  <option value="ll">Low Latency</option>
		  <option value="ull">Ultra Low Latency</option>
		  <option value="lossless">Lossless</option>
		</select>
	  </div>
	</div>

	<div style="margin-top:12px">
	  <button class="btn alt" on:click={saveDefaults} disabled={saving}>{saving ? 'Saving…' : 'Save defaults'}</button>
	</div>
  </div>

	<!-- Support (collapsed by default) -->
	<div class="card" style="padding:8px">
		<details>
			<summary style="cursor:pointer; list-style:none; display:flex; align-items:center; gap:8px">
				<span class="title" style="margin:0; font-size:18px">Support the Project</span>
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>
			</summary>
			<div style="margin-top:12px">
				<p class="label" style="color:#cbd5e1">If 8mb.local helps you, a small gesture goes a long way. Thank you for supporting continued development!</p>
				<div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:10px">
					  <a class="btn" style="text-decoration:none" href="https://www.paypal.com/paypalme/jasonselsley" target="_blank" rel="noopener noreferrer">Support via PayPal</a>
					<a class="btn" style="text-decoration:none; background:#374151" href="https://github.com/JMS1717/8mb.local" target="_blank" rel="noopener noreferrer">Star on GitHub</a>
				</div>
			</div>
		</details>
	</div>
</div>
