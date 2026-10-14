// MusiConnect Frontend Application Logic

let currentJobId = null;
let eventSource = null;
let currentPreviewPlaylist = null;

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    fetchStatus();
    initEventListeners();
});

// Tab Switcher
function initTabs() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const target = btn.getAttribute('data-tab');
            document.getElementById(target).classList.add('active');

            if (target === 'history') {
                fetchHistory();
            }
        });
    });
}

function initEventListeners() {
    // Preview Button
    document.getElementById('btn-preview').addEventListener('click', handlePreview);
    document.getElementById('spotify-url-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handlePreview();
    });

    // Start Transfer Button
    document.getElementById('btn-start-transfer').addEventListener('click', handleStartTransfer);

    // Cancel Transfer Button
    document.getElementById('btn-cancel-transfer').addEventListener('click', handleCancelTransfer);

    // Settings Form
    document.getElementById('settings-form').addEventListener('submit', handleSaveSettings);

    // YouTube Connect Form
    document.getElementById('yt-connect-form').addEventListener('submit', handleConnectYouTube);
    document.getElementById('btn-yt-disconnect').addEventListener('click', handleDisconnectYouTube);

    // Spotify Login Button
    document.getElementById('btn-spotify-login').addEventListener('click', handleSpotifyLogin);
}

async function handleSpotifyLogin() {
    try {
        const res = await fetch('/api/spotify/login');
        const data = await res.json();
        if (data.url) {
            window.location.href = data.url;
        } else {
            alert('Giriş linki alınamadı: ' + (data.detail || 'Bilinmeyen hata'));
        }
    } catch (err) {
        alert('Giriş başlatılamadı: ' + err.message);
    }
}

// Fetch Global Connection Status
async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        renderStatus(data);
    } catch (err) {
        console.error('Status fetch error:', err);
    }
}

function renderStatus(data) {
    const spStatus = document.getElementById('spotify-status-indicator');
    const spText = document.getElementById('spotify-status-text');
    const ytStatus = document.getElementById('yt-status-indicator');
    const ytText = document.getElementById('yt-status-text');

    // Spotify status
    const spUserConnected = document.getElementById('spotify-user-connected');
    const spUserName = document.getElementById('spotify-user-name');
    const spLoginBtn = document.getElementById('btn-spotify-login');

    if (data.spotify.user_logged_in) {
        spStatus.className = 'status-indicator status-green';
        spText.textContent = `Spotify: ${data.spotify.user_name || 'Bağlı'}`;
        if (spUserConnected) spUserConnected.style.display = 'flex';
        if (spUserName) spUserName.textContent = data.spotify.user_name || 'Giriş Yapıldı';
        if (spLoginBtn) spLoginBtn.textContent = 'Farklı Hesapla Giriş Yap';
    } else if (data.spotify.connected) {
        spStatus.className = 'status-indicator status-green';
        spText.textContent = 'Spotify: Giriş Bekleniyor';
        if (spUserConnected) spUserConnected.style.display = 'none';
        if (spLoginBtn) spLoginBtn.textContent = 'Spotify ile Giriş Yap (Yetkilendir)';
    } else {
        spStatus.className = 'status-indicator status-red';
        spText.textContent = 'Spotify: Anahtar Gerekli';
        if (spUserConnected) spUserConnected.style.display = 'none';
    }

    // YouTube status
    const ytCardConnected = document.getElementById('yt-account-connected');
    const ytCardDisconnected = document.getElementById('yt-account-disconnected');

    if (data.youtube.connected) {
        ytStatus.className = 'status-indicator status-green';
        ytText.textContent = 'YouTube: Bağlı';
        
        ytCardConnected.style.display = 'block';
        ytCardDisconnected.style.display = 'none';

        if (data.youtube.account) {
            document.getElementById('yt-account-name').textContent = data.youtube.account.accountName || 'YouTube Music Hesabı';
            document.getElementById('yt-account-handle').textContent = data.youtube.account.channelHandle || '';
            if (data.youtube.account.accountPhotoUrl) {
                document.getElementById('yt-account-photo').src = data.youtube.account.accountPhotoUrl;
            }
        }
    } else {
        ytStatus.className = 'status-indicator status-red';
        ytText.textContent = 'YouTube: Giriş Yapılmadı';

        ytCardConnected.style.display = 'none';
        ytCardDisconnected.style.display = 'block';
    }

    // Populate settings inputs
    if (data.spotify.client_id) {
        document.getElementById('cfg-spotify-client-id').value = data.spotify.client_id;
    }
    if (data.settings) {
        document.getElementById('cfg-delay').value = data.settings.transfer_delay;
        document.getElementById('cfg-tolerance').value = data.settings.duration_tolerance;
        document.getElementById('cfg-batch').value = data.settings.batch_size;
    }
}

