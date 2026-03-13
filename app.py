# -*- coding: utf-8 -*-
"""
鸣潮DPS计算器 - Web版本 (Flask后端)
"""

from flask import Flask, render_template, jsonify, request
from typing import List, Dict, Optional, Any
import pandas as pd
from dataclasses import dataclass, field, asdict
from pathlib import Path
import copy
import re
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# ==================== Excel引擎 ====================

class CellRef:
    """单元格引用 A1, B2"""
    
    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row
    
    @classmethod
    def from_string(cls, ref: str) -> 'CellRef':
        ref = ref.upper().strip()
        match = re.match(r'([A-Z]+)(\d+)', ref)
        if not match:
            raise ValueError(f"无效的单元格引用: {ref}")
        
        col_str, row_str = match.groups()
        col = 0
        for char in col_str:
            col = col * 26 + (ord(char) - ord('A') + 1)
        col -= 1
        row = int(row_str) - 1
        
        return cls(col, row)
    
    def to_string(self) -> str:
        col = self.col
        col_str = ""
        while col >= 0:
            col_str = chr(col % 26 + ord('A')) + col_str
            col = col // 26 - 1
        return f"{col_str}{self.row + 1}"


class Spreadsheet:
    """电子表格引擎"""
    
    def __init__(self):
        self.cells: Dict[str, Any] = {}
    
    def set(self, ref: str, value: Any):
        self.cells[ref.upper()] = value
    
    def get(self, ref: str) -> Any:
        return self.cells.get(ref.upper(), 0)
    
    def eval_formula(self, formula: str) -> Any:
        if not formula.startswith('='):
            return formula
        
        formula = formula[1:]
        
        def replace_ref(match):
            ref = match.group(1) + match.group(2)
            return str(self.get(ref))
        
        formula = re.sub(r'\$?([A-Z]+)\$?(\d+)', replace_ref, formula)
        
        def replace_sum(match):
            range_str = match.group(1)
            if ':' in range_str:
                start, end = range_str.split(':')
                start_ref = CellRef.from_string(start)
                end_ref = CellRef.from_string(end)
                total = 0
                for row in range(start_ref.row, end_ref.row + 1):
                    for col in range(start_ref.col, end_ref.col + 1):
                        ref = CellRef(col, row).to_string()
                        val = self.get(ref)
                        if isinstance(val, (int, float)):
                            total += val
                return str(total)
            return "0"
        
        formula = re.sub(r'SUM\s*\(\s*([^)]+)\s*\)', replace_sum, formula, flags=re.IGNORECASE)
        
        try:
            return eval(formula)
        except:
            return "#ERROR"


# ==================== 角色面板数据模型 ====================

@dataclass
class EchoConfig:
    """声骸配置"""
    c3_element_dmg: float = 60.0
    c3_count: int = 2
    set_name: str = "新暗套"
    set_first_bonus: float = 22.0
    set_bonus: float = 20.0
    main_atk_pct: float = 33.0
    main_crit_rate: float = 22.0
    main_crit_dmg: float = 44.0
    sub_atk_pct: float = 25.8
    sub_skill_dmg: float = 17.2
    sub_crit_rate: float = 40.5
    sub_crit_dmg: float = 81.0
    fixed_atk: float = 350.0


@dataclass
class WeaponConfig:
    """武器配置"""
    name: str = "裁春"
    base_atk: float = 500.0
    atk_pct: float = 24.0
    crit_rate: float = 24.3
    crit_dmg: float = 0.0
    skill_dmg: float = 0.0
    passive: str = ""


@dataclass
class InherentConfig:
    """固有技能配置"""
    inherent_crit_rate: float = 13.0
    inherent_crit_dmg: float = 150.0
    chain_crit_rate: float = 0.0
    chain_crit_dmg: float = 0.0
    chain_skill_dmg: float = 0.0


@dataclass
class SelfBuffConfig:
    """自拐配置"""
    self_atk_pct: float = 0.0
    self_element_dmg: float = 0.0
    self_e_dmg: float = 49.0
    self_q_dmg: float = 55.0
    self_basic_dmg: float = 0.0
    self_heavy_dmg: float = 0.0
    self_crit_rate: float = 0.0
    self_crit_dmg: float = 0.0


@dataclass
class SupportConfig:
    """队友拐力配置"""
    support_atk_pct: float = 61.5
    support_fixed_atk: float = 0.0
    support_element_dmg: float = 12.0
    support_all_amplify: float = 35.0
    support_e_amplify: float = 25.0
    support_q_amplify: float = 32.0
    support_crit_rate: float = 12.5
    support_crit_dmg: float = 25.0
    support_res_reduction: float = 0.0
    support_def_reduction: float = 0.0
    support_ignore_def: float = 0.0


