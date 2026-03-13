# -*- coding: utf-8 -*-
"""
鸣潮动作数据汇总 - Flask后端API + 内置排轴DPS计算器
"""

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from sqlalchemy import or_, and_, func
from models import (
    init_db, get_session, Character, Action, Echo, Enemy,
    Gender, BodyType, Element, WeaponType, ActionType, PositionState
)
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 初始化数据库
db_path = os.path.join(os.path.dirname(__file__), 'wuwa_data.db')
engine = init_db(db_path)

def get_db_session():
    return get_session(engine)

# ==================== 角色相关API ====================

@app.route('/api/characters', methods=['GET'])
def get_characters():
    session = get_db_session()
    try:
        gender = request.args.get('gender')
        body_type = request.args.get('body_type')
        element = request.args.get('element')
        search = request.args.get('search')
        
        query = session.query(Character)
        
        if gender:
            query = query.filter(Character.gender == Gender(gender))
        if body_type:
            query = query.filter(Character.body_type == BodyType(body_type))
        if element:
            query = query.filter(Character.element == Element(element))
        if search:
            query = query.filter(Character.name.contains(search))
        
        query = query.order_by(Character.name)
        characters = query.all()
        
        return jsonify({
            'success': True,
            'data': [char.to_dict() for char in characters],
            'total': len(characters)
        })
    finally:
        session.close()

@app.route('/api/characters/<int:char_id>', methods=['GET'])
def get_character(char_id):
    session = get_db_session()
    try:
        char = session.query(Character).get(char_id)
        if not char:
            return jsonify({'success': False, 'error': '角色不存在'}), 404
        
        action_types = session.query(
            Action.action_type,
            func.count(Action.id)
        ).filter_by(character_id=char_id).group_by(Action.action_type).all()
        
        result = char.to_dict()
        result['action_stats'] = {
            at.value if at else '未知': count 
            for at, count in action_types
        }
        
        return jsonify({'success': True, 'data': result})
    finally:
        session.close()

@app.route('/api/characters/<int:char_id>/actions', methods=['GET'])
def get_character_actions(char_id):
    session = get_db_session()
    try:
        action_type = request.args.get('type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        query = session.query(Action).filter_by(character_id=char_id)
        
        if action_type:
            query = query.filter(Action.action_type == ActionType(action_type))
        
        query = query.order_by(Action.action_type, Action.start_frame)
        
        total = query.count()
        actions = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'success': True,
            'data': [action.to_dict() for action in actions],
            'total': total,
            'page': page,
            'per_page': per_page
        })
    finally:
        session.close()

# ==================== 动作查询API ====================

@app.route('/api/actions', methods=['GET'])
def get_actions():
    session = get_db_session()
    try:
        char_id = request.args.get('character_id', type=int)
        action_type = request.args.get('type')
        search = request.args.get('search')
        
        min_start_frame = request.args.get('min_start_frame', type=int)
        max_start_frame = request.args.get('max_start_frame', type=int)
        min_poise = request.args.get('min_poise', type=float)
        max_poise = request.args.get('max_poise', type=float)
        
        can_parry = request.args.get('can_parry')
        can_detach = request.args.get('can_detach')
        position_state = request.args.get('position_state')
        
        sort_by = request.args.get('sort_by', 'start_frame')
        sort_order = request.args.get('sort_order', 'asc')
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        query = session.query(Action)
        
        if char_id:
            query = query.filter(Action.character_id == char_id)
        if action_type:
            query = query.filter(Action.action_type == ActionType(action_type))
        if search:
            query = query.filter(
                or_(
                    Action.action_name.contains(search),
                    Action.notes.contains(search)
                )
            )
        
        if min_start_frame is not None:
            query = query.filter(Action.start_frame >= min_start_frame)
        if max_start_frame is not None:
            query = query.filter(Action.start_frame <= max_start_frame)
        if min_poise is not None:
            query = query.filter(Action.poise_damage >= min_poise)
        if max_poise is not None:
            query = query.filter(Action.poise_damage <= max_poise)
        
        if can_parry == 'true':
            query = query.filter(Action.can_parry == True)
        if can_detach == 'true':
            query = query.filter(Action.can_detach == True)
        if position_state:
            query = query.filter(Action.position_state == PositionState(position_state))
        
        sort_column = getattr(Action, sort_by, Action.start_frame)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        total = query.count()
        actions = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'success': True,
            'data': [action.to_dict() for action in actions],
            'total': total,
            'page': page,
            'per_page': per_page
        })
    finally:
        session.close()

# ==================== 声骸API ====================

