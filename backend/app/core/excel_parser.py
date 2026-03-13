"""
Excel拉表解析器 - 整合V3-V4版本的最优特性
完美解析社区通用的鸣潮拉表Excel模板
"""

import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
from .dps_calculator import Character, Stats, Skill, DamageType, Environment


class ExcelTemplateParser:
    """
    拉表模板解析器
    
    解析策略（来自V3-V4的最优方案）:
    1. 查找所有"角色主类型"标记
    2. 读取角色名（下一行）
    3. 读取属性区（行+2到行+10）
    4. 读取技能区（列14+）
    """
    
    def __init__(self):
        self.invalid_names = [
            "一号位", "二号位", "三号位", "角色主类型", 
            "攻击", "次数", "a", ""
        ]
    
    def parse_file(self, file_path: str) -> List[Character]:
        """
        从Excel文件解析所有角色
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            角色对象列表
        """
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        characters = []
        
        char_positions = self._find_character_positions(df)
        
        for idx, start_row in enumerate(char_positions):
            char = self._parse_character(df, start_row, idx + 1, file_path)
            if char and self._is_valid_character(char):
                characters.append(char)
        
        return characters
    
    def _find_character_positions(self, df: pd.DataFrame) -> List[int]:
        """查找所有角色分块的起始行"""
        positions = []
        for i in range(len(df)):
            row = df.iloc[i]
            for j, val in enumerate(row):
                if pd.notna(val) and str(val).strip() == "角色主类型":
                    positions.append(i)
                    break
        return positions
    
    def _parse_character(self, df: pd.DataFrame, start_row: int, 
                         position: int, file_path: str) -> Optional[Character]:
        """解析单个角色"""
        try:
            char_name = self._extract_character_name(df, start_row)
            if not char_name:
                return None
            
            char = Character(name=char_name, position=position)
            char.stats = Stats()
            
            self._parse_stats(df, start_row + 2, char.stats)
            self._parse_skills(df, start_row, char)
            
            char.calculate_all_skills()
            
            return char
            
        except Exception as e:
            print(f"解析角色失败: {e}")
            return None
    
    def _extract_character_name(self, df: pd.DataFrame, start_row: int) -> Optional[str]:
        """提取角色名"""
        if start_row + 1 >= len(df):
            return None
        
        name_row = df.iloc[start_row + 1]
        for j in range(len(name_row)):
            if pd.notna(name_row.iloc[j]):
                name = str(name_row.iloc[j]).strip()
                if name and name not in self.invalid_names:
                    return name
        return None
    
    def _parse_stats(self, df: pd.DataFrame, start_row: int, stats: Stats):
        """解析属性区（整合V3-V4的完整属性解析）"""
        for i in range(start_row, min(start_row + 10, len(df))):
            row = df.iloc[i]
            
            label = self._extract_label(row)
            if not label:
                continue
            
            values = self._extract_values(row)
            self._set_stat_by_label(stats, label, values)
    
    def _extract_label(self, row) -> str:
        """从行中提取标签"""
        for j in range(min(2, len(row))):
            if pd.notna(row.iloc[j]):
                return str(row.iloc[j]).strip()
        return ""
    
    def _extract_values(self, row) -> List[float]:
        """从行中提取数值"""
        values = []
        for j in range(2, min(13, len(row))):
            if pd.notna(row.iloc[j]):
                try:
                    val = float(row.iloc[j])
                    values.append(val)
                except:
                    pass
        return values
    
    def _set_stat_by_label(self, stats: Stats, label: str, values: List[float]):
        """根据标签设置属性值（V4的完整属性映射）"""
        if not values:
            return
        
        # 攻击区
        if label == "白值":
            stats.base_atk = values[0]
        elif label == "固有武器":
            stats.inherent_weapon_atk = values[0]
        elif label == "主副词条":
            if len(values) > 0:
                stats.echo_main_sub_atk = values[0]
            if len(values) > 2:
                stats.echo_crit_rate = values[2]
            if len(values) > 3:
                stats.echo_crit_damage = values[3]
        elif label == "声骸固定攻击":
            stats.fixed_atk = values[0]
        elif label == "额外固定攻击":
            stats.extra_fixed_atk = values[0]
        elif label == "自拐攻击":
            stats.self_atk_buff = values[0]
        elif label == "被拐攻击":
            stats.received_atk_buff = values[0]
        
        # 加成区
        elif label == "3C声骸":
            stats.echo_3c_count = int(values[0])
        elif label == "套装首位":
            stats.echo_set_first = values[0]
        elif label == "自拐属伤":
            stats.self_element_buff = values[0]
        elif label == "被拐属伤":
            stats.received_element_buff = values[0]
        elif label == "其他属伤":
            stats.other_element_buff = values[0]
        elif label == "主类型加成":
            stats.main_type_bonus = values[0]
        
        # 暴击区
        elif label == "基础与固有":
            if len(values) > 0:
                stats.base_crit_rate = values[0]
            if len(values) > 1:
                stats.base_crit_damage = values[1]
        elif label == "武器":
            if len(values) > 0:
                stats.weapon_crit_rate = values[0]
            if len(values) > 1:
                stats.weapon_crit_damage = values[1]
        elif label == "套装":
            if len(values) > 0:
                stats.set_crit_rate = values[0]
            if len(values) > 1:
                stats.set_crit_damage = values[1]
        elif label == "共鸣链":
            if len(values) > 0:
                stats.chain_crit_rate = values[0]
            if len(values) > 1:
                stats.chain_crit_damage = values[1]
        elif label == "队友":
            if len(values) > 0:
                stats.teammate_crit_rate = values[0]
            if len(values) > 1:
                stats.teammate_crit_damage = values[1]
        elif label == "面板暴击率":
            stats.panel_crit_rate = values[0]
        elif label == "溢出暴击":
            stats.overflow_crit_rate = values[0]
        elif label == "面板暴击伤害":
            stats.panel_crit_damage = values[0]
        
        # 加深区
        elif label == "全加深":
            stats.universal_amplify = values[0]
        elif label == "主类型加深":
            stats.main_type_amplify = values[0]
        
        # 副词条
        elif label == "大攻击":
            stats.sub_atk_percent = values[0]
        elif label == "共技伤害":
            stats.sub_skill_bonus = values[0]
        elif label == "暴击":
            stats.sub_crit_rate = values[0]
        elif label == "爆伤":
            stats.sub_crit_damage = values[0]
    
    def _parse_skills(self, df: pd.DataFrame, start_row: int, char: Character):
        """解析技能区（V4的完整技能解析）"""
        skill_start = self._find_skill_start(df, start_row)
        if not skill_start:
            return
        
        for i in range(skill_start, min(skill_start + 50, len(df))):
            row = df.iloc[i]
            
            if len(row) <= 14:
                continue
            
            try:
                skill = self._parse_single_skill(row)
                if skill and skill.multiplier > 0:
                    self._parse_skill_results(row, skill)
                    char.skills.append(skill)
            except Exception as e:
                continue
    
    def _find_skill_start(self, df: pd.DataFrame, start_row: int) -> Optional[int]:
        """查找技能区起始行"""
        for i in range(start_row + 2, min(start_row + 15, len(df))):
            row = df.iloc[i]
            if len(row) > 14 and pd.notna(row.iloc[14]):
                if str(row.iloc[14]).strip() == "次数":
                    return i + 1
        return None
    
    def _parse_single_skill(self, row) -> Optional[Skill]:
        """解析单个技能基本信息"""
        count = 1
        name = ""
        multiplier = 0.0
        skill_type = DamageType.NORMAL
        
        if pd.notna(row.iloc[14]):
            try:
                count = int(float(row.iloc[14]))
            except:
                pass
        
        if len(row) > 15 and pd.notna(row.iloc[15]):
            name = str(row.iloc[15]).strip()
        
        if len(row) > 16 and pd.notna(row.iloc[16]):
            try:
                multiplier = float(row.iloc[16])
            except:
                pass
        
        if len(row) > 17 and pd.notna(row.iloc[17]):
            type_str = str(row.iloc[17]).strip()
            for dt in DamageType:
                if dt.value == type_str:
                    skill_type = dt
                    break
        
        if not name and multiplier <= 0:
            return None
        
        return Skill(
            name=name,
            multiplier=multiplier,
            skill_type=skill_type,
            count=count
        )
    
    def _parse_skill_results(self, row, skill: Skill):
        """解析技能计算结果（来自V4的完整结果读取）"""
        col_map = {
            18: 'panel_atk',
            19: 'atk_zone',
            20: 'bonus_zone',
            21: 'crit_zone',
            22: 'amplify_zone',
            23: 'defense_zone',
            24: 'resistance_zone',
            25: 'multiplier_boost',
            26: 'vulnerable_zone',
            27: 'independent_zone',
            28: 'final_damage',
            29: 'counter1',
            30: 'counter2',
            31: 'skill_def_ignore',
            32: 'skill_def_shred',
            33: 'skill_defense_zone',
            34: 'skill_enemy_level',
        }
        
        for col, attr in col_map.items():
            if len(row) > col and pd.notna(row.iloc[col]):
                try:
                    val = row.iloc[col]
                    if attr in ['counter1', 'counter2', 'skill_enemy_level']:
                        val = int(float(val))
                    else:
                        val = float(val)
                    setattr(skill, attr, val)
                except:
                    pass
    
    def _is_valid_character(self, char: Character) -> bool:
        """检查角色是否有效"""
        if char.name in self.invalid_names:
            return False
        if char.stats.base_atk == 0 and len(char.skills) == 0:
            return False
        return True