@dataclass
class CharacterPanel:
    """完整角色面板"""
    name: str = "弗洛洛"
    element: str = "湮灭"
    skill_type: str = "e"
    base_atk: float = 1024.0
    echo: EchoConfig = field(default_factory=EchoConfig)
    weapon: WeaponConfig = field(default_factory=WeaponConfig)
    inherent: InherentConfig = field(default_factory=InherentConfig)
    self_buff: SelfBuffConfig = field(default_factory=SelfBuffConfig)
    support: SupportConfig = field(default_factory=SupportConfig)
    
    def get_total_atk_pct(self) -> float:
        return (self.weapon.atk_pct + self.echo.main_atk_pct + 
                self.echo.sub_atk_pct + self.support.support_atk_pct + 
                self.self_buff.self_atk_pct)
    
    def get_total_fixed_atk(self) -> float:
        return self.echo.fixed_atk + self.support.support_fixed_atk
    
    def get_panel_atk(self) -> float:
        return self.base_atk * (1 + self.get_total_atk_pct() / 100) + self.get_total_fixed_atk()
    
    def get_total_element_dmg(self) -> float:
        return (self.echo.c3_element_dmg * self.echo.c3_count + 
                self.echo.set_first_bonus + self.echo.set_bonus +
                self.self_buff.self_element_dmg + self.support.support_element_dmg)
    
    def get_panel_crit_rate(self) -> float:
        return (self.inherent.inherent_crit_rate + self.weapon.crit_rate + 
                self.echo.set_bonus + self.echo.main_crit_rate + 
                self.echo.sub_crit_rate + self.support.support_crit_rate +
                self.self_buff.self_crit_rate)
    
    def get_panel_crit_dmg(self) -> float:
        return (self.inherent.inherent_crit_dmg + self.weapon.crit_dmg + 
                self.echo.main_crit_dmg + self.echo.sub_crit_dmg + 
                self.support.support_crit_dmg + self.inherent.chain_crit_dmg +
                self.self_buff.self_crit_dmg)
    
    def get_crit_zone(self) -> float:
        crit_rate = min(self.get_panel_crit_rate() / 100, 1.0)
        crit_dmg = self.get_panel_crit_dmg() / 100
        return 1 + crit_rate * crit_dmg
    
    def get_amplify_zone(self, skill_type: str = "e") -> float:
        total = self.support.support_all_amplify
        if skill_type == "e":
            total += self.support.support_e_amplify + self.self_buff.self_e_dmg
        elif skill_type == "q":
            total += self.support.support_q_amplify + self.self_buff.self_q_dmg
        elif skill_type == "a":
            total += self.self_buff.self_basic_dmg
        elif skill_type == "h":
            total += self.self_buff.self_heavy_dmg
        return total / 100
    
    def get_defense_zone(self, monster_level: int = 90) -> float:
        def_reduction = self.support.support_def_reduction / 100
        ignore_def = self.support.support_ignore_def / 100
        return 1520 / (1520 + (792 + 8 * monster_level) * (1 - def_reduction) * (1 - ignore_def))
    
    def get_resistance_zone(self) -> float:
        res_reduction = self.support.support_res_reduction / 100
        return 0.9 - res_reduction


@dataclass
class Skill:
    """动作数据"""
    name: str = "新动作"
    skill_type: str = "e"
    count: int = 1
    multiplier: float = 0
    use_panel: bool = True
    atk_zone: float = 1.0
    bonus_zone: float = 1.0
    crit_zone: float = 1.0
    amplify_zone: float = 0
    defense_zone: float = 0.5
    resistance_zone: float = 0.8
    multiplier_boost: float = 0
    vulnerable_zone: float = 0
    independent_zone: float = 1.0
    echo: int = 17
    overflow: int = 0
    damage: float = 0
    total_damage: float = 0
    
    def calculate(self, panel: CharacterPanel = None) -> float:
        if self.use_panel and panel:
            panel_atk = panel.get_panel_atk()
            bonus = 1 + panel.get_total_element_dmg() / 100
            crit_z = panel.get_crit_zone()
            amplify = panel.get_amplify_zone(self.skill_type)
            defense = panel.get_defense_zone()
            resistance = panel.get_resistance_zone()
        else:
            panel_atk = 1000
            bonus = self.bonus_zone
            crit_z = self.crit_zone
            amplify = self.amplify_zone
            defense = self.defense_zone
            resistance = self.resistance_zone
        
        self.damage = (
            panel_atk *
            (self.multiplier / 100) *
            self.atk_zone *
            bonus *
            crit_z *
            (1 + amplify) *
            defense *
            resistance *
            (1 + self.multiplier_boost) *
            (1 + self.vulnerable_zone) *
            self.independent_zone
        )
        self.total_damage = self.damage * self.count
        return self.damage