@app.route('/api/echoes', methods=['GET'])
def get_echoes():
    session = get_db_session()
    try:
        search = request.args.get('search')
        skill_type = request.args.get('skill_type')
        
        query = session.query(Echo)
        
        if search:
            query = query.filter(
                or_(
                    Echo.name.contains(search),
                    Echo.action_name.contains(search)
                )
            )
        if skill_type:
            query = query.filter(Echo.skill_type == skill_type)
        
        echoes = query.order_by(Echo.name).all()
        
        return jsonify({
            'success': True,
            'data': [echo.to_dict() for echo in echoes],
            'total': len(echoes)
        })
    finally:
        session.close()

# ==================== 统计数据API ====================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    session = get_db_session()
    try:
        char_count = session.query(Character).count()
        action_count = session.query(Action).count()
        echo_count = session.query(Echo).count()
        
        gender_stats = session.query(
            Character.gender,
            func.count(Character.id)
        ).group_by(Character.gender).all()
        
        body_stats = session.query(
            Character.body_type,
            func.count(Character.id)
        ).group_by(Character.body_type).all()
        
        action_type_stats = session.query(
            Action.action_type,
            func.count(Action.id)
        ).group_by(Action.action_type).all()
        
        return jsonify({
            'success': True,
            'data': {
                'total_characters': char_count,
                'total_actions': action_count,
                'total_echoes': echo_count,
                'gender_distribution': {
                    g.value if g else '未知': count 
                    for g, count in gender_stats
                },
                'body_type_distribution': {
                    bt.value if bt else '未知': count 
                    for bt, count in body_stats
                },
                'action_type_distribution': {
                    at.value if at else '未知': count 
                    for at, count in action_type_stats
                }
            }
        })
    finally:
        session.close()

@app.route('/api/filters', methods=['GET'])
def get_filters():
    return jsonify({
        'success': True,
        'data': {
            'genders': [{'value': g.value, 'label': g.value} for g in Gender],
            'body_types': [{'value': bt.value, 'label': bt.value} for bt in BodyType],
            'elements': [{'value': e.value, 'label': e.value} for e in Element],
            'weapon_types': [{'value': wt.value, 'label': wt.value} for wt in WeaponType],
            'action_types': [{'value': at.value, 'label': at.value} for at in ActionType],
            'position_states': [{'value': ps.value, 'label': ps.value} for ps in PositionState],
        }
    })

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

# ==================== 主页 ====================

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>鸣潮动作数据汇总</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f5f7fa; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
        .stat-card h3 { color: #606266; font-size: 14px; margin-bottom: 10px; }
        .stat-card .number { font-size: 32px; font-weight: bold; color: #409eff; }
        .section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .section h2 { margin-bottom: 15px; color: #303133; }
        .btn { display: inline-block; padding: 10px 20px; background: #409eff; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px; margin-bottom: 10px; }
        .btn:hover { background: #66b1ff; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ebeef5; }
        th { background: #f5f7fa; font-weight: bold; color: #606266; }
        tr:hover { background: #f5f7fa; }
        .tag { display: inline-block; padding: 2px 8px; background: #ecf5ff; color: #409eff; border-radius: 4px; font-size: 12px; margin-right: 5px; }
        .loading { text-align: center; padding: 40px; color: #909399; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>鸣潮动作数据汇总</h1>
            <p>完整的数据查询系统 | 数据来源：鸣潮动作数据汇总.xlsx</p>
        </div>
        
        <div class="stats-grid" id="stats">
            <div class="loading">加载统计数据...</div>
        </div>
        
        <div class="section">
            <h2>快速导航</h2>
            <a href="#characters" class="btn" onclick="loadCharacters()">角色数据库</a>
            <a href="#actions" class="btn" onclick="loadActions()">动作查询</a>
            <a href="#echoes" class="btn" onclick="loadEchoes()">声骸数据库</a>
            <a href="/calculator" class="btn" style="background: #67c23a;">排轴DPS计算器</a>
            <a href="/api/stats" class="btn" target="_blank">API统计</a>
        </div>
        
        <div class="section">
            <h2>角色列表</h2>
            <div id="characters">
                <div class="loading">点击上方"角色数据库"按钮加载数据</div>
            </div>
        </div>
        
        <div class="section">
            <h2>声骸列表</h2>
            <div id="echoes">
                <div class="loading">点击上方"声骸数据库"按钮加载数据</div>
            </div>
        </div>
    </div>
    
    <script>
        function loadStats() {
            fetch("/api/stats")
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const s = data.data;
                        document.getElementById("stats").innerHTML = `
                            <div class="stat-card"><h3>角色总数</h3><div class="number">${s.total_characters}</div></div>
                            <div class="stat-card"><h3>动作总数</h3><div class="number">${s.total_actions}</div></div>
                            <div class="stat-card"><h3>声骸总数</h3><div class="number">${s.total_echoes}</div></div>
                            <div class="stat-card"><h3>女/男角色</h3><div class="number">${s.gender_distribution["女"] || 0}/${s.gender_distribution["男"] || 0}</div></div>
                        `;
                    }
                })
                .catch(e => console.error(e));
        }
        loadStats();
        
        function loadCharacters() {
            document.getElementById("characters").innerHTML = "<div class=\"loading\">加载中...</div>";
            fetch("/api/characters")
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        let html = "<table><tr><th>角色名</th><th>性别</th><th>体型</th><th>属性</th><th>动作数</th></tr>";
                        data.data.forEach(c => {
                            html += `<tr><td><strong>${c.name}</strong></td><td><span class="tag">${c.gender}</span></td><td><span class="tag">${c.body_type}</span></td><td><span class="tag">${c.element || "-"}</span></td><td>${c.action_count}</td></tr>`;
                        });
                        html += "</table>";
                        document.getElementById("characters").innerHTML = html;
                    }
                });
        }
        
        function loadEchoes() {
            document.getElementById("echoes").innerHTML = "<div class=\"loading\">加载中...</div>";
            fetch("/api/echoes")
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const echoes = data.data.slice(0, 50);
                        let html = "<table><tr><th>声骸名称</th><th>动作</th><th>类型</th><th>冷却</th><th>削韧</th></tr>";
                        echoes.forEach(e => {
                            html += `<tr><td><strong>${e.name}</strong></td><td>${e.action_name}</td><td><span class="tag">${e.skill_type || "-"}</span></td><td>${e.cooldown ? e.cooldown + "s" : "-"}</td><td>${e.poise_damage || "-"}</td></tr>`;
                        });
                        html += "</table>";
                        document.getElementById("echoes").innerHTML = html;
                    }
                });
        }
        
        function loadActions() {
            window.open("/api/actions?per_page=100", "_blank");
        }
    </script>
