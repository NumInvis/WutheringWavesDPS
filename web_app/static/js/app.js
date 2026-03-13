// 鸣潮DPS计算器 - 前端应用

// 全局状态
const state = {
    characters: [],
    echoes: [],
    weapons: [],
    currentCharacter: null,
    calculationConfig: {
        echo_c3_count: 2,
        echo_c3_element_dmg: 60.0,
        echo_set_bonus: 20.0,
        support_atk_pct: 61.5,
        support_element_dmg: 12.0,
        support_all_amplify: 35.0,
        support_e_amplify: 25.0,
        support_q_amplify: 32.0,
        support_crit_rate: 12.5,
        support_crit_dmg: 25.0,
        time_seconds: 25.0
    },
    skills: []
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('鸣潮DPS计算器已加载');
    loadInitialData();
});

// 加载初始数据
async function loadInitialData() {
    try {
        // 加载角色列表
        const charRes = await fetch('/api/characters');
        const charData = await charRes.json();
        if (charData.success) {
            state.characters = charData.data;
        }
        
        // 加载声骸列表
        const echoRes = await fetch('/api/echoes');
        const echoData = await echoRes.json();
        if (echoData.success) {
            state.echoes = echoData.data;
        }
        
        // 加载武器列表
        const weaponRes = await fetch('/api/weapons');
        const weaponData = await weaponRes.json();
        if (weaponData.success) {
            state.weapons = weaponData.data;
        }
    } catch (e) {
        console.error('加载数据失败:', e);
    }
}

// 显示角色列表
async function showCharacterList() {
    const panel = document.getElementById('character-panel');
    const overlay = document.getElementById('overlay');
    const listContainer = document.getElementById('character-list');
    
    // 加载角色数据
    if (state.characters.length === 0) {
        try {
            const res = await fetch('/api/characters');
            const data = await res.json();
            if (data.success) {
                state.characters = data.data;
            }
        } catch (e) {
            console.error('加载角色失败:', e);
        }
    }
    
    // 渲染角色列表
    listContainer.innerHTML = state.characters.map(char => `
        <div class="character-item" onclick="selectCharacter('${char.name}')">
            <div class="character-avatar">${char.name.charAt(0)}</div>
            <div class="character-info">
                <h4>${char.name}</h4>
                <span>${char.element || '未知属性'} · ${char.gender || '未知'}</span>
            </div>
        </div>
    `).join('');
    
    panel.classList.add('open');
    overlay.classList.add('show');
}

// 显示声骸列表
async function showEchoList() {
    const panel = document.getElementById('echo-panel');
    const overlay = document.getElementById('overlay');
    const listContainer = document.getElementById('echo-list');
    
    // 加载声骸数据
    if (state.echoes.length === 0) {
        try {
            const res = await fetch('/api/echoes');
            const data = await res.json();
            if (data.success) {
                state.echoes = data.data;
            }
        } catch (e) {
            console.error('加载声骸失败:', e);
        }
    }
    
    // 渲染声骸列表
    listContainer.innerHTML = state.echoes.map(echo => `
        <div class="echo-item">
            <h4>${echo.name}</h4>
            <span>COST: ${echo.cost || 4}</span>
        </div>
    `).join('');
    
    panel.classList.add('open');
    overlay.classList.add('show');
}

// 关闭面板
function closePanel(panelId) {
    const panel = document.getElementById(panelId);
    const overlay = document.getElementById('overlay');
    panel.classList.remove('open');
    overlay.classList.remove('show');
}

// 关闭所有面板
function closeAllPanels() {
    document.querySelectorAll('.side-panel').forEach(panel => {
        panel.classList.remove('open');
    });
    document.getElementById('overlay').classList.remove('show');
}

// 选择角色
async function selectCharacter(name) {
    try {
        const res = await fetch(`/api/character/${name}`);
        const data = await res.json();
        if (data.success) {
            state.currentCharacter = data.data;
            console.log('选择角色:', state.currentCharacter);
            
            // 如果当前在计算器页面，更新角色选择
            if (window.location.pathname === '/calculator') {
                updateCalculatorCharacter(data.data);
                // 自动加载角色技能到技能列表
                loadCharacterSkills(data.data.skills);
            } else {
                // 跳转到角色详情页
                window.location.href = `/character/${name}`;
            }
        }
    } catch (e) {
        console.error('加载角色详情失败:', e);
    }
    closeAllPanels();
}

