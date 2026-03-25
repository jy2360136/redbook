"""
公司名过滤模块
==============
用于根据公司名单过滤新闻标题

TODO: 后续重构方向
1. 从配置文件读取公司名单
2. 支持自定义公司名单
3. 支持公司别名和简称映射
4. 支持正则表达式匹配
5. 支持公司名称权重打分
"""

# 默认公司名单（暂时写死，后续会从配置文件读取）
DEFAULT_COMPANIES = [
    "比亚迪", "小鹏", "蔚来", "理想", "小米", "吉利", "华为", "腾讯", "阿里",
    "字节", "百度", "京东", "美团", "拼多多", "网易", "快手", "B 站",
    "宁德时代", "茅台", "五粮液", "伊利", "蒙牛", "安踏", "李宁", "万科",
]


def filter_by_companies(title: str, companies: list = None, use_regex: bool = False) -> bool:
    """
    根据公司名过滤标题
    
    Args:
        title: 新闻标题
        companies: 公司名列表，为 None 时使用 DEFAULT_COMPANIES
        use_regex: 是否使用正则表达式匹配（目前未实现）
    
    Returns:
        bool: 是否包含公司名
    
    Examples:
        >>> filter_by_companies("小米发布新手机")
        True
        >>> filter_by_companies("今天天气不错")
        False
    """
    if companies is None:
        companies = DEFAULT_COMPANIES
    
    # TODO: 实现正则表达式匹配
    # if use_regex:
    #     pattern = '|'.join(map(re.escape, companies))
    #     return bool(re.search(pattern, title))
    
    return any(c in title for c in companies)


def get_company_matches(title: str, companies: list = None) -> list:
    """
    获取标题中匹配的所有公司名
    
    Args:
        title: 新闻标题
        companies: 公司名列表，为 None 时使用 DEFAULT_COMPANIES
    
    Returns:
        list: 匹配到的公司名列表
    
    Examples:
        >>> get_company_matches("小米和华为合作")
        ['小米', '华为']
    """
    if companies is None:
        companies = DEFAULT_COMPANIES
    
    matches = []
    for company in companies:
        if company in title:
            matches.append(company)
    
    return matches


def score_by_companies(title: str, companies: list = None) -> int:
    """
    根据标题中匹配的公司名数量打分
    
    Args:
        title: 新闻标题
        companies: 公司名列表，为 None 时使用 DEFAULT_COMPANIES
    
    Returns:
        int: 匹配到的公司名数量（分数）
    """
    return len(get_company_matches(title, companies))


# 测试
if __name__ == "__main__":
    test_titles = [
        "小米发布新手机，雷军亲自站台",
        "腾讯和阿里达成战略合作",
        "今天天气不错",
        "华为Mate60 发布，余承东亮相",
        "比亚迪销量再创新高",
    ]
    
    print("测试公司名过滤功能：\n")
    for title in test_titles:
        is_match = filter_by_companies(title)
        matches = get_company_matches(title)
        score = score_by_companies(title)
        print(f"标题：{title}")
        print(f"  匹配：{is_match}")
        print(f"  公司：{matches}")
        print(f"  分数：{score}\n")