</body>
</html>
    '''


# ==================== 排轴DPS计算器页面（内置Excel解析） ====================


# ==================== 排轴DPS计算器API ====================

# 存储计算器数据（生产环境应使用数据库）
CALCULATOR_SAVES_DIR = os.path.join(os.path.dirname(__file__), 'calculator_saves')
os.makedirs(CALCULATOR_SAVES_DIR, exist_ok=True)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """提供uploads目录下的文件访问"""
    uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    return send_from_directory(uploads_dir, filename)

@app.route('/calculator')
def calculator_page():
    """排轴DPS计算器页面 - 真实拉表版（最终版本）"""
    return render_template('real_luckysheet.html')

@app.route('/characters')
def characters_page():
    """角色列表页面"""
    return render_template('characters.html')

@app.route('/wiki')
def wiki_page():
    """常识手册页面"""
    return render_template('wiki.html')

@app.route('/api/calculator/save', methods=['POST'])
def save_calculator():
    """保存计算器数据"""
    try:
        data = request.get_json()
        name = data.get('name', '未命名')
        calc_data = data.get('data', {})
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}.json"
        filepath = os.path.join(CALCULATOR_SAVES_DIR, filename)
        
        # 保存数据
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'name': name,
                'time': datetime.now().isoformat(),
                'data': calc_data
            }, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calculator/list', methods=['GET'])
def list_calculator_saves():
    """列出所有保存的计算器数据"""
    try:
        saves = []
        for filename in os.listdir(CALCULATOR_SAVES_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(CALCULATOR_SAVES_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    saves.append({
                        'name': data.get('name', filename),
                        'filename': filename,
                        'time': data.get('time', '')
                    })
        
        # 按时间倒序
        saves.sort(key=lambda x: x['time'], reverse=True)
        return jsonify(saves)
    except Exception as e:
        return jsonify([])

@app.route('/api/calculator/load', methods=['GET'])
def load_calculator():
    """加载计算器数据"""
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({'success': False, 'error': '未指定文件名'}), 400
        
        # 查找文件
        filepath = None
        for filename in os.listdir(CALCULATOR_SAVES_DIR):
            if filename.endswith('.json'):
                fpath = os.path.join(CALCULATOR_SAVES_DIR, filename)
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('name') == name:
                        filepath = fpath
                        break
        
        if not filepath:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({'success': True, 'data': data.get('data', {})})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calculator/delete', methods=['POST'])
def delete_calculator():
    """删除计算器数据"""
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'success': False, 'error': '未指定文件名'}), 400
        
        # 查找并删除文件
        for filename in os.listdir(CALCULATOR_SAVES_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(CALCULATOR_SAVES_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    if file_data.get('name') == name:
                        os.remove(filepath)
                        return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12056, debug=True)
