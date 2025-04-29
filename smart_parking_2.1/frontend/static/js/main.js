// main.js
let currentCameraId = 0;
let streamInterval = null;
let cameraListUpdater = null;

// 登录功能
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) throw new Error('登录失败');
        return response.json();
    })
    .then(data => {
        localStorage.setItem('token', data.access_token);
        document.getElementById('loginContainer').classList.add('hidden');
        document.getElementById('videoPanel').classList.remove('hidden');
        startVideoStream(data.access_token);
    })
    .catch(error => alert('用户名或密码错误'));
});

// 注册功能
document.getElementById('registerForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;

    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.msg);
        if (response.status === 201) {
            document.getElementById('registerContainer').classList.add('hidden');
            document.getElementById('loginContainer').classList.remove('hidden');
        }
    });
});

// 界面切换
document.getElementById('registerLink').addEventListener('click', () => {
    document.getElementById('loginContainer').classList.add('hidden');
    document.getElementById('registerContainer').classList.remove('hidden');
});

document.getElementById('loginLink').addEventListener('click', () => {
    document.getElementById('registerContainer').classList.add('hidden');
    document.getElementById('loginContainer').classList.remove('hidden');
});

// 视频流功能
function startVideoStream(token) {
    fetch('/available_cameras', {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(data => {
        if(data.available_cameras.length === 0) {
            alert('没有可用的摄像头');
            return;
        }
        currentCameraId = data.current_camera;
        initVideoStream(token, currentCameraId);
        setupCameraControls(data.available_cameras);
        startAutoRecovery();

        // 定期更新摄像头列表
        cameraListUpdater = setInterval(() => {
            fetch('/available_cameras', {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            .then(response => response.json())
            .then(data => {
                const controls = document.querySelector('.camera-controls');
                if (controls) controls.remove();
                setupCameraControls(data.available_cameras);
            });
        }, 10000);
    })
    .catch(error => {
        console.error('摄像头列表获取失败:', error);
        alert('无法获取摄像头信息');
    });
}

function initVideoStream(token, camId) {
    // 清理旧资源
    const oldImg = document.getElementById('videoStream');
    if (oldImg) {
        oldImg.onerror = null;
        oldImg.src = '';
        oldImg.remove();
    }
    if (streamInterval) {
        clearInterval(streamInterval);
        streamInterval = null;
    }

    // 创建新视频元素
    const img = document.createElement('img');
    img.id = 'videoStream';
    img.className = 'live-feed';
    const videoUrl = `/video_feed/${camId}?token=${token}&ts=${Date.now()}`;
    img.src = videoUrl;

    // 错误处理
    img.onerror = function() {
        console.log('视频流中断，尝试重新连接...');
        this.src = `${videoUrl}&retry=${Date.now()}`;
        setTimeout(() => {
            if (this.naturalWidth === 0) {
                initVideoStream(token, camId);
            }
        }, 2000);
    };

    // 添加新元素
    videoContainer.appendChild(img);

    // 心跳检测
    streamInterval = setInterval(() => {
        if (img.naturalWidth === 0) {
            console.log('心跳检测到画面丢失，刷新视频流...');
            img.src = `${videoUrl}&ping=${Date.now()}`;
        }
    }, 3000);
}

function setupCameraControls(cameras) {
    const controls = document.createElement('div');
    controls.className = 'camera-controls';

    cameras.forEach(camId => {
        const btn = document.createElement('button');
        btn.textContent = `摄像头 ${camId}`;
        btn.onclick = () => switchCamera(camId);
        controls.appendChild(btn);
    });

    videoContainer.prepend(controls);
}

function switchCamera(newCamId) {
    if (newCamId === currentCameraId) return;
    const token = localStorage.getItem('token');
    if (!token) return;
    initVideoStream(token, newCamId);
    currentCameraId = newCamId;
}

function startAutoRecovery() {
    setInterval(() => {
        const img = document.getElementById('videoStream');
        if (img && img.naturalWidth === 0) {
            console.log('自动恢复机制触发...');
            const token = localStorage.getItem('token');
            if (token) {
                initVideoStream(token, currentCameraId);
            }
        }
    }, 5000);
}

// 退出功能
document.getElementById('logoutButton').addEventListener('click', () => {
    localStorage.removeItem('token');
    document.getElementById('videoPanel').classList.add('hidden');
    document.getElementById('loginContainer').classList.remove('hidden');
    clearInterval(streamInterval);
    clearInterval(cameraListUpdater);
});