// Preview Spotify Playlist
async function handlePreview() {
    const input = document.getElementById('spotify-url-input');
    const url = input.value.trim();
    if (!url) {
        alert('Lütfen geçerli bir Spotify çalma listesi linki girin.');
        return;
    }

    const previewContainer = document.getElementById('preview-container');
    const btnPreview = document.getElementById('btn-preview');
    btnPreview.disabled = true;
    btnPreview.innerHTML = '<span>Yükleniyor...</span>';

    try {
        const res = await fetch('/api/spotify/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Liste bilgileri alınamadı.');
        }

        currentPreviewPlaylist = data.playlist;
        renderPreview(data);
        previewContainer.style.display = 'block';
    } catch (err) {
        if (err.message.includes('yetkilendirin') || err.message.includes('authentication required')) {
            if (confirm(err.message + '\n\nŞimdi Spotify ile giriş yapıp yetkilendirmek ister misiniz?')) {
                handleSpotifyLogin();
            }
        } else {
            alert(`Hata: ${err.message}`);
        }
        previewContainer.style.display = 'none';
    } finally {
        btnPreview.disabled = false;
        btnPreview.innerHTML = '<span>Önizle</span>';
    }
}

function renderPreview(data) {
    const { playlist, preview_tracks, total_tracks } = data;

    document.getElementById('preview-cover').src = playlist.image_url || 'https://via.placeholder.com/130?text=Playlist';
    document.getElementById('preview-title').textContent = playlist.name;
    document.getElementById('preview-owner').textContent = playlist.owner ? `Oluşturan: ${playlist.owner}` : '';
    document.getElementById('preview-count').textContent = `${total_tracks} Şarkı`;
    document.getElementById('target-name-input').value = playlist.name;

    const tbody = document.getElementById('track-list-body');
    tbody.innerHTML = '';

    preview_tracks.forEach((track, i) => {
        const tr = document.createElement('tr');
        const durationMin = Math.floor(track.duration_seconds / 60);
        const durationSec = (track.duration_seconds % 60).toString().padStart(2, '0');

        tr.innerHTML = `
            <td>${i + 1}</td>
            <td>
                <div class="track-item-cell">
                    <img src="${track.image_url || 'https://via.placeholder.com/36'}" class="track-thumb" />
                    <div>
                        <div style="font-weight: 600;">${escapeHtml(track.title)}</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(track.artists.join(', '))}</div>
                    </div>
                </div>
            </td>
            <td>${escapeHtml(track.album || '-')}</td>
            <td>${durationMin}:${durationSec}</td>
        `;
        tbody.appendChild(tr);
    });

    const moreText = document.getElementById('preview-more-tracks');
    if (total_tracks > preview_tracks.length) {
        moreText.textContent = `... ve ${total_tracks - preview_tracks.length} şarkı daha (tüm liste aktarılacak)`;
        moreText.style.display = 'block';
    } else {
        moreText.style.display = 'none';
    }
}

// Start Transfer Job
async function handleStartTransfer() {
    const url = document.getElementById('spotify-url-input').value.trim();
    const customName = document.getElementById('target-name-input').value.trim();
    const isPrivate = document.getElementById('target-privacy-select').value === 'true';

    const btnStart = document.getElementById('btn-start-transfer');
    btnStart.disabled = true;

    try {
        const res = await fetch('/api/transfer/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, custom_name: customName, is_private: isPrivate })
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Aktarım başlatılamadı.');
        }

        currentJobId = data.job_id;
        openTransferModal();
        connectEventSource(currentJobId);
    } catch (err) {
        alert(`Aktarım Başlatma Hatası: ${err.message}`);
    } finally {
        btnStart.disabled = false;
    }
}

