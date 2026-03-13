"""
整合版本功能验证测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("鸣潮DPS计算器整合版本 - 功能验证")
print("=" * 80)

try:
    from app.core import (
        Environment,
        DamageType,
        Skill,
        Stats,
        Character,
        Team,
        DPSCalculator,
        ExcelTemplateParser,
        ExcelWriter
    )
    print("✅ 核心模块导入成功")
except Exception as e:
    print(f"❌ 核心模块导入失败: {e}")
    sys.exit(1)

print("\n【测试1】创建基础角色和技能")
try:
    stats = Stats(
        base_atk=1000.0,
        base_crit_rate=0.05,
        base_crit_damage=1.5,
        environment=Environment.TOWER
    )
    
    skill1 = Skill(
        name="普攻1",
        multiplier=2.0,
        skill_type=DamageType.NORMAL,
        count=3
    )
    
    skill2 = Skill(
        name="共鸣技能",
        multiplier=5.0,
        skill_type=DamageType.RESONANCE,
        count=1
    )
    
    char = Character(
        name="测试角色",
        position=1,
        stats=stats,
        skills=[skill1, skill2]
    )
    
    char.calculate_all_skills()
    print(f"✅ 角色创建成功: {char.name}")
    print(f"   总伤害: {char.get_total_damage():,.2f}")
    print(f"   DPS: {char.get_dps():,.2f}")
except Exception as e:
    print(f"❌ 角色创建失败: {e}")
    sys.exit(1)

print("\n【测试2】创建队伍")
try:
    calc = DPSCalculator()
    calc.add_character(char, key="测试角色")
    
    team = calc.create_team("测试队伍", ["测试角色"], rotation_time=25.0)
    print(f"✅ 队伍创建成功: {team.name}")
    print(f"   队伍DPS: {team.get_team_dps():,.2f}")
except Exception as e:
    print(f"❌ 队伍创建失败: {e}")
    sys.exit(1)

print("\n【测试3】生成报告")
try:
    report = calc.generate_report()
    print("✅ 报告生成成功")
    print(report[:200] + "..." if len(report) > 200 else report)
except Exception as e:
    print(f"❌ 报告生成失败: {e}")
    sys.exit(1)

print("\n【测试4】获取优化建议")
try:
    suggestions = char.get_optimization_suggestions()
    print(f"✅ 优化建议获取成功: {len(suggestions)} 条")
    for s in suggestions:
        print(f"   - [{s['priority']}] {s['message']}")
except Exception as e:
    print(f"❌ 优化建议获取失败: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("🎉 所有功能验证通过！")
print("=" * 80)
print("\n【文件结构】")
print("wuwa_calc_final/backend/")
print("├── app/core/")
print("│   ├── __init__.py           # 核心模块导出")
print("│   ├── dps_calculator.py     # 整合V1-V4的计算引擎")
print("│   └── excel_parser.py       # 整合V3-V4的Excel解析器")
print("├── requirements.txt          # 已添加pandas和numpy")
print("├── INTEGRATION_SUMMARY.md    # 整合总结文档")
print("└── test_integration.py       # 本测试文件")
