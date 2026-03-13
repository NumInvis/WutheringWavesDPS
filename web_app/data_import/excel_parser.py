# -*- coding: utf-8 -*-
"""
Excel数据解析器 - 读取鸣潮动作数据汇总
正确解析角色技能类型sheet数据结构
"""

import pandas as pd
from typing import List, Dict, Optional
import re


class MingchaoDataParser:
    """鸣潮动作数据汇总解析器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.xlsx = pd.ExcelFile(file_path)
    
    def get_sheet_names(self) -> List[str]:
        return self.xlsx.sheet_names
    
    def parse_all_characters(self) -> List[Dict]:
        """
        解析角色技能类型sheet
        数据结构：
        - 角色名行：只有第0列有值（如"椿"），其他列为空
        - 技能行：第0列是动作代码（如A1），后面是属性/倍率等数据
        """
        df = pd.read_excel(self.xlsx, sheet_name='角色技能类型', header=None)
        
        characters = []
        current_char = None
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # 获取第一列的值
            first_col_val = row.iloc[0] if pd.notna(row.iloc[0]) else None
            
            # 检查是否是角色名行（只有第一列有值，第二列为空）
            if first_col_val and not pd.notna(row.iloc[1]):
                char_name = str(first_col_val).strip()
                
                # 跳过表头行
                if char_name in ['角色/动作', '角色']:
                    continue
                
                # 新角色
                current_char = {
                    'name': char_name,
                    'skills': []
                }
                characters.append(current_char)
                continue
            
            # 检查是否是技能数据行（第一列是动作代码，第二列有属性值）
            if first_col_val and pd.notna(row.iloc[1]) and current_char:
                action_code = str(first_col_val).strip()
                
                # 跳过表头行
                if action_code in ['角色/动作', '角色']:
                    continue
                
                # 解析技能数据
                skill = self._parse_skill_row(row)
                if skill:
                    current_char['skills'].append(skill)
        
        return characters
    
    def _parse_skill_row(self, row) -> Optional[Dict]:
        """解析技能行数据"""
        try:
            skill_code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
            if not skill_code:
                return None
            
            # 读取倍率（列8）
            multiplier = 0.0
            if pd.notna(row.iloc[8]):
                val = row.iloc[8]
                if isinstance(val, str):
                    val = val.replace('%', '')
                try:
                    multiplier = float(val)
                    # 如果大于1，说明是百分比形式，转换为小数
                    if multiplier > 1:
                        multiplier = multiplier / 100
                except (ValueError, TypeError):
                    multiplier = 0.0
            
            skill = {
                'skill_code': skill_code,
                'element': str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else '',
                'settlement_type': str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else '',
                'skill_type': str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else '',
                'damage_type': str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else '',
                'damage_subtype': str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else '',
                'multiplier_base': str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else '',
                'multiplier': multiplier,
                'ult_energy_cost': float(row.iloc[9]) if pd.notna(row.iloc[9]) else 0,
                'resonance_energy1': float(row.iloc[10]) if pd.notna(row.iloc[10]) else 0,
                'resonance_energy2': float(row.iloc[11]) if pd.notna(row.iloc[11]) else 0,
            }
            return skill
        except Exception as e:
            return None
    
    def parse_echoes(self) -> List[Dict]:
        """解析声骸sheet"""
        df = pd.read_excel(self.xlsx, sheet_name='声骸', header=None)
        
        echoes = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            if pd.notna(row.iloc[0]):
                echo_name = str(row.iloc[0]).strip()
                if echo_name and echo_name != '声骸':
                    echoes.append({'name': echo_name})
        
        return echoes
    
    def parse_weapons(self) -> List[Dict]:
        """解析武器sheet"""
        weapons = []
        
        for sheet_name in self.xlsx.sheet_names:
            if '武器' in sheet_name:
                df = pd.read_excel(self.xlsx, sheet_name=sheet_name, header=None)
                
                for i in range(1, len(df)):
                    row = df.iloc[i]
                    if pd.notna(row.iloc[0]):
                        weapon = {
                            'name': str(row.iloc[0]).strip(),
                            'type': str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else '',
                            'base_atk': int(row.iloc[2]) if pd.notna(row.iloc[2]) else 500,
                            'sub_stat': str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else '',
                            'sub_stat_value': float(row.iloc[4]) if pd.notna(row.iloc[4]) else 0,
                        }
                        weapons.append(weapon)
        
        return weapons
    
    def parse_characters_base(self) -> List[Dict]:
        """解析角色基础属性（从角色技能类型sheet读取）"""
        df = pd.read_excel(self.xlsx, sheet_name='角色技能类型', header=None)
        
        characters = []
        current_char = None
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # 获取第一列的值
            first_col_val = row.iloc[0] if pd.notna(row.iloc[0]) else None
            
            # 检查是否是角色名行（只有第一列有值，第二列为空）
            if first_col_val and not pd.notna(row.iloc[1]):
                char_name = str(first_col_val).strip()
                
                # 跳过表头行
                if char_name in ['角色/动作', '角色']:
                    continue
                
                # 新角色
                current_char = {
                    'name': char_name,
                    'base_hp': 0,
                    'base_atk': 0,
                    'base_def': 0
                }
                characters.append(current_char)
        
        return characters


class LalabiaoParser:
    """拉表文件解析器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def _load_excel(self):
        """加载Excel文件 - 读取后关闭句柄"""
        return pd.ExcelFile(self.file_path, engine='openpyxl')
    
    def parse_character_panel(self, sheet_name: str) -> Optional[Dict]:
        """解析拉表中的角色面板数据"""
        xlsx = self._load_excel()
        try:
            df = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)
        finally:
            xlsx.close()
        
        panel = None
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            if pd.notna(row.iloc[1]) and str(row.iloc[1]).strip() == '角色主类型':
                panel = {
                    'skill_type': str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else 'e',
                    'c3_count': int(row.iloc[5]) if pd.notna(row.iloc[5]) else 2,
                    'name': '',
                    'attack': {},
                    'bonus': {},
                    'crit': {},
                    'crit_dmg': {},
                    'amplify': {},
                    'sub_stats': {}
                }
                
                if i + 1 < len(df):
                    name_row = df.iloc[i + 1]
                    if pd.notna(name_row.iloc[1]):
                        panel['name'] = str(name_row.iloc[1]).strip()
                
                data_start = i + 3
                for j in range(data_start, min(data_start + 8, len(df))):
                    data_row = df.iloc[j]
                    
                    if pd.notna(data_row.iloc[1]):
                        key = str(data_row.iloc[1]).strip()
                        if pd.notna(data_row.iloc[2]):
                            try:
                                val = float(data_row.iloc[2])
                                if val < 10:
                                    val = val * 100
                                panel['attack'][key] = val
                            except (ValueError, TypeError):
                                panel['attack'][key] = str(data_row.iloc[2])
                    
                    if pd.notna(data_row.iloc[3]):
                        key = str(data_row.iloc[3]).strip()
                        if pd.notna(data_row.iloc[4]):
                            try:
                                val = float(data_row.iloc[4])
                                if val < 10:
                                    val = val * 100
                                panel['bonus'][key] = val
                            except (ValueError, TypeError):
                                panel['bonus'][key] = str(data_row.iloc[4])
                    
                    if pd.notna(data_row.iloc[5]):
                        key = str(data_row.iloc[5]).strip()
                        if pd.notna(data_row.iloc[6]):
                            try:
                                val = float(data_row.iloc[6])
                                if val < 1:
                                    val = val * 100
                                panel['crit'][key] = val
                            except (ValueError, TypeError):
                                panel['crit'][key] = str(data_row.iloc[6])
                    
                    if pd.notna(data_row.iloc[7]):
                        key = str(data_row.iloc[7]).strip()
                        if pd.notna(data_row.iloc[8]):
                            try:
                                val = float(data_row.iloc[8])
                                if val < 2:
                                    val = val * 100
                                panel['crit_dmg'][key] = val
                            except (ValueError, TypeError):
                                panel['crit_dmg'][key] = str(data_row.iloc[8])
                    
                    if pd.notna(data_row.iloc[9]):
                        key = str(data_row.iloc[9]).strip()
                        if pd.notna(data_row.iloc[10]):
                            try:
                                val = float(data_row.iloc[10])
                                if val < 1:
                                    val = val * 100
                                panel['amplify'][key] = val
                            except (ValueError, TypeError):
                                panel['amplify'][key] = str(data_row.iloc[10])
                    
                    if pd.notna(data_row.iloc[11]):
                        key = str(data_row.iloc[11]).strip()
                        if pd.notna(data_row.iloc[12]):
                            try:
                                val = float(data_row.iloc[12])
                                if val < 1:
                                    val = val * 100
                                panel['sub_stats'][key] = val
                            except (ValueError, TypeError):
                                panel['sub_stats'][key] = str(data_row.iloc[12])
                
                break
        
        return panel
    
    def parse_skills(self, sheet_name: str) -> List[Dict]:
        """解析拉表中的技能列表"""
        xlsx = self._load_excel()
        try:
            df = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)
        finally:
            xlsx.close()
        
        skills = []
        data_started = False
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            if not data_started:
                if pd.notna(row.iloc[14]) and '次数' in str(row.iloc[14]):
                    data_started = True
                continue
            
            if pd.notna(row.iloc[1]):
                skill = {
                    'name': str(row.iloc[1]).strip(),
                    'multiplier': float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0,
                    'count': int(row.iloc[14]) if pd.notna(row.iloc[14]) else 1,
                    'skill_type': str(row.iloc[17]).strip() if pd.notna(row.iloc[17]) else 'e',
                    'echo': int(row.iloc[29]) if pd.notna(row.iloc[29]) else 17,
                    'overflow': int(row.iloc[30]) if pd.notna(row.iloc[30]) else 0,
                }
                skills.append(skill)
        
        return skills