@dataclass
class Character:
    """角色"""
    name: str = "新角色"
    panel: CharacterPanel = field(default_factory=CharacterPanel)
    skills: List[Skill] = field(default_factory=list)
    
    def add_skill(self, skill: Skill = None) -> Skill:
        if skill is None:
            skill = Skill(name=f"动作{len(self.skills)+1}")
        self.skills.append(skill)
        return skill
    
    def remove_skills(self, indices: List[int]):
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.skills):
                del self.skills[idx]
    
    def get_total_damage(self) -> float:
        return sum(s.total_damage for s in self.skills)
    
    def recalculate_all(self):
        for skill in self.skills:
            skill.calculate(self.panel)


@dataclass
class Team:
    """队伍"""
    name: str = ""
    characters: List[Character] = field(default_factory=list)
    time_seconds: float = 25.0
    monster_level: int = 90
    
    def add_character(self, char: Character = None) -> Character:
        if char is None:
            char = Character(name=f"角色{len(self.characters)+1}")
        self.characters.append(char)
        return char
    
    def get_team_damage(self) -> float:
        return sum(c.get_total_damage() for c in self.characters)
    
    def get_team_dps(self) -> float:
        return self.get_team_damage() / self.time_seconds if self.time_seconds > 0 else 0


# ==================== Excel处理器 ====================

