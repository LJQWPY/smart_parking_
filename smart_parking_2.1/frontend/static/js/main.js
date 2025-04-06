// 获取 DOM 元素
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const registerLink = document.getElementById('registerLink');
const loginLink = document.getElementById('loginLink');
const loginContainer = document.getElementById('loginContainer');
const registerContainer = document.getElementById('registerContainer');
const videoPanel = document.getElementById('videoPanel');
const logoutButton = document.getElementById('logoutButton');
const videoContainer = document.getElementById('videoContainer');

// 切换到注册页面
registerLink.addEventListener('click', (e) => {
    e.preventDefault();
    loginContainer.classList.add('hidden');
    registerContainer.classList.remove('hidden');
});

// 切换到登录页面
loginLink.addEventListener('click', (e) => {
    e.preventDefault();
    registerContainer.classList.add('hidden');
    loginContainer.classList.remove('hidden');
});

// 登录表单提交事件
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    if (!username || !password) {
        console.error('登录失败: 用户名和密码不能为空');
        alert('用户名和密码不能为空');
        return;
    }

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('登录失败:', errorData.msg);
            alert(errorData.msg);
            return;
        }

        const data = await response.json();
        if (!data.access_token) {
            console.error('登录失败: 未获取到有效的访问令牌');
            alert('登录失败: 未获取到有效的访问令牌');
            return;
        }
        loginContainer.classList.add('hidden');
        videoPanel.classList.remove('hidden');
        startVideoStream(data.access_token);
    } catch (error) {
        console.error('登录请求出错:', error);
        alert('登录请求出错，请稍后重试');
    }
});

// 注册表单提交事件
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;

    if (!username || !password) {
        console.error('注册失败: 用户名和密码不能为空');
        alert('用户名和密码不能为空');
        return;
    }

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('注册失败:', errorData.msg);
            alert(errorData.msg);
            return;
        }

        const data = await response.json();
        alert('注册成功，请登录');
        registerContainer.classList.add('hidden');
        loginContainer.classList.remove('hidden');
    } catch (error) {
        console.error('注册请求出错:', error);
        alert('注册请求出错，请稍后重试');
    }
});

// 退出登录按钮点击事件
logoutButton.addEventListener('click', () => {
    videoPanel.classList.add('hidden');
    loginContainer.classList.remove('hidden');
    if (eventSource) {
        eventSource.close();
    }
});

// 开始视频流
let eventSource;
function startVideoStream(token) {
    if (!token) {
        console.error('无法启动视频流: 未提供有效的访问令牌');
        alert('无法启动视频流: 未提供有效的访问令牌');
        videoPanel.classList.add('hidden');
        loginContainer.classList.remove('hidden');
        return;
    }

    eventSource = new EventSource('/video_feed', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (!data.data) {
                console.error('视频流数据解析出错: 数据字段缺失');
                alert('视频流数据解析出错: 数据字段缺失');
                videoPanel.classList.add('hidden');
                loginContainer.classList.remove('hidden');
                return;
            }
            const img = document.createElement('img');
            img.src = `data:image/jpeg;base64,${data.data}`;
            videoContainer.innerHTML = '';
            videoContainer.appendChild(img);
        } catch (parseError) {
            console.error('视频流数据解析出错:', parseError);
            console.error('接收到的数据:', event.data);
            alert('视频流数据解析出错，请稍后重试');
            videoPanel.classList.add('hidden');
            loginContainer.classList.remove('hidden');
        }
    };

    eventSource.onerror = (error) => {
        console.error('EventSource 出错:', error);
        if (error.status === 401) {
            console.error('未授权访问，请重新登录');
            alert('未授权访问，请重新登录');
        } else if (error.status === 404) {
            console.error('视频流资源未找到，请检查后端配置');
            alert('视频流资源未找到，请检查后端配置');
        } else {
            console.error('视频流获取失败，错误状态码:', error.status);
            alert('视频流获取失败，请稍后重试');
        }
        videoPanel.classList.add('hidden');
        loginContainer.classList.remove('hidden');
    };
}