function openTransferModal() {
    const modal = document.getElementById('transfer-modal');
    modal.classList.add('active');

    // Reset modal state
    document.getElementById('modal-progress-bar').style.width = '0%';
    document.getElementById('modal-progress-text').textContent = 'Hazırlanıyor...';
    document.getElementById('modal-stats-text').textContent = '0 / 0 Şarkı';
    document.getElementById('live-console').innerHTML = '';
    document.getElementById('btn-cancel-transfer').style.display = 'inline-block';
    document.getElementById('btn-view-playlist').style.display = 'none';
}

function connectEventSource(jobId) {
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`/api/transfer/stream/${jobId}`);
    const consoleEl = document.getElementById('live-console');

    eventSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        handleStreamEvent(data, consoleEl);
    };

    eventSource.onerror = (err) => {
        console.error('SSE Error:', err);
        eventSource.close();
    };
}

function handleStreamEvent(data, consoleEl) {
    const pBar = document.getElementById('modal-progress-bar');
    const pText = document.getElementById('modal-progress-text');
    const sText = document.getElementById('modal-stats-text');

    if (data.type === 'start') {
        logConsole(consoleEl, `🚀 Aktarım başladı! Toplam: ${data.total} şarkı`, 'info');
        pText.textContent = `0 / ${data.total} şarkı işlendi (%0)`;
    } else if (data.type === 'item_updated') {
        const item = data.item;
        const percent = Math.round((data.processed / data.total) * 100);
        pBar.style.width = `${percent}%`;
        pText.textContent = `${data.processed} / ${data.total} şarkı işlendi (%${percent})`;
        sText.textContent = `Eşleşen: ${data.processed - data.failed} | Başarısız: ${data.failed}`;

        if (item.status === 'matched') {
            logConsole(consoleEl, `[${item.index}/${data.total}] 🎵 Eşleşti: ${item.source_track.title} ➔ ${item.matched_result.title} (Skor: ${item.matched_result.match_score}%)`);
        } else if (item.status === 'not_found') {
            logConsole(consoleEl, `[${item.index}/${data.total}] ⚠️ Bulunamadı: ${item.source_track.title} - ${item.source_track.artists.join(', ')}`, 'warning');
        }
    } else if (data.type === 'batch_added') {
        logConsole(consoleEl, `💾 ${data.added_count} şarkı YouTube Music listesine yazıldı! (Toplam eklenen: ${data.total_added})`, 'success');
    } else if (data.type === 'finished') {
        const summary = data.summary;
        pBar.style.width = '100%';
        pText.textContent = `Tamamlandı! (${summary.added_count}/${summary.total_tracks} şarkı YouTube Music'e aktarıldı)`;
        logConsole(consoleEl, `🎉 AKTARIM TAMAMLANDI! Süre: ${summary.duration_seconds} sn`, 'success');

        document.getElementById('btn-cancel-transfer').style.display = 'none';
        const viewBtn = document.getElementById('btn-view-playlist');
        viewBtn.href = summary.target_playlist_url;
        viewBtn.style.display = 'inline-flex';

        if (eventSource) eventSource.close();
    } else if (data.type === 'error') {
        logConsole(consoleEl, `❌ HATA: ${data.error}`, 'error');
        pText.textContent = 'Aktarım hata ile sonuçlandı.';
        if (eventSource) eventSource.close();
    }
}

function logConsole(consoleEl, text, level = 'default') {
    const line = document.createElement('div');
    line.className = 'console-entry';
    if (level === 'success') line.style.color = '#10b981';
    else if (level === 'warning') line.style.color = '#f59e0b';
    else if (level === 'error') line.style.color = '#ef4444';
    else if (level === 'info') line.style.color = '#38bdf8';
    
    line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    consoleEl.prepend(line);
}