class ExcelHandler:
    """Excel处理器 - 适配爱弥斯/弗洛洛拉表格式"""
    
    def load(self, file_path: str, sheet_name: str = None) -> Team:
        xlsx = pd.ExcelFile(file_path)
        
        if sheet_name is None:
            sheet_name = xlsx.sheet_names[0]
        
        df = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)
        
        team = Team(name=Path(file_path).stem)
        
        # 查找所有角色分块
        char_starts = []
        for i in range(len(df)):
            row = df.iloc[i]
            for j, val in enumerate(row):
                if pd.notna(val) and str(val).strip() == "角色主类型":
                    char_starts.append(i)
                    break
        
        for start_row in char_starts:
            char = self._parse_character(df, start_row)
            if char and char.skills:
                team.characters.append(char)
        
        return team
    
    def _parse_character(self, df: pd.DataFrame, start_row: int) -> Optional[Character]:
        try:
            # 行0: 角色主类型 | 类型值 | 3C属伤数 | 数量
            # 行1: 角色名
            char_name = ""
            if start_row + 1 < len(df):
                name_val = df.iloc[start_row + 1, 1]
                if pd.notna(name_val):
                    char_name = str(name_val).strip()
            
            if not char_name:
                return None
            
            char = Character(name=char_name)
            panel = char.panel
            
            # 读取角色主类型 (行0, 列2)
            if start_row < len(df):
                row0 = df.iloc[start_row]
                if len(row0) > 2 and pd.notna(row0.iloc[2]):
                    panel.skill_type = str(row0.iloc[2]).strip()
                # 读取3C属伤数 (行0, 列4)
                if len(row0) > 4 and pd.notna(row0.iloc[4]):
                    try:
                        panel.echo.c3_count = int(float(row0.iloc[4]))
                    except:
                        pass
            
            # 读取面板数据 (行2-9)
            # 行2: 攻击 | NaN | 加成区 | NaN | 暴击 | NaN | 暴击伤害 | NaN | 加深区 | NaN | 副词条
            # 行3: 白值 | 数值 | 3C声骸 | 数值 | 基础与固有 | 数值 | 基础与固有 | 数值 | 全加深 | 数值 | 大攻击 | 数值
            # 行4: 固有武器 | 数值 | 套装首位 | 数值 | 武器 | 数值 | 武器 | 数值 | e加深 | 数值 | r伤害/共技伤害 | 数值
            # 行5: 主副词条 | 数值 | 自拐属伤 | 数值 | 套装 | 数值 | 套装 | 数值 | q加深 | 数值 | 暴击 | 数值
            # 行6: 自拐攻击 | 数值 | 被拐属伤 | 数值 | 主副词条 | 数值 | 主副词条 | 数值 | ... | 爆伤 | 数值
            # 行7: 被拐攻击 | 数值 | 其他属伤 | 数值 | 共鸣链 | 数值 | 共鸣链 | 数值
            # 行8: 声骸固定攻击 | 数值 | e加成 | 数值 | 队友 | 数值 | 队友 | 数值
            # 行9: 额外固定攻击 | NaN | q加成 | 数值 | 面板暴击率 | 数值 | 面板暴击伤害 | 数值
            
            try:
                # 行3: 白值, 3C声骸(属伤%), 基础与固有(暴击), 基础与固有(爆伤), 全加深, 大攻击
                if start_row + 3 < len(df):
                    row = df.iloc[start_row + 3]
                    if len(row) > 2 and pd.notna(row.iloc[2]):
                        panel.base_atk = self._parse_float(row.iloc[2])
                    if len(row) > 4 and pd.notna(row.iloc[4]):
                        panel.echo.c3_element_dmg = self._parse_percent(row.iloc[4])
                    if len(row) > 6 and pd.notna(row.iloc[6]):
                        panel.inherent.inherent_crit_rate = self._parse_percent(row.iloc[6])
                    if len(row) > 8 and pd.notna(row.iloc[8]):
                        panel.inherent.inherent_crit_dmg = self._parse_percent(row.iloc[8])
                    if len(row) > 10 and pd.notna(row.iloc[10]):
                        panel.support.support_all_amplify = self._parse_percent(row.iloc[10])
                    if len(row) > 12 and pd.notna(row.iloc[12]):
                        panel.echo.sub_atk_pct = self._parse_percent(row.iloc[12])
                
                # 行4: 固有武器(攻击%), 套装首位, 武器(暴击率), e加深, 共技伤害
                if start_row + 4 < len(df):
                    row = df.iloc[start_row + 4]
                    if len(row) > 2 and pd.notna(row.iloc[2]):
                        panel.weapon.atk_pct = self._parse_percent(row.iloc[2])
                    if len(row) > 4 and pd.notna(row.iloc[4]):
                        panel.echo.set_first_bonus = self._parse_percent(row.iloc[4])
                    if len(row) > 6 and pd.notna(row.iloc[6]):
                        panel.weapon.crit_rate = self._parse_percent(row.iloc[6])
                    if len(row) > 10 and pd.notna(row.iloc[10]):
                        panel.support.support_e_amplify = self._parse_percent(row.iloc[10])
                    if len(row) > 12 and pd.notna(row.iloc[12]):
                        panel.echo.sub_skill_dmg = self._parse_percent(row.iloc[12])
                
                # 行5: 主副词条(攻击%), 自拐属伤, 套装(暴击), q加深, 暴击
                if start_row + 5 < len(df):
                    row = df.iloc[start_row + 5]
                    if len(row) > 2 and pd.notna(row.iloc[2]):
                        panel.echo.main_atk_pct = self._parse_percent(row.iloc[2])
                    if len(row) > 4 and pd.notna(row.iloc[4]):
                        panel.self_buff.self_element_dmg = self._parse_percent(row.iloc[4])
                    if len(row) > 6 and pd.notna(row.iloc[6]):
                        val = self._parse_percent(row.iloc[6])
                        # 可能是套装加成或共鸣链
                        if val < 50:  # 假设小于50%是套装加成
                            panel.echo.set_bonus = val
                    if len(row) > 10 and pd.notna(row.iloc[10]):
                        panel.support.support_q_amplify = self._parse_percent(row.iloc[10])
                    if len(row) > 12 and pd.notna(row.iloc[12]):
                        panel.echo.sub_crit_rate = self._parse_percent(row.iloc[12])
                
                # 行6: 自拐攻击, 被拐属伤, 主副词条(暴击), 主副词条(爆伤)
                if start_row + 6 < len(df):
                    row = df.iloc[start_row + 6]
                    if len(row) > 2 and pd.notna(row.iloc[2]):
                        panel.self_buff.self_atk_pct = self._parse_percent(row.iloc[2])
                    if len(row) > 4 and pd.notna(row.iloc[4]):
                        panel.support.support_element_dmg = self._parse_percent(row.iloc[4])
                    if len(row) > 6 and pd.notna(row.iloc[6]):
                        panel.inherent.chain_crit_rate = self._parse_percent(row.iloc[6])
                    if len(row) > 12 and pd.notna(row.iloc[12]):
                        panel.echo.sub_crit_dmg = self._parse_percent(row.iloc[12])
                
                # 行7: 被拐攻击, 其他属伤, 共鸣链
                if start_row + 7 < len(df):
                    row = df.iloc[start_row + 7]
                    if len(row) > 2 and pd.notna(row.iloc[2]):
                        panel.support.support_atk_pct = self._parse_percent(row.iloc[2])
                    if len(row) > 6 and pd.notna(row.iloc[6]):
                        panel.inherent.chain_crit_dmg = self._parse_percent(row.iloc[6])
                    if len(row) > 8 and pd.notna(row.iloc[8]):
                        panel.support.support_crit_dmg = self._parse_percent(row.iloc[8])
                
                # 行8: 声骸固定攻击, e加成, 队友(暴击拐)
                if start_row + 8 < len(df):
                    row = df.iloc[start_row + 8]
                    if len(row) > 2 and pd.notna(row.iloc[2]):
                        panel.echo.fixed_atk = self._parse_float(row.iloc[2])
                    if len(row) > 4 and pd.notna(row.iloc[4]):
                        panel.self_buff.self_e_dmg = self._parse_percent(row.iloc[4])
                    if len(row) > 6 and pd.notna(row.iloc[6]):
                        panel.support.support_crit_rate = self._parse_percent(row.iloc[6])
                
                # 行9: 额外固定攻击, q加成, 面板暴击率, 面板暴击伤害
                if start_row + 9 < len(df):
                    row = df.iloc[start_row + 9]
                    if len(row) > 4 and pd.notna(row.iloc[4]):
                        panel.self_buff.self_q_dmg = self._parse_percent(row.iloc[4])
                
            except Exception as e:
                print(f"读取面板数据警告: {e}")
            
            # 读取动作列表 - 从行2开始（与面板数据同行）
            # 动作列表列: 14=次数, 15=动作, 16=倍率, 17=类型, 18=面板攻击, 19=攻击区, 20=加成区, 
            # 21=双爆区, 22=加深区, 23=防御区, 24=抗性区, 25=倍率提升, 26=易伤区, 27=独立乘区, 28=伤害
            # 29=余响/无视防御, 30=溢出/减防, 31=防御区, 32=怪物等级
            
            skill_start = start_row + 2  # 动作数据从行2开始
            for i in range(skill_start, len(df)):
                try:
                    row = df.iloc[i]
                    
                    # 检查是否是新角色开始
                    if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == "角色主类型":
                        break
                    
                    # 检查是否是动作行 - 需要有序号(列14)和动作名(列15)
                    if len(row) <= 15:
                        continue
                    
                    count_val = row.iloc[14]
                    name_val = row.iloc[15] if len(row) > 15 else None
                    
                    # 跳过无效行
                    if pd.isna(count_val) and pd.isna(name_val):
                        continue
                    
                    if pd.isna(name_val) or str(name_val).strip() == "":
                        continue
                    
                    # 跳过标题行
                    if str(name_val).strip() in ["动作", "次数", "角色主类型"]:
                        continue
                    
                    skill = Skill()
                    skill.name = str(name_val).strip()
                    
                    # 次数 (列14)
                    if pd.notna(count_val):
                        try:
                            skill.count = int(float(count_val))
                        except:
                            skill.count = 1
                    
                    # 倍率 (列16) - 原样读取，如596.43表示596.43%
                    if len(row) > 16 and pd.notna(row.iloc[16]):
                        skill.multiplier = self._parse_float(row.iloc[16])
                    
                    # 类型 (列17)
                    if len(row) > 17 and pd.notna(row.iloc[17]):
                        skill.skill_type = str(row.iloc[17]).strip()
                    
                    # 读取各乘区（如果存在）
                    if len(row) > 18 and pd.notna(row.iloc[18]):
                        skill.panel_atk_input = self._parse_float(row.iloc[18])
                    if len(row) > 19 and pd.notna(row.iloc[19]):
                        skill.atk_zone = self._parse_float(row.iloc[19])
                    if len(row) > 20 and pd.notna(row.iloc[20]):
                        skill.bonus_zone = self._parse_float(row.iloc[20])
                    if len(row) > 21 and pd.notna(row.iloc[21]):
                        skill.crit_zone = self._parse_float(row.iloc[21])
                    if len(row) > 22 and pd.notna(row.iloc[22]):
                        skill.amplify_zone = self._parse_float(row.iloc[22])
                    if len(row) > 23 and pd.notna(row.iloc[23]):
                        skill.defense_zone = self._parse_float(row.iloc[23])
                    if len(row) > 24 and pd.notna(row.iloc[24]):
                        skill.resistance_zone = self._parse_float(row.iloc[24])
                    
                    # 伤害 (列28)
                    if len(row) > 28 and pd.notna(row.iloc[28]):
                        skill.damage = self._parse_float(row.iloc[28])
                        skill.total_damage = skill.damage * skill.count
                    
                    # 余响/无视防御 (列29)
                    if len(row) > 29 and pd.notna(row.iloc[29]):
                        val = row.iloc[29]
                        # 如果是数值，可能是余响(弗洛洛)或无视防御
                        try:
                            float_val = float(val)
                            if float_val < 100:  # 小于100认为是余响层数
                                skill.echo = int(float_val)
                            else:
                                skill.overflow = int(float_val)
                        except:
                            pass
                    
                    # 溢出/减防 (列30)
                    if len(row) > 30 and pd.notna(row.iloc[30]):
                        val = row.iloc[30]
                        try:
                            skill.overflow = int(float(val))
                        except:
                            pass
                    
                    skill.use_panel = True
                    
                    # 如果没有预计算的伤害，则计算
                    if skill.damage == 0:
                        skill.calculate(panel)
                    
                    char.skills.append(skill)
                    
                except Exception as e:
                    continue
            
            return char
            
        except Exception as e:
            print(f"解析角色失败: {e}")
            return None
    
    def _parse_float(self, val) -> float:
        """解析浮点数"""
        if pd.isna(val):
            return 0.0
        if isinstance(val, str):
            val = val.replace('%', '').replace('％', '').strip()
            if val == '' or val == 'NaN':
                return 0.0
        try:
            return float(val)
        except:
            return 0.0
    
    def _parse_percent(self, val) -> float:
        """解析百分比值，返回百分比数值（如12.5表示12.5%）"""
        if pd.isna(val):
            return 0.0
        if isinstance(val, str):
            val = val.replace('%', '').replace('％', '').strip()
            if val == '' or val == 'NaN':
                return 0.0
        try:
            fval = float(val)
            # Excel存储的百分比可能是小数形式（如0.125表示12.5%）
            # 或者是百分比形式（如12.5表示12.5%）
            # 如果值小于1，假设是小数形式，转换为百分比
            if fval < 1 and fval > 0:
                fval = fval * 100
            return fval
        except:
            return 0.0
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        xlsx = pd.ExcelFile(file_path)
        return xlsx.sheet_names


