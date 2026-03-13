# -*- coding: utf-8 -*-
"""
鸣潮动作数据汇总 - Excel导入脚本
将Excel数据导入SQLite数据库
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List
import re

from models import (
    init_db, get_session, Character, Action, Echo, Enemy,
    Gender, BodyType, Element, WeaponType, ActionType, PositionState
)


class ExcelImporter:
    """Excel数据导入器"""
    
    def __init__(self, excel_path: str, db_path: str = 'wuwa_data.db'):
        self.excel_path = excel_path
        self.engine = init_db(db_path)
        self.session = get_session(self.engine)
        self.xlsx = pd.ExcelFile(excel_path)
        
        # 角色名称到性别体型的映射（从索引sheet读取）
        self.char_mapping: Dict[str, Dict] = {}
        
    def parse_index_sheet(self):
        """解析索引sheet，获取角色分类信息"""
        print("解析索引sheet...")
        df = pd.read_excel(self.xlsx, sheet_name='索引', header=None)
        
        current_category = None
        for idx, row in df.iterrows():
            # 检查是否是分类行
            if pd.notna(row.iloc[0]):
                cat_val = str(row.iloc[0]).strip()
                if '女' in cat_val or '男' in cat_val:
                    current_category = cat_val
                    continue
            
            # 读取角色名
            if current_category:
                for col_idx in range(2, len(row)):
                    val = row.iloc[col_idx]
                    if pd.notna(val):
                        char_name = str(val).strip()
                        if char_name and char_name != 'NaN':
                            # 解析性别和体型
                            gender = Gender.FEMALE if '女' in current_category else Gender.MALE
                            body_type = self._parse_body_type(current_category)
                            self.char_mapping[char_name] = {
                                'gender': gender,
                                'body_type': body_type
                            }
        
        print(f"从索引读取到 {len(self.char_mapping)} 个角色")
        return self.char_mapping
    
    def _parse_body_type(self, category: str) -> BodyType:
        """解析体型"""
        if '大' in category:
            return BodyType.LARGE
        elif '中小' in category:
            return BodyType.SMALL_MEDIUM
        elif '小' in category:
            return BodyType.SMALL
        else:
            return BodyType.MEDIUM
    
    def import_characters_from_actions(self, sheet_name: str):
        """从角色动作sheet导入角色和动作数据"""
        print(f"\n导入 {sheet_name} sheet...")
        df = pd.read_excel(self.xlsx, sheet_name=sheet_name, header=None)
        
        current_char = None
        current_char_name = None
        action_count = 0
        
        for idx, row in df.iterrows():
            try:
                # 检查是否是新角色开始
                name_val = row.iloc[0] if len(row) > 0 else None
                
                if pd.notna(name_val):
                    name_str = str(name_val).strip()
                    
                    # 跳过通用动作（以"通用-"开头）
                    if name_str.startswith('通用-'):
                        continue
                    
                    # 检查是否是角色名行
                    if name_str in self.char_mapping or self._is_character_name(name_str, df, idx):
                        # 保存之前的角色
                        if current_char and action_count > 0:
                            self.session.commit()
                            print(f"  角色 '{current_char_name}' 导入完成，共 {action_count} 个动作")
                        
                        # 创建新角色
                        char_info = self.char_mapping.get(name_str, {
                            'gender': Gender.FEMALE if '女' in sheet_name else Gender.MALE,
                            'body_type': BodyType.MEDIUM
                        })
                        
                        current_char = self._get_or_create_character(name_str, char_info)
                        current_char_name = name_str
                        action_count = 0
                        continue
                
                # 如果不是角色名，检查是否是动作数据行
                if current_char and len(row) > 2:
                    action = self._parse_action_row(row, current_char.id)
                    if action:
                        self.session.add(action)
                        action_count += 1
                        
                        # 每100个动作提交一次
                        if action_count % 100 == 0:
                            self.session.commit()
                            
            except Exception as e:
                print(f"  处理第{idx+1}行时出错: {e}")
                continue
        
        # 提交最后一个角色
        if current_char and action_count > 0:
            self.session.commit()
            print(f"  角色 '{current_char_name}' 导入完成，共 {action_count} 个动作")
        
        print(f"  {sheet_name} 导入完成")
    
    def _is_character_name(self, name: str, df: pd.DataFrame, idx: int) -> bool:
        """判断是否是角色名（通过检查下一行是否是动作数据）"""
        # 简单启发式：如果名字在索引中，或者是中文且长度2-4
        if name in self.char_mapping:
            return True
        
        # 检查是否是中文名（2-4个字）
        if re.match(r'^[\u4e00-\u9fa5]{2,4}$', name):
            # 检查下一行是否有动作数据特征
            if idx + 1 < len(df):
                next_row = df.iloc[idx + 1]
                if len(next_row) > 3:
                    # 检查是否有动作相关的列数据
                    action_val = next_row.iloc[2] if len(next_row) > 2 else None
                    if pd.notna(action_val) and '闪避' in str(action_val):
                        return True
        
        return False
    
    def _get_or_create_character(self, name: str, char_info: Dict) -> Character:
        """获取或创建角色"""
        char = self.session.query(Character).filter_by(name=name).first()
        if not char:
            char = Character(
                name=name,
                gender=char_info['gender'],
                body_type=char_info['body_type']
            )
            self.session.add(char)
            self.session.commit()
            print(f"  创建角色: {name}")
        return char
    
    def _parse_action_row(self, row: pd.Series, char_id: int) -> Optional[Action]:
        """解析动作数据行"""
        try:
            # 动作名在列2
            if len(row) <= 2:
                return None
            
            action_name = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None
            if not action_name or action_name in ['动作', 'NaN', '']:
                return None
            
            action = Action(
                character_id=char_id,
                action_name=action_name
            )
            
            # 解析各列数据
            # 列3: 备注
            if len(row) > 3 and pd.notna(row.iloc[3]):
                action.notes = str(row.iloc[3]).strip()
            
            # 列4: 发生帧
            if len(row) > 4 and pd.notna(row.iloc[4]):
                action.start_frame = self._parse_int(row.iloc[4])
            
            # 列5: 持续帧
            if len(row) > 5 and pd.notna(row.iloc[5]):
                action.duration_frame = self._parse_int(row.iloc[5])
            
            # 列6: 顿帧-自
            if len(row) > 6 and pd.notna(row.iloc[6]):
                action.self_hitstop = self._parse_float(row.iloc[6])
            
            # 列7: 顿帧-敌
            if len(row) > 7 and pd.notna(row.iloc[7]):
                action.enemy_hitstop = self._parse_float(row.iloc[7])
            
            # 列8: 无敌启动帧
            if len(row) > 8 and pd.notna(row.iloc[8]):
                action.invincible_start = self._parse_int(row.iloc[8])
            
            # 列9: 无敌持续帧
            if len(row) > 9 and pd.notna(row.iloc[9]):
                action.invincible_duration = self._parse_int(row.iloc[9])
            
            # 列10: 优先级改变
            if len(row) > 10 and pd.notna(row.iloc[10]):
                action.priority_change = self._parse_int(row.iloc[10])
            
            # 列11: 派生帧
            if len(row) > 11 and pd.notna(row.iloc[11]):
                action.derive_frame = self._parse_int(row.iloc[11])
            
            # 列12: 派生持续帧
            if len(row) > 12 and pd.notna(row.iloc[12]):
                action.derive_duration = self._parse_int(row.iloc[12])
            
            # 列13: 动作结束帧
            if len(row) > 13 and pd.notna(row.iloc[13]):
                action.end_frame = self._parse_int(row.iloc[13])
            
            # 列14: 可弹刀
            if len(row) > 14 and pd.notna(row.iloc[14]):
                action.can_parry = str(row.iloc[14]).strip() == '√'
            
            # 列15: 可脱手
            if len(row) > 15 and pd.notna(row.iloc[15]):
                action.can_detach = str(row.iloc[15]).strip() == '√'
            
            # 列16: 削韧值
            if len(row) > 16 and pd.notna(row.iloc[16]):
                action.poise_damage = self._parse_float(row.iloc[16])
            
            # 列17: 偏谐值（大招回收）
            if len(row) > 17 and pd.notna(row.iloc[17]):
                # 可能是文本描述，尝试解析
                val = str(row.iloc[17]).strip()
                if val.replace('.', '').isdigit():
                    action.core_recovery = self._parse_float(row.iloc[17])
            
            # 列18: 协奏回收
            if len(row) > 18 and pd.notna(row.iloc[18]):
                action.concerto_recovery = self._parse_float(row.iloc[18])
            
            # 列19: 核心回收
            if len(row) > 19 and pd.notna(row.iloc[19]):
                action.core_recovery = self._parse_float(row.iloc[19])
            
            # 列20: 受击韧性系数
            if len(row) > 20 and pd.notna(row.iloc[20]):
                action.hit_resistance_factor = self._parse_float(row.iloc[20])
            
            # 列21: 中断优先级
            if len(row) > 21 and pd.notna(row.iloc[21]):
                action.interrupt_priority = self._parse_int(row.iloc[21])
            
            # 列22: 位置状态
            if len(row) > 22 and pd.notna(row.iloc[22]):
                pos_state = str(row.iloc[22]).strip()
                if '地面' in pos_state:
                    action.position_state = PositionState.GROUND
                elif '空中' in pos_state:
                    action.position_state = PositionState.AIR
                elif '地转空' in pos_state:
                    action.position_state = PositionState.GROUND_TO_AIR
                elif '空转地' in pos_state:
                    action.position_state = PositionState.AIR_TO_GROUND
            
            # 列23: 状态转换时间
            if len(row) > 23 and pd.notna(row.iloc[23]):
                action.state_transition_time = self._parse_int(row.iloc[23])
            
            # 列24: 时间膨胀类型
            if len(row) > 24 and pd.notna(row.iloc[24]):
                action.time_dilation_type = str(row.iloc[24]).strip()
            
            # 列25: 膨胀系数-自
            if len(row) > 25 and pd.notna(row.iloc[25]):
                action.self_dilation_factor = self._parse_float(row.iloc[25])
            
            # 列26: 膨胀发生-自
            if len(row) > 26 and pd.notna(row.iloc[26]):
                action.self_dilation_start = self._parse_int(row.iloc[26])
            
            # 列27: 膨胀持续-自
            if len(row) > 27 and pd.notna(row.iloc[27]):
                action.self_dilation_duration = self._parse_int(row.iloc[27])
            
            # 列28: 膨胀系数-敌
            if len(row) > 28 and pd.notna(row.iloc[28]):
                action.enemy_dilation_factor = self._parse_float(row.iloc[28])
            
            # 列29: 膨胀发生-敌
            if len(row) > 29 and pd.notna(row.iloc[29]):
                action.enemy_dilation_start = self._parse_int(row.iloc[29])
            
            # 列30: 膨胀持续-敌
            if len(row) > 30 and pd.notna(row.iloc[30]):
                action.enemy_dilation_duration = self._parse_int(row.iloc[30])
            
            # 列31: 膨胀系数-友
            if len(row) > 31 and pd.notna(row.iloc[31]):
                action.ally_dilation_factor = self._parse_float(row.iloc[31])
            
            # 列32: 膨胀发生-友
            if len(row) > 32 and pd.notna(row.iloc[32]):
                action.ally_dilation_start = self._parse_int(row.iloc[32])
            
            # 列33: 膨胀持续-友
            if len(row) > 33 and pd.notna(row.iloc[33]):
                action.ally_dilation_duration = self._parse_int(row.iloc[33])
            
            # 列34: 命中类型
            if len(row) > 34 and pd.notna(row.iloc[34]):
                action.hit_type = str(row.iloc[34]).strip()
            
            # 列35: 位置基准
            if len(row) > 35 and pd.notna(row.iloc[35]):
                action.position_reference = str(row.iloc[35]).strip()
            
            # 列36: 跟随骨骼
            if len(row) > 36 and pd.notna(row.iloc[36]):
                action.follow_bone = str(row.iloc[36]).strip()
            
            # 列37: 解除跟随帧
            if len(row) > 37 and pd.notna(row.iloc[37]):
                action.unfollow_frame = self._parse_int(row.iloc[37])
            
            # 列38: 缩放倍数
            if len(row) > 38 and pd.notna(row.iloc[38]):
                action.scale_factor = self._parse_float(row.iloc[38])
            
            # 列39: 判定范围
            if len(row) > 39 and pd.notna(row.iloc[39]):
                action.hit_range = str(row.iloc[39]).strip()
            
            # 尝试从动作名推断动作类型
            action.action_type = self._infer_action_type(action_name)
            
            return action
            
        except Exception as e:
            print(f"    解析动作行出错: {e}")
            return None
    
    def _infer_action_type(self, action_name: str) -> Optional[ActionType]:
        """从动作名推断动作类型"""
        name = action_name.lower()
        
        if '普攻' in name or '攻击' in name:
            return ActionType.NORMAL_ATTACK
        elif '共鸣技能' in name or 'e-' in name:
            return ActionType.RESONANCE_SKILL
        elif '共鸣回路' in name:
            return ActionType.RESONANCE_CIRCUIT
        elif '共鸣解放' in name or 'q-' in name:
            return ActionType.RESONANCE_LIBERATION
        elif '变奏' in name or '出场技' in name:
            return ActionType.INTRO_SKILL
        elif '延奏' in name:
            return ActionType.OUTRO_SKILL
        elif '闪避' in name or '躲避' in name:
            return ActionType.DODGE
        elif '声骸' in name or '召唤' in name:
            return ActionType.ECHO
        
        return None
    
    def _parse_int(self, val) -> Optional[int]:
        """解析整数"""
        if pd.isna(val):
            return None
        try:
            return int(float(val))
        except:
            return None
    
    def _parse_float(self, val) -> Optional[float]:
        """解析浮点数"""
        if pd.isna(val):
            return None
        try:
            return float(val)
        except:
            return None
    
    def import_echoes(self):
        """导入声骸数据"""
        print("\n导入声骸数据...")
        
        try:
            df = pd.read_excel(self.xlsx, sheet_name='声骸', header=None)
        except:
            print("  未找到'声骸'sheet，跳过")
            return
        
        current_echo_name = None
        count = 0
        
        for idx, row in df.iterrows():
            try:
                # 声骸名在列0
                name_val = row.iloc[0] if len(row) > 0 else None
                
                if pd.notna(name_val):
                    name_str = str(name_val).strip()
                    if name_str and name_str != '名称':
                        current_echo_name = name_str
                
                # 动作名在列1
                if len(row) > 1 and pd.notna(row.iloc[1]) and current_echo_name:
                    action_name = str(row.iloc[1]).strip()
                    if action_name and action_name != '动作':
                        echo = self._parse_echo_row(row, current_echo_name, action_name)
                        if echo:
                            self.session.add(echo)
                            count += 1
                            
                            if count % 50 == 0:
                                self.session.commit()
                                
            except Exception as e:
                print(f"  处理第{idx+1}行时出错: {e}")
                continue
        
        self.session.commit()
        print(f"  导入 {count} 个声骸动作")
    
    def _parse_echo_row(self, row: pd.Series, echo_name: str, action_name: str) -> Optional[Echo]:
        """解析声骸数据行"""
        try:
            echo = Echo(
                name=echo_name,
                action_name=action_name
            )
            
            # 列2: 发生帧
            if len(row) > 2 and pd.notna(row.iloc[2]):
                echo.start_frame = self._parse_int(row.iloc[2])
            
            # 列3: 持续帧
            if len(row) > 3 and pd.notna(row.iloc[3]):
                echo.duration_frame = self._parse_int(row.iloc[3])
            
            # 列4: 顿帧-自
            if len(row) > 4 and pd.notna(row.iloc[4]):
                echo.self_hitstop = self._parse_float(row.iloc[4])
            
            # 列5: 顿帧-敌
            if len(row) > 5 and pd.notna(row.iloc[5]):
                echo.enemy_hitstop = self._parse_float(row.iloc[5])
            
            # 列8: 动作结束帧
            if len(row) > 8 and pd.notna(row.iloc[8]):
                echo.end_frame = self._parse_int(row.iloc[8])
            
            # 列9: 可弹刀
            if len(row) > 9 and pd.notna(row.iloc[9]):
                echo.can_parry = str(row.iloc[9]).strip() == '√'
            
            # 列10: 可脱手
            if len(row) > 10 and pd.notna(row.iloc[10]):
                echo.can_detach = str(row.iloc[10]).strip() == '√'
            
            # 列11: 削韧值
            if len(row) > 11 and pd.notna(row.iloc[11]):
                echo.poise_damage = self._parse_float(row.iloc[11])
            
            # 列12: 大招回收
            if len(row) > 12 and pd.notna(row.iloc[12]):
                val = self._parse_float(row.iloc[12])
                if val:
                    echo.core_recovery = val
            
            # 列13: 协奏回收
            if len(row) > 13 and pd.notna(row.iloc[13]):
                echo.concerto_recovery = self._parse_float(row.iloc[13])
            
            # 列16: 类型
            if len(row) > 16 and pd.notna(row.iloc[16]):
                echo.skill_type = str(row.iloc[16]).strip()
            
            # 列17: 冷却
            if len(row) > 17 and pd.notna(row.iloc[17]):
                echo.cooldown = self._parse_int(row.iloc[17])
            
            # 列18: 单段冷却
            if len(row) > 18 and pd.notna(row.iloc[18]):
                echo.single_cooldown = self._parse_float(row.iloc[18])
            
            # 列19: 接续时限
            if len(row) > 19 and pd.notna(row.iloc[19]):
                echo.continuation_limit = self._parse_int(row.iloc[19])
            
            # 列20: 位置状态
            if len(row) > 20 and pd.notna(row.iloc[20]):
                pos_state = str(row.iloc[20]).strip()
                if '地面' in pos_state:
                    echo.position_state = PositionState.GROUND
                elif '空中' in pos_state:
                    echo.position_state = PositionState.AIR
            
            # 列21: 状态转换时间
            if len(row) > 21 and pd.notna(row.iloc[21]):
                echo.state_transition_time = self._parse_int(row.iloc[21])
            
            # 列23: 时间膨胀类型
            if len(row) > 23 and pd.notna(row.iloc[23]):
                echo.time_dilation_type = str(row.iloc[23]).strip()
            
            # 列24: 膨胀系数-自
            if len(row) > 24 and pd.notna(row.iloc[24]):
                echo.self_dilation_factor = self._parse_float(row.iloc[24])
            
            # 列27: 膨胀系数-敌
            if len(row) > 27 and pd.notna(row.iloc[27]):
                echo.enemy_dilation_factor = self._parse_float(row.iloc[27])
            
            # 列22: 备注/技能说明
            if len(row) > 22 and pd.notna(row.iloc[22]):
                notes = str(row.iloc[22]).strip()
                if len(notes) > 10:  # 较长的文本是技能说明
                    echo.description = notes
                else:
                    echo.notes = notes
            
            return echo
            
        except Exception as e:
            print(f"    解析声骸行出错: {e}")
            return None
    
    def import_all(self):
        """导入所有数据"""
        print(f"开始导入数据: {self.excel_path}")
        print("=" * 50)
        
        # 1. 解析索引
        self.parse_index_sheet()
        
        # 2. 导入角色-女
        if '角色-女' in self.xlsx.sheet_names:
            self.import_characters_from_actions('角色-女')
        
        # 3. 导入角色-男
        if '角色-男' in self.xlsx.sheet_names:
            self.import_characters_from_actions('角色-男')
        
        # 4. 导入声骸
        if '声骸' in self.xlsx.sheet_names:
            self.import_echoes()
        
        print("\n" + "=" * 50)
        print("导入完成!")
        
        # 统计
        char_count = self.session.query(Character).count()
        action_count = self.session.query(Action).count()
        echo_count = self.session.query(Echo).count()
        
        print(f"角色数量: {char_count}")
        print(f"动作数量: {action_count}")
        print(f"声骸数量: {echo_count}")
    
    def close(self):
        """关闭会话"""
        self.session.close()


def main():
    """主函数"""
    excel_path = r'd:\素材\鸣潮动作数据汇总.xlsx'
    db_path = 'wuwa_data.db'
    
    importer = ExcelImporter(excel_path, db_path)
    
    try:
        importer.import_all()
    finally:
        importer.close()


if __name__ == '__main__':
    main()
