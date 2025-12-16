from lxml import etree


def parse_html(html_content):
    """解析HTML数据"""
    # 加载 HTML
    if isinstance(html_content, str) and html_content.endswith(".html"):
        with open(html_content, "rb") as f:
            content = f.read()
    else:
        content = (
            html_content.encode("utf-8")
            if isinstance(html_content, str)
            else html_content
        )

    parser = etree.HTMLParser(recover=True, encoding="utf-8")
    tree = etree.fromstring(content, parser)
    root = tree if tree.tag == "html" else tree.getroottree().getroot()
    return root


def group_logic_cols(etree_group):
    """
    计算行组各行的逻辑单元格数，统计rowspan和colspan
    """
    # 存储每行的物理/视觉列数
    logic_cols = []
    rowspan_occupancy = []
    for row_idx, row in enumerate(etree_group):
        # 更新 rowspan 占用：上一行延续下来的，每列 -1；若减到0则释放
        new_occupancy = [r - 1 for r in rowspan_occupancy if r - 1 > 0]
        rowspan_occupancy = new_occupancy

        cells = row.xpath(".//td | .//th")
        for cell in cells:
            cs = int(cell.get("colspan", "1")) or 1
            rs = int(cell.get("rowspan", "1")) or 1
            for i in range(cs):
                rowspan_occupancy.append(rs)
        logic_cols.append(len(rowspan_occupancy))
    return logic_cols


def rows_occupied(rows):
    """返回每一行被前面 rowspan 占用的视觉列数量（即不可用单元格数）。
    Args:
        rows: list of etree.Element("<tr>")
    Returns:
        List[int]: occupied_counts[i] 表示第 i 行被 rowspan 占用的列数
    """
    # active[col] 表示该列在当前行是否被前面的 rowspan 占用（值 > 0 表示是），
    # 且值为包括当前行在内的剩余占用行数。
    active = []
    occupied_counts = []

    for row in rows:
        # Step 1: 计算当前行被前面 rowspan 占用的列数
        occupied = sum(1 for x in active if x > 0)
        occupied_counts.append(occupied)

        # Step 2: 构建当前行的占用状态（用于跳过列），并准备下一行的 active
        current_occupied = [x > 0 for x in active]
        next_active = [max(0, x - 1) for x in active]

        # Step 3: 遍历当前行的所有单元格（<td> 或 <th>）
        col = 0
        cells = [child for child in row if child.tag in ("td", "th")]

        for cell in cells:
            # 跳过被前面 rowspan 占用的列
            while col < len(current_occupied) and current_occupied[col]:
                col += 1

            # 确保数组足够长以容纳当前单元格
            while col >= len(current_occupied):
                current_occupied.append(False)
                next_active.append(0)

            # 解析 rowspan 和 colspan，确保至少为 1
            try:
                rowspan = max(1, int(cell.get("rowspan", 1)))
            except (ValueError, TypeError):
                rowspan = 1
            try:
                colspan = max(1, int(cell.get("colspan", 1)))
            except (ValueError, TypeError):
                colspan = 1

            # 扩展数组以适应 colspan
            while col + colspan > len(next_active):
                next_active.append(0)
                current_occupied.append(False)

            # 如果 rowspan > 1，则设置下一行开始的占用
            if rowspan > 1:
                for c in range(col, col + colspan):
                    next_active[c] = rowspan - 1  # 从下一行起还需占用 rowspan-1 行

            col += colspan

        # 更新 active 为下一行准备
        active = next_active

    return occupied_counts


def align_table(html_content: str) -> str:
    """
    对 HTML 中的第一个 <table> 进行列对齐处理：
      - 清理每行 <tr> 末尾的空白单元格（<td>/<th> 内容为空或仅空白）
      - 计算所有行清理后的最大列数
      - 在每行末尾补 <td></td> 至该列数
    返回：修改后的完整 HTML 字符串（保留原始结构、属性、换行等）
    """
    doc = parse_html(html_content)

    # 支持处理多个 <table>？当前按「所有 table」处理（更实用）
    tables = doc.xpath("//table")
    if not tables:
        return html_content

    for table in tables:
        rows = table.xpath(".//tr")
        if not rows:
            continue

        # 清理每行末尾空白单元格，并记录清理后列数
        cleaned_row_cells = []  # List[List[etree.Element]]
        for tr in rows:
            cells = tr.xpath("./td | ./th")
            # 倒序移除末尾空白单元格（就地操作更安全）
            while cells:
                cell = cells[-1]
                text = "".join(cell.itertext())  # 递归提取所有文本（含子标签内）
                if text.strip() == "":
                    # 移除此单元格
                    tr.remove(cell)
                    cells.pop()
                else:
                    break
            cleaned_row_cells.append(cells)

        # 计算所有列的占用情况
        rows_len = group_logic_cols(rows)
        print("rows_len", rows_len)

        # Step 2: 计算最大列数
        max_cols = max(rows_len)

        # Step 3: 补齐每行至 max_cols（补 <td></td>）
        for idx, (tr, cells) in enumerate(zip(rows, cleaned_row_cells)):
            need = max_cols - rows_len[idx]
            for _ in range(need):
                new_td = etree.Element("td")
                # 可选：保留某些默认属性？一般空 td 即可
                tr.append(new_td)

    # 序列化回字符串；保留原始编码/声明
    return etree.tostring(doc, encoding="unicode", method="html")