# ==================== 全局数据存储 ====================
# 使用简单的内存存储，实际生产环境应该使用数据库
session_data = {
    'team': None,
    'current_char_idx': 0
}

def get_default_team():
    """获取默认队伍"""
    team = Team(name="新队伍")
    char = Character(name="弗洛洛")
    team.characters.append(char)
    return team


def team_to_dict(team: Team) -> dict:
    """将队伍转换为字典"""
    return {
        'name': team.name,
        'time_seconds': team.time_seconds,
        'monster_level': team.monster_level,
        'team_damage': team.get_team_damage(),
        'team_dps': team.get_team_dps(),
        'characters': [character_to_dict(c) for c in team.characters]
    }


def character_to_dict(char: Character) -> dict:
    """将角色转换为字典"""
    panel = char.panel
    return {
        'name': char.name,
        'total_damage': char.get_total_damage(),
        'panel': {
            'name': panel.name,
            'element': panel.element,
            'skill_type': panel.skill_type,
            'base_atk': panel.base_atk,
            'panel_atk': panel.get_panel_atk(),
            'panel_crit_rate': panel.get_panel_crit_rate(),
            'panel_crit_dmg': panel.get_panel_crit_dmg(),
            'element_dmg': panel.get_total_element_dmg(),
            'crit_zone': panel.get_crit_zone(),
            'defense_zone': panel.get_defense_zone(),
            'resistance_zone': panel.get_resistance_zone(),
            'echo': {
                'c3_element_dmg': panel.echo.c3_element_dmg,
                'c3_count': panel.echo.c3_count,
                'set_name': panel.echo.set_name,
                'set_first_bonus': panel.echo.set_first_bonus,
                'set_bonus': panel.echo.set_bonus,
                'main_atk_pct': panel.echo.main_atk_pct,
                'main_crit_rate': panel.echo.main_crit_rate,
                'main_crit_dmg': panel.echo.main_crit_dmg,
                'sub_atk_pct': panel.echo.sub_atk_pct,
                'sub_skill_dmg': panel.echo.sub_skill_dmg,
                'sub_crit_rate': panel.echo.sub_crit_rate,
                'sub_crit_dmg': panel.echo.sub_crit_dmg,
                'fixed_atk': panel.echo.fixed_atk,
            },
            'weapon': {
                'name': panel.weapon.name,
                'base_atk': panel.weapon.base_atk,
                'atk_pct': panel.weapon.atk_pct,
                'crit_rate': panel.weapon.crit_rate,
                'crit_dmg': panel.weapon.crit_dmg,
                'skill_dmg': panel.weapon.skill_dmg,
            },
            'inherent': {
                'inherent_crit_rate': panel.inherent.inherent_crit_rate,
                'inherent_crit_dmg': panel.inherent.inherent_crit_dmg,
                'chain_crit_rate': panel.inherent.chain_crit_rate,
                'chain_crit_dmg': panel.inherent.chain_crit_dmg,
            },
            'self_buff': {
                'self_atk_pct': panel.self_buff.self_atk_pct,
                'self_element_dmg': panel.self_buff.self_element_dmg,
                'self_e_dmg': panel.self_buff.self_e_dmg,
                'self_q_dmg': panel.self_buff.self_q_dmg,
                'self_basic_dmg': panel.self_buff.self_basic_dmg,
                'self_heavy_dmg': panel.self_buff.self_heavy_dmg,
            },
            'support': {
                'support_atk_pct': panel.support.support_atk_pct,
                'support_element_dmg': panel.support.support_element_dmg,
                'support_all_amplify': panel.support.support_all_amplify,
                'support_e_amplify': panel.support.support_e_amplify,
                'support_q_amplify': panel.support.support_q_amplify,
                'support_crit_rate': panel.support.support_crit_rate,
                'support_crit_dmg': panel.support.support_crit_dmg,
                'support_res_reduction': panel.support.support_res_reduction,
                'support_def_reduction': panel.support.support_def_reduction,
                'support_ignore_def': panel.support.support_ignore_def,
            }
        },
        'skills': [skill_to_dict(s) for s in char.skills]
    }