// 加载角色技能到技能列表
function loadCharacterSkills(skills) {
    const skillList = document.getElementById('skill-list');
    if (!skillList || !skills || skills.length === 0) return;
    
    // 清空现有技能
    skillList.innerHTML = '';
    state.skills = [];
    
    // 添加角色技能（只添加前20个主要技能）
    const mainSkills = skills.slice(0, 20);
    
    mainSkills.forEach((skill, index) => {
        const skillItem = document.createElement('div');
        skillItem.className = 'skill-item';
        skillItem.dataset.index = index;
        
        // 确定技能类型缩写
        let skillTypeCode = 'e';
        if (skill.skill_type && skill.skill_type.includes('普攻')) skillTypeCode = 'a';
        else if (skill.skill_type && skill.skill_type.includes('解放')) skillTypeCode = 'q';
        else if (skill.skill_type && skill.skill_type.includes('技能')) skillTypeCode = 'e';
        
        // 获取倍率（从数据库的multiplier字段）
        const multiplier = skill.multiplier ? (skill.multiplier * 100).toFixed(2) : '0';
        
        skillItem.innerHTML = `
            <div class="skill-header">
                <span class="skill-code">${skill.skill_code}</span>
                <span class="skill-name">${skill.skill_type || ''}</span>
                <span class="skill-type">${skill.element || ''}</span>
            </div>
            <div class="skill-config">
                <label>倍率: <input type="number" class="multiplier-input" value="${multiplier}" step="0.01">%</label>
                <label>次数: <input type="number" class="count-input" value="1" min="1"></label>
                <label>类型: 
                    <select class="skill-type-select">
                        <option value="a" ${skillTypeCode === 'a' ? 'selected' : ''}>普攻</option>
                        <option value="e" ${skillTypeCode === 'e' ? 'selected' : ''}>E技能</option>
                        <option value="q" ${skillTypeCode === 'q' ? 'selected' : ''}>Q技能</option>
                    </select>
                </label>
            </div>
        `;
        skillList.appendChild(skillItem);
    });
}

// 更新计算器页面的角色
function updateCalculatorCharacter(character) {
    const charDisplay = document.getElementById('selected-character');
    if (charDisplay) {
        charDisplay.innerHTML = `
            <div class="selected-char">
                <h3>${character.name}</h3>
                <span>${character.element || '未知属性'}</span>
            </div>
        `;
    }
    
    // 更新技能列表
    updateSkillList(character.skills);
}

// 更新技能列表
function updateSkillList(skills) {
    const skillList = document.getElementById('skill-list');
    if (!skillList) return;
    
    if (!skills || skills.length === 0) {
        skillList.innerHTML = '<div class="empty">暂无技能数据</div>';
        return;
    }
    
    skillList.innerHTML = skills.map((skill, index) => `
        <div class="skill-item" data-index="${index}">
            <div class="skill-header">
                <span class="skill-code">${skill.skill_code}</span>
                <span class="skill-name">${skill.skill_name || ''}</span>
                <span class="skill-type">${skill.skill_type || ''}</span>
            </div>
            <div class="skill-config">
                <label>倍率: <input type="number" class="multiplier-input" value="100" step="0.1">%</label>
                <label>次数: <input type="number" class="count-input" value="1" min="1"></label>
            </div>
        </div>
    `).join('');
}

// 添加自定义技能
function addCustomSkill() {
    const skillList = document.getElementById('skill-list');
    if (!skillList) return;
    
    const index = skillList.children.length;
    const skillItem = document.createElement('div');
    skillItem.className = 'skill-item';
    skillItem.dataset.index = index;
    skillItem.innerHTML = `
        <div class="skill-header">
            <input type="text" class="skill-code-input" placeholder="技能代码" value="技能${index + 1}">
            <select class="skill-type-select">
                <option value="e">共鸣技能</option>
                <option value="q">共鸣解放</option>
                <option value="a">普攻</option>
                <option value="h">重击</option>
            </select>
            <button class="btn-remove" onclick="removeSkill(${index})">删除</button>
        </div>
        <div class="skill-config">
            <label>倍率: <input type="number" class="multiplier-input" value="100" step="0.1">%</label>
            <label>次数: <input type="number" class="count-input" value="1" min="1"></label>
        </div>
    `;
    skillList.appendChild(skillItem);
}

// 删除技能
function removeSkill(index) {
    const skillList = document.getElementById('skill-list');
    const skillItem = skillList.querySelector(`[data-index="${index}"]`);
    if (skillItem) {
        skillItem.remove();
    }
}

