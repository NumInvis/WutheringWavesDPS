# -*- coding: utf-8 -*-
"""
鸣潮DPS计算器 - Flask Web应用
本地服务器端口: 5030
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import tempfile
import time

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import db, Character, CharacterSkill, Echo, Weapon, CalculationConfig
from data_import.excel_parser import MingchaoDataParser, LalabiaoParser

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)

# 配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wuwa_calc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

# 启用CORS
CORS(app)

# 初始化数据库
db.init_app(app)

# 数据文件路径
DATA_FILE = r'd:\素材\鸣潮动作数据汇总.xlsx'


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/calculator')
def calculator():
    """DPS计算器页面"""
    return render_template('calculator.html')


@app.route('/excel-calc')
def excel_calculator():
    """Excel风格排轴计算器页面"""
    return render_template('excel_calc.html')


@app.route('/univer-calc')
def univer_calculator():
    """Univer满血Excel排轴计算器页面"""
    return render_template('univer_calc.html')


@app.route('/characters')
def characters_list():
    """角色列表页面"""
    return render_template('characters.html')


@app.route('/character/<name>')
def character_detail(name):
    """角色详情页面"""
    return render_template('character.html', name=name)


@app.route('/wiki')
def wiki():
    """鸣潮常识手册Wiki页面"""
    return render_template('wiki.html')


# ==================== API路由 ====================

@app.route('/api/characters')
def get_characters():
    """获取所有角色列表"""
    characters = Character.query.all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in characters]
    })


@app.route('/api/character/<name>')
def get_character(name):
    """获取单个角色详情"""
    character = Character.query.filter_by(name=name).first()
    if not character:
        return jsonify({'success': False, 'error': '角色不存在'}), 404
    return jsonify({
        'success': True,
        'data': character.to_dict()
    })


@app.route('/api/echoes')
def get_echoes():
    """获取所有声骸列表"""
    echoes = Echo.query.all()
    return jsonify({
        'success': True,
        'data': [e.to_dict() for e in echoes]
    })


@app.route('/api/weapons')
def get_weapons():
    """获取所有武器列表"""
    weapons = Weapon.query.all()
    return jsonify({
        'success': True,
        'data': [w.to_dict() for w in weapons]
    })


@app.route('/api/calculate', methods=['POST'])
def calculate_damage():
    """
    计算DPS
    请求体: {
        character_id: int,
        skills: [{skill_code, multiplier, count, skill_type}],
        config: {
            echo_c3_count, echo_c3_element_dmg, echo_set_bonus,
            support_atk_pct, support_element_dmg, support_all_amplify,
            support_e_amplify, support_q_amplify, support_crit_rate, support_crit_dmg
        },
        time_seconds: float
    }
    """
    data = request.json
    
    try:
        character_id = data.get('character_id')
        skills_data = data.get('skills', [])
        config = data.get('config', {})
        time_seconds = data.get('time_seconds', 25.0)
        
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'success': False, 'error': '角色不存在'}), 404
        
        # 计算面板属性
        panel_atk = calculate_panel_atk(character, config)
        crit_zone = calculate_crit_zone(character, config)
        element_dmg = calculate_element_dmg(config)
        
        # 计算每个技能的伤害
        results = []
        total_damage = 0
        
        for skill_data in skills_data:
            skill_type = skill_data.get('skill_type', 'e')
            multiplier = skill_data.get('multiplier', 0)
            count = skill_data.get('count', 1)
            
            # 计算各乘区
            amplify = calculate_amplify_zone(skill_type, config)
            defense = calculate_defense_zone(config)
            resistance = calculate_resistance_zone(config)
            
            # 计算伤害
            damage = (
                panel_atk *
                (multiplier / 100) *
                (1 + element_dmg / 100) *
                crit_zone *
                (1 + amplify) *
                defense *
                resistance
            )
            
            skill_total = damage * count
            total_damage += skill_total
            
            results.append({
                'skill_code': skill_data.get('skill_code', ''),
                'multiplier': multiplier,
                'count': count,
                'damage': round(damage, 2),
                'total': round(skill_total, 2)
            })
        
        dps = total_damage / time_seconds if time_seconds > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'panel_atk': round(panel_atk, 2),
                'crit_zone': round(crit_zone, 4),
                'element_dmg': round(element_dmg, 2),
                'skills': results,
                'total_damage': round(total_damage, 2),
                'dps': round(dps, 2),
                'time_seconds': time_seconds
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def calculate_panel_atk(character, config):
    """计算面板攻击"""
    base_atk = character.base_atk or 1024
    
    # 攻击百分比加成
    atk_pct = (
        config.get('weapon_atk_pct', 24.0) +
        config.get('echo_main_atk_pct', 33.0) +
        config.get('echo_sub_atk_pct', 25.8) +
        config.get('support_atk_pct', 61.5) +
        config.get('self_atk_pct', 0)
    )
    
    # 固定攻击
    fixed_atk = config.get('echo_fixed_atk', 350)
    
    return base_atk * (1 + atk_pct / 100) + fixed_atk


def calculate_crit_zone(character, config):
    """计算双爆区"""
    crit_rate = (
        character.inherent_crit_rate +
        config.get('weapon_crit_rate', 24.3) +
        config.get('echo_set_bonus', 20.0) +
        config.get('echo_main_crit_rate', 22.0) +
        config.get('echo_sub_crit_rate', 40.5) +
        config.get('support_crit_rate', 12.5) +
        config.get('self_crit_rate', 0)
    )
    
    crit_dmg = (
        character.inherent_crit_dmg +
        config.get('weapon_crit_dmg', 0) +
        config.get('echo_main_crit_dmg', 44.0) +
        config.get('echo_sub_crit_dmg', 81.0) +
        config.get('support_crit_dmg', 25.0) +
        config.get('self_crit_dmg', 0)
    )
    
    crit_rate = min(crit_rate / 100, 1.0)
    crit_dmg = crit_dmg / 100
    
    return 1 + crit_rate * crit_dmg


def calculate_element_dmg(config):
    """计算属伤加成"""
    return (
        config.get('echo_c3_element_dmg', 60.0) * config.get('echo_c3_count', 2) +
        config.get('echo_set_first_bonus', 22.0) +
        config.get('echo_set_bonus', 20.0) +
        config.get('self_element_dmg', 0) +
        config.get('support_element_dmg', 12.0)
    )


def calculate_amplify_zone(skill_type, config):
    """计算加深区"""
    total = config.get('support_all_amplify', 35.0)
    
    if skill_type == 'e':
        total += config.get('support_e_amplify', 25.0) + config.get('self_e_dmg', 49.0)
    elif skill_type == 'q':
        total += config.get('support_q_amplify', 32.0) + config.get('self_q_dmg', 55.0)
    elif skill_type == 'a':
        total += config.get('self_basic_dmg', 0)
    elif skill_type == 'h':
        total += config.get('self_heavy_dmg', 0)
    
    return total / 100


def calculate_defense_zone(config):
    """计算防御区"""
    monster_level = config.get('monster_level', 90)
    def_reduction = config.get('support_def_reduction', 0) / 100
    ignore_def = config.get('support_ignore_def', 0) / 100
    
    return 1520 / (1520 + (792 + 8 * monster_level) * (1 - def_reduction) * (1 - ignore_def))


def calculate_resistance_zone(config):
    """计算抗性区"""
    res_reduction = config.get('support_res_reduction', 0) / 100
    return 0.9 - res_reduction


@app.route('/api/import-data', methods=['POST'])
def import_data():
    """从Excel导入数据到数据库"""
    try:
        parser = MingchaoDataParser(DATA_FILE)
        
        # 导入角色基础数据
        characters_base = parser.parse_characters_base()
        for char_data in characters_base:
            char = Character.query.filter_by(name=char_data['name']).first()
            if not char:
                char = Character(
                    name=char_data['name'],
                    gender=char_data['gender'],
                    base_hp=char_data['base_hp'],
                    base_atk=char_data['base_atk'],
                    base_def=char_data['base_def']
                )
                db.session.add(char)
        
        db.session.commit()
        
        # 导入角色（合并基础属性和技能）
        characters = parser.parse_all_characters()
        for char_data in characters:
            char = Character.query.filter_by(name=char_data['name']).first()
            if not char:
                char = Character(
                    name=char_data['name'],
                    level=char_data.get('level', 90),
                    chain=char_data.get('chain', 0),
                    skill_level=char_data.get('skill_level', 10),
                    passive_level=char_data.get('passive_level', 2),
                    base_hp=char_data.get('base_hp', 0),
                    base_atk=char_data.get('base_atk', 0),
                    base_def=char_data.get('base_def', 0),
                    ult_energy=char_data.get('ult_energy', 125)
                )
                db.session.add(char)
                db.session.flush()
            
            # 添加技能
            for skill_data in char_data.get('skills', []):
                skill = CharacterSkill(
                    character_id=char.id,
                    skill_code=skill_data['skill_code'],
                    element=skill_data['element'],
                    settlement_type=skill_data['settlement_type'],
                    skill_type=skill_data['skill_type'],
                    damage_type=skill_data['damage_type'],
                    damage_subtype=skill_data['damage_subtype'],
                    multiplier_base=skill_data['multiplier_base'],
                    multiplier=skill_data['multiplier'],
                    ult_energy_cost=skill_data['ult_energy_cost'],
                    resonance_energy1=skill_data['resonance_energy1'],
                    resonance_energy2=skill_data['resonance_energy2']
                )
                db.session.add(skill)
        
        db.session.commit()
        
        # 导入声骸
        echoes = parser.parse_echoes()
        for echo_data in echoes:
            echo = Echo.query.filter_by(name=echo_data['name']).first()
            if not echo:
                echo = Echo(
                    name=echo_data['name'],
                    cost=echo_data.get('cost', 4)
                )
                db.session.add(echo)
                db.session.flush()
            
            # 声骸数据已简化，不再存储帧相关数据
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '数据导入成功',
            'characters': len(characters),
            'echoes': len(echoes)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/import-lalabiao', methods=['POST'])
def import_lalabiao():
    """导入拉表文件 - 支持文件上传"""
    tmp_path = None
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        file = request.files['file']
        sheet_name = request.form.get('sheet_name', None)
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400
        
        # 保存上传的文件到临时目录
        tmp_path = os.path.join(tempfile.gettempdir(), f'wuwa_calc_{os.getpid()}_{int(time.time())}.xlsx')
        file.save(tmp_path)
        
        # 解析Excel
        import pandas as pd
        xlsx = pd.ExcelFile(tmp_path, engine='openpyxl')
        
        # 如果没有指定sheet，使用第一个
        if sheet_name is None:
            sheet_name = xlsx.sheet_names[0]
        
        xlsx.close()
        
        # 使用解析器
        parser = LalabiaoParser(tmp_path)
        
        # 解析面板数据
        panel = parser.parse_character_panel(sheet_name)
        
        # 解析技能
        skills = parser.parse_skills(sheet_name)
        
        return jsonify({
            'success': True,
            'data': {
                'panel': panel,
                'skills': skills
            }
        })
        
    except Exception as e:
        import traceback
        print(f"导入错误: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        # 删除临时文件
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                print(f"删除临时文件失败: {e}")


@app.route('/api/character-skills/<character_name>')
def get_character_skills(character_name):
    """获取指定角色的技能列表"""
    try:
        parser = MingchaoDataParser(DATA_FILE)
        characters = parser.parse_all_characters()
        
        for char in characters:
            if char['name'] == character_name:
                return jsonify({
                    'success': True,
                    'data': char['skills']
                })
        
        return jsonify({'success': False, 'error': '角色不存在'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/all-character-skills')
def get_all_character_skills():
    """获取所有角色的技能列表"""
    try:
        parser = MingchaoDataParser(DATA_FILE)
        characters = parser.parse_all_characters()
        
        return jsonify({
            'success': True,
            'data': characters
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 初始化命令 ====================

@app.cli.command('init-db')
def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print('数据库初始化完成')


@app.cli.command('import-data')
def import_excel_data():
    """导入Excel数据"""
    with app.app_context():
        parser = MingchaoDataParser(DATA_FILE)
        
        # 导入角色
        characters = parser.parse_characters_base()
        for char_data in characters:
            char = Character.query.filter_by(name=char_data['name']).first()
            if not char:
                char = Character(**char_data)
                db.session.add(char)
        
        db.session.commit()
        print(f'导入 {len(characters)} 个角色')
        
        # 导入声骸
        echoes = parser.parse_echoes()
        for echo_data in echoes:
            echo = Echo.query.filter_by(name=echo_data['name']).first()
            if not echo:
                echo = Echo(name=echo_data['name'])
                db.session.add(echo)
        
        db.session.commit()
        print(f'导入 {len(echoes)} 个声骸')


def auto_import_data():
    """自动导入数据（如果数据库为空）"""
    with app.app_context():
        # 检查是否已有数据
        char_count = Character.query.count()
        if char_count > 0:
            print(f'数据库已有 {char_count} 个角色，跳过自动导入')
            return
        
        print('数据库为空，开始自动导入数据...')
        
        try:
            parser = MingchaoDataParser(DATA_FILE)
            
            # 导入角色和技能
            characters = parser.parse_all_characters()
            for char_data in characters:
                char = Character.query.filter_by(name=char_data['name']).first()
                if not char:
                    char = Character(name=char_data['name'])
                    db.session.add(char)
                    db.session.flush()
                
                # 添加技能
                for skill_data in char_data.get('skills', []):
                    skill = CharacterSkill(
                        character_id=char.id,
                        skill_code=skill_data['skill_code'],
                        element=skill_data['element'],
                        settlement_type=skill_data['settlement_type'],
                        skill_type=skill_data['skill_type'],
                        damage_type=skill_data['damage_type'],
                        damage_subtype=skill_data['damage_subtype'],
                        multiplier_base=skill_data['multiplier_base'],
                        multiplier=skill_data['multiplier'],
                        ult_energy_cost=skill_data['ult_energy_cost'],
                        resonance_energy1=skill_data['resonance_energy1'],
                        resonance_energy2=skill_data['resonance_energy2']
                    )
                    db.session.add(skill)
            
            db.session.commit()
            print(f'成功导入 {len(characters)} 个角色')
            
            # 导入声骸
            echoes = parser.parse_echoes()
            for echo_data in echoes:
                echo = Echo.query.filter_by(name=echo_data['name']).first()
                if not echo:
                    echo = Echo(name=echo_data['name'])
                    db.session.add(echo)
            
            db.session.commit()
            print(f'成功导入 {len(echoes)} 个声骸')
            
        except Exception as e:
            print(f'自动导入失败: {e}')
            db.session.rollback()


if __name__ == '__main__':
    # 确保数据库存在
    with app.app_context():
        db.create_all()
        
        # 自动导入数据
        auto_import_data()
    
    print('=' * 50)
    print('鸣潮DPS计算器 Web服务器')
    print('=' * 50)
    print('访问地址: http://localhost:5030')
    print('=' * 50)
    
    app.run(host='0.0.0.0', port=5030, debug=True)