def skill_to_dict(skill: Skill) -> dict:
    """将技能转换为字典"""
    return {
        'name': skill.name,
        'skill_type': skill.skill_type,
        'count': skill.count,
        'multiplier': skill.multiplier,
        'echo': skill.echo,
        'overflow': skill.overflow,
        'damage': skill.damage,
        'total_damage': skill.total_damage,
    }


# ==================== Flask路由 ====================

@app.route('/')
def index():
    """主页"""
    if session_data['team'] is None:
        session_data['team'] = get_default_team()
    return render_template('index.html')


@app.route('/api/team', methods=['GET'])
def get_team():
    """获取队伍数据"""
    if session_data['team'] is None:
        session_data['team'] = get_default_team()
    return jsonify(team_to_dict(session_data['team']))


@app.route('/api/team/time', methods=['POST'])
def update_time():
    """更新战斗时间"""
    data = request.json
    if session_data['team']:
        session_data['team'].time_seconds = data.get('time_seconds', 25.0)
    return jsonify(team_to_dict(session_data['team']))


@app.route('/api/character/<int:char_idx>', methods=['GET'])
def get_character(char_idx):
    """获取角色数据"""
    if session_data['team'] and 0 <= char_idx < len(session_data['team'].characters):
        return jsonify(character_to_dict(session_data['team'].characters[char_idx]))
    return jsonify({'error': 'Character not found'}), 404