class ExcelWriter:
    """
    Excel写入器 - 来自V4的同格式输出功能
    将计算结果写回与拉表模板同格式的Excel文件
    """
    
    def __init__(self):
        self.max_cols = 35
    
    def save_team_to_excel(self, characters: List[Character], 
                          output_path: str, environment: Environment = Environment.TOWER):
        """
        将队伍保存为Excel文件，格式完全同拉表模板
        
        Args:
            characters: 角色列表
            output_path: 输出文件路径
            environment: 战斗环境
        """
        data = []
        
        for char in characters:
            char_data = self._character_to_rows(char, environment)
            data.extend(char_data)
        
        df = pd.DataFrame(data, columns=[f"Col_{i}" for i in range(self.max_cols)])
        df.to_excel(output_path, index=False, header=False)
        print(f"已保存到: {output_path}")
    
    def _character_to_rows(self, char: Character, env: Environment) -> List[List]:
        """将角色转换为行数据"""
        rows = []
        stats = char.stats
        
        row0 = [""] * self.max_cols
        row0[1] = "角色主类型"
        rows.append(row0)
        
        row1 = [""] * self.max_cols
        row1[1] = char.name
        rows.append(row1)
        
        row2 = [""] * self.max_cols
        row2[1] = "攻击"
        row2[3] = "加成区"
        row2[5] = "暴击"
        row2[7] = "暴击伤害"
        row2[9] = "加深区"
        row2[11] = "副词条"
        rows.append(row2)
        
        stat_rows = self._create_stat_rows(stats)
        rows.extend(stat_rows)
        
        skill_header = self._create_skill_header()
        rows.append(skill_header)
        
        for skill in char.skills:
            skill_row = self._skill_to_row(skill)
            rows.append(skill_row)
        
        return rows
    
    def _create_stat_rows(self, stats: Stats) -> List[List]:
        """创建属性行"""
        rows = []
        
        rows.append(self._create_stat_row("白值", [stats.base_atk]))
        rows.append(self._create_stat_row("固有武器", [stats.inherent_weapon_atk]))
        rows.append(self._create_stat_row("主副词条", [
            stats.echo_main_sub_atk, None, stats.echo_crit_rate, stats.echo_crit_damage
        ]))
        rows.append(self._create_stat_row("声骸固定攻击", [stats.fixed_atk]))
        rows.append(self._create_stat_row("额外固定攻击", [stats.extra_fixed_atk]))
        rows.append(self._create_stat_row("自拐攻击", [stats.self_atk_buff]))
        rows.append(self._create_stat_row("被拐攻击", [stats.received_atk_buff]))
        rows.append(self._create_stat_row("3C声骸", [stats.echo_3c_count]))
        
        return rows
    
    def _create_stat_row(self, label: str, values: List) -> List:
        """创建单个属性行"""
        row = [""] * self.max_cols
        row[0] = label
        for i, val in enumerate(values):
            if val is not None:
                row[i + 2] = val
        return row
    
    def _create_skill_header(self) -> List:
        """创建技能表头"""
        row = [""] * self.max_cols
        headers = [
            "次数", "动作", "倍率", "类型", "面板攻击", "攻击区", "加成区", "双爆区",
            "加深区", "防御区", "抗性区", "倍率提升", "易伤区", "独立乘区",
            "伤害", "计数1", "计数2", "无视防御", "减防", "防御区", "怪物等级"
        ]
        for i, header in enumerate(headers):
            row[14 + i] = header
        return row
    
    def _skill_to_row(self, skill: Skill) -> List:
        """将技能转换为行数据"""
        row = [""] * self.max_cols
        
        row[14] = skill.count
        row[15] = skill.name
        row[16] = skill.multiplier
        row[17] = skill.skill_type.value
        
        col_map = {
            18: skill.panel_atk,
            19: skill.atk_zone,
            20: skill.bonus_zone,
            21: skill.crit_zone,
            22: skill.amplify_zone,
            23: skill.defense_zone,
            24: skill.resistance_zone,
            25: skill.multiplier_boost,
            26: skill.vulnerable_zone,
            27: skill.independent_zone,
            28: skill.final_damage,
            29: skill.counter1,
            30: skill.counter2,
            31: skill.skill_def_ignore,
            32: skill.skill_def_shred,
            33: skill.skill_defense_zone,
            34: skill.skill_enemy_level,
        }
        
        for col, val in col_map.items():
            if val is not None:
                row[col] = val
        
        return row