// 计算DPS
async function calculateDPS() {
    if (!state.currentCharacter) {
        alert('请先选择角色');
        return;
    }
    
    // 收集技能数据
    const skillItems = document.querySelectorAll('.skill-item');
    const skills = [];
    
    skillItems.forEach(item => {
        const codeInput = item.querySelector('.skill-code-input') || item.querySelector('.skill-code');
        const typeSelect = item.querySelector('.skill-type-select');
        const multiplierInput = item.querySelector('.multiplier-input');
        const countInput = item.querySelector('.count-input');
        
        skills.push({
            skill_code: codeInput ? codeInput.value || codeInput.textContent : '未知',
            skill_type: typeSelect ? typeSelect.value : 'e',
            multiplier: parseFloat(multiplierInput ? multiplierInput.value : 100),
            count: parseInt(countInput ? countInput.value : 1)
        });
    });
    
    // 收集配置数据
    const config = {
        echo_c3_count: parseInt(document.getElementById('echo-c3-count')?.value || 2),
        echo_c3_element_dmg: parseFloat(document.getElementById('echo-c3-dmg')?.value || 60),
        echo_set_bonus: parseFloat(document.getElementById('echo-set-bonus')?.value || 20),
        support_atk_pct: parseFloat(document.getElementById('support-atk')?.value || 61.5),
        support_element_dmg: parseFloat(document.getElementById('support-element')?.value || 12),
        support_all_amplify: parseFloat(document.getElementById('support-all-amp')?.value || 35),
        support_e_amplify: parseFloat(document.getElementById('support-e-amp')?.value || 25),
        support_q_amplify: parseFloat(document.getElementById('support-q-amp')?.value || 32),
        support_crit_rate: parseFloat(document.getElementById('support-crit-rate')?.value || 12.5),
        support_crit_dmg: parseFloat(document.getElementById('support-crit-dmg')?.value || 25),
    };
    
    const timeSeconds = parseFloat(document.getElementById('time-seconds')?.value || 25);
    
    try {
        const res = await fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                character_id: state.currentCharacter.id,
                skills: skills,
                config: config,
                time_seconds: timeSeconds
            })
        });
        
        const data = await res.json();
        if (data.success) {
            displayResults(data.data);
        } else {
            alert('计算失败: ' + data.error);
        }
    } catch (e) {
        console.error('计算错误:', e);
        alert('计算错误: ' + e.message);
    }
}

// 显示计算结果
function displayResults(results) {
    const resultsContainer = document.getElementById('calculation-results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = `
        <div class="results-panel">
            <h3>计算结果</h3>
            <div class="result-stats">
                <div class="result-item">
                    <span class="label">面板攻击</span>
                    <span class="value">${results.panel_atk.toFixed(0)}</span>
                </div>
                <div class="result-item">
                    <span class="label">双爆区</span>
                    <span class="value">${results.crit_zone.toFixed(3)}</span>
                </div>
                <div class="result-item">
                    <span class="label">属伤加成</span>
                    <span class="value">${results.element_dmg.toFixed(1)}%</span>
                </div>
                <div class="result-item highlight">
                    <span class="label">总伤害</span>
                    <span class="value">${results.total_damage.toFixed(0)}</span>
                </div>
                <div class="result-item highlight">
                    <span class="label">DPS</span>
                    <span class="value">${results.dps.toFixed(0)}</span>
                </div>
            </div>
            <div class="skill-results">
                <h4>技能详情</h4>
                ${results.skills.map(s => `
                    <div class="skill-result">
                        <span>${s.skill_code}</span>
                        <span>${s.multiplier}% × ${s.count}</span>
                        <span>${s.damage.toFixed(0)}</span>
                        <span>${s.total.toFixed(0)}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// 导入数据
async function importData() {
    try {
        const res = await fetch('/api/import-data', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            alert(`导入成功！\n角色: ${data.characters}\n声骸: ${data.echoes}`);
            location.reload();
        } else {
            alert('导入失败: ' + data.error);
        }
    } catch (e) {
        alert('导入错误: ' + e.message);
    }
}

// 导入拉表文件 - 使用文件选择
async function importLalabiao() {
    // 创建文件输入元素
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.xlsx,.xls';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);
    
    fileInput.onchange = async function() {
        const file = fileInput.files[0];
        if (!file) return;
        
        // 获取sheet名称（使用文件名或默认）
        const sheetName = prompt('请输入Sheet名称（默认使用第一个）:', 'Sheet1') || 'Sheet1';
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('sheet_name', sheetName);
        
        try {
            const res = await fetch('/api/import-lalabiao', {
                method: 'POST',
                body: formData
            });
            
            const data = await res.json();
            if (data.success) {
                alert('拉表导入成功！');
                console.log('面板数据:', data.data.panel);
                console.log('技能数据:', data.data.skills);
            } else {
                alert('导入失败: ' + data.error);
            }
        } catch (e) {
            alert('导入错误: ' + e.message);
        }
        
        document.body.removeChild(fileInput);
    };
    
    fileInput.click();
}