@app.route('/api/character/<int:char_idx>/panel', methods=['POST'])
def update_panel(char_idx):
    """更新角色面板"""
    if not session_data['team'] or not (0 <= char_idx < len(session_data['team'].characters)):
        return jsonify({'error': 'Character not found'}), 404
    
    data = request.json
    char = session_data['team'].characters[char_idx]
    panel = char.panel
    
    # 更新基础信息
    if 'name' in data:
        char.name = data['name']
    if 'element' in data:
        panel.element = data['element']
    if 'skill_type' in data:
        panel.skill_type = data['skill_type']
    if 'base_atk' in data:
        panel.base_atk = float(data['base_atk'])
    
    # 更新声骸
    if 'echo' in data:
        echo_data = data['echo']
        if 'c3_element_dmg' in echo_data:
            panel.echo.c3_element_dmg = float(echo_data['c3_element_dmg'])
        if 'c3_count' in echo_data:
            panel.echo.c3_count = int(echo_data['c3_count'])
        if 'set_bonus' in echo_data:
            panel.echo.set_bonus = float(echo_data['set_bonus'])
        if 'main_atk_pct' in echo_data:
            panel.echo.main_atk_pct = float(echo_data['main_atk_pct'])
        if 'fixed_atk' in echo_data:
            panel.echo.fixed_atk = float(echo_data['fixed_atk'])
    
    # 更新武器
    if 'weapon' in data:
        weapon_data = data['weapon']
        if 'name' in weapon_data:
            panel.weapon.name = weapon_data['name']
        if 'atk_pct' in weapon_data:
            panel.weapon.atk_pct = float(weapon_data['atk_pct'])
        if 'crit_rate' in weapon_data:
            panel.weapon.crit_rate = float(weapon_data['crit_rate'])
    
    # 更新拐力
    if 'support' in data:
        support_data = data['support']
        if 'support_atk_pct' in support_data:
            panel.support.support_atk_pct = float(support_data['support_atk_pct'])
        if 'support_element_dmg' in support_data:
            panel.support.support_element_dmg = float(support_data['support_element_dmg'])
        if 'support_all_amplify' in support_data:
            panel.support.support_all_amplify = float(support_data['support_all_amplify'])
        if 'support_e_amplify' in support_data:
            panel.support.support_e_amplify = float(support_data['support_e_amplify'])
        if 'support_q_amplify' in support_data:
            panel.support.support_q_amplify = float(support_data['support_q_amplify'])
        if 'support_crit_rate' in support_data:
            panel.support.support_crit_rate = float(support_data['support_crit_rate'])
        if 'support_crit_dmg' in support_data:
            panel.support.support_crit_dmg = float(support_data['support_crit_dmg'])
    
    # 重新计算所有技能
    char.recalculate_all()
    
    return jsonify(character_to_dict(char))