async function handleCancelTransfer() {
    if (!currentJobId) return;
    if (!confirm('Aktarım işlemini iptal etmek istediğinize emin misiniz?')) return;

    try {
        await fetch(`/api/transfer/cancel/${currentJobId}`, { method: 'POST' });
        logConsole(document.getElementById('live-console'), '🛑 İptal isteği gönderildi...', 'warning');
    } catch (err) {
        console.error('Cancel error:', err);
    }
}

// Close Modal
document.getElementById('btn-close-modal').addEventListener('click', () => {
    document.getElementById('transfer-modal').classList.remove('active');
    if (eventSource) eventSource.close();
});

// Settings Save
async function handleSaveSettings(e) {
    e.preventDefault();
    const clientId = document.getElementById('cfg-spotify-client-id').value.trim();
    const clientSecret = document.getElementById('cfg-spotify-client-secret').value.trim();
    const delay = parseFloat(document.getElementById('cfg-delay').value);
    const tolerance = parseInt(document.getElementById('cfg-tolerance').value);
    const batch = parseInt(document.getElementById('cfg-batch').value);

    const body = {
        spotify_client_id: clientId,
        transfer_delay: delay,
        duration_tolerance: tolerance,
        batch_size: batch
    };
    if (clientSecret) {
        body.spotify_client_secret = clientSecret;
    }

    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.success) {
            alert('Ayarlar başarıyla kaydedildi!');
            fetchStatus();
        }
    } catch (err) {
        alert(`Ayarlar kaydedilemedi: ${err.message}`);
    }
}

// YouTube Connect
async function handleConnectYouTube(e) {
    e.preventDefault();
    const headersRaw = document.getElementById('yt-headers-input').value.trim();
    if (!headersRaw) {
        alert('Lütfen kopyaladığınız request headers içeriğini yapıştırın.');
        return;
    }

    const btn = document.getElementById('btn-submit-yt');
    btn.disabled = true;
    btn.textContent = 'Doğrulanıyor...';

    try {
        const res = await fetch('/api/youtube/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ headers_raw: headersRaw })
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Giriş yapılamadı.');
        }

        alert('YouTube Music bağlantısı başarıyla kuruldu!');
        document.getElementById('yt-headers-input').value = '';
        fetchStatus();
    } catch (err) {
        alert(`Bağlantı Hatası: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Bağlan ve Doğrula';
    }
}

// YouTube Disconnect
async function handleDisconnectYouTube() {
    if (!confirm('YouTube Music bağlantısını kesmek istediğinize emin misiniz?')) return;
    try {
        await fetch('/api/youtube/disconnect', { method: 'POST' });
        fetchStatus();
    } catch (err) {
        console.error('Disconnect error:', err);
    }
}

// History
async function fetchHistory() {
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        renderHistory(data.history || []);
    } catch (err) {
        console.error('History fetch error:', err);
    }
}

function renderHistory(list) {
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '';

    if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 2rem;">Henüz bir aktarım geçmişi yok.</td></tr>';
        return;
    }

    list.forEach(item => {
        const tr = document.createElement('tr');
        const badgeColor = item.status === 'completed' ? '#10b981' : (item.status === 'cancelled' ? '#f59e0b' : '#ef4444');
        const statusText = item.status === 'completed' ? 'Tamamlandı' : (item.status === 'cancelled' ? 'İptal Edildi' : 'Hata');

        tr.innerHTML = `
            <td>${item.created_at || '-'}</td>
            <td><strong>${escapeHtml(item.source_playlist_name)}</strong></td>
            <td>${item.added_count} / ${item.total_tracks}</td>
            <td><span style="color: ${badgeColor}; font-weight: 700;">● ${statusText}</span></td>
            <td>${item.duration_seconds} sn</td>
            <td>
                ${item.target_playlist_url ? `<a href="${item.target_playlist_url}" target="_blank" style="color: var(--yt-red); text-decoration: none; font-weight: 600;">YouTube'da Aç ↗</a>` : '-'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
