"""
IP 地址脱敏工具
所有存储或展示的 IP 地址必须经过脱敏处理。
"""


def mask_ip(ip: str) -> str:
    """
    脱敏 IP 地址，仅保留前两段。
    - IPv4: 111.19.99.2     -> 111.19.*.*
    - IPv6: 2001:db8::1      -> 2001:*:*:*:*:*:*:*
    - localhost: 127.0.0.1   -> 127.0.*.*
    - 未知/异常: unknown     -> ***
    """
    if not ip or ip in ("unknown", "-", ""):
        return "***"

    # IPv4: 保留前两段
    parts = ip.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        return f"{parts[0]}.{parts[1]}.*.*"

    # IPv6: 保留第一段
    if ":" in ip:
        first_part = ip.split(":")[0]
        return f"{first_part}:*:*:*:*:*:*:*"

    # 无法识别的格式
    return "***"