@app.route('/api/character/<int:char_idx>/skills', methods=['POST'])
def add_skill(char_idx):
    """添加技能"""
    if not session_data['team'] or not (0 <= char_idx < len(session_data['team'].characters)):
        return jsonify({'error': 'Character not found'}), 404
    
    char = session_data['team'].characters[char_idx]
    skill = char.add_skill()
    skill.use_panel = True
    skill.calculate(char.panel)
    
    return jsonify(skill_to_dict(skill))


@app.route('/api/character/<int:char_idx>/skills/<int:skill_idx>', methods=['PUT'])
def update_skill(char_idx, skill_idx):
    """更新技能"""
    if not session_data['team'] or not (0 <= char_idx < len(session_data['team'].characters)):
        return jsonify({'error': 'Character not found'}), 404
    
    char = session_data['team'].characters[char_idx]
    if not (0 <= skill_idx < len(char.skills)):
        return jsonify({'error': 'Skill not found'}), 404
    
    data = request.json
    skill = char.skills[skill_idx]
    
    if 'name' in data:
        skill.name = data['name']
    if 'skill_type' in data:
        skill.skill_type = data['skill_type']
    if 'count' in data:
        skill.count = int(data['count'])
    if 'multiplier' in data:
        skill.multiplier = float(data['multiplier'])
    if 'echo' in data:
        skill.echo = int(data['echo'])
    if 'overflow' in data:
        skill.overflow = int(data['overflow'])
    
    skill.calculate(char.panel)
    
    return jsonify(skill_to_dict(skill))


@app.route('/api/character/<int:char_idx>/skills/<int:skill_idx>', methods=['DELETE'])
def delete_skill(char_idx, skill_idx):
    """删除技能"""
    if not session_data['team'] or not (0 <= char_idx < len(session_data['team'].characters)):
        return jsonify({'error': 'Character not found'}), 404
    
    char = session_data['team'].characters[char_idx]
    char.remove_skills([skill_idx])
    
    return jsonify({'success': True})


@app.route('/api/character', methods=['POST'])
def add_character():
    """添加角色"""
    if session_data['team'] is None:
        session_data['team'] = get_default_team()
    
    data = request.json or {}
    name = data.get('name', f"角色{len(session_data['team'].characters)+1}")
    char = Character(name=name)
    session_data['team'].characters.append(char)
    
    return jsonify(character_to_dict(char))


@app.route('/api/character/<int:char_idx>', methods=['DELETE'])
def delete_character(char_idx):
    """删除角色"""
    if not session_data['team'] or not (0 <= char_idx < len(session_data['team'].characters)):
        return jsonify({'error': 'Character not found'}), 404
    
    del session_data['team'].characters[char_idx]
    if session_data['current_char_idx'] >= len(session_data['team'].characters):
        session_data['current_char_idx'] = max(0, len(session_data['team'].characters) - 1)
    
    return jsonify({'success': True})


@app.route('/api/excel/sheets', methods=['POST'])
def get_excel_sheets():
    """获取Excel文件的sheet列表"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # 保存临时文件
        temp_path = os.path.join('uploads', file.filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(temp_path)
        
        handler = ExcelHandler()
        sheets = handler.get_sheet_names(temp_path)
        
        return jsonify({
            'sheets': sheets,
            'temp_path': temp_path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/excel/load', methods=['POST'])
def load_excel():
    """加载Excel文件"""
    data = request.json
    temp_path = data.get('temp_path')
    sheet_name = data.get('sheet_name')
    
    if not temp_path or not os.path.exists(temp_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        handler = ExcelHandler()
        session_data['team'] = handler.load(temp_path, sheet_name)
        session_data['current_char_idx'] = 0
        
        # 清理临时文件
        os.remove(temp_path)
        
        return jsonify(team_to_dict(session_data['team']))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recalculate', methods=['POST'])
def recalculate_all():
    """重新计算所有"""
    if session_data['team']:
        for char in session_data['team'].characters:
            char.recalculate_all()
        return jsonify(team_to_dict(session_data['team']))
    return jsonify({'error': 'No team data'}), 404


if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
