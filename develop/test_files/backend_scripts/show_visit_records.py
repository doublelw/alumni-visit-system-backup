"""
显示当前访问记录统计
展示所有增强后的字段
"""

import sqlite3
from datetime import datetime

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def main():
    print_section("访问记录统计 - 增强字段展示")

    conn = sqlite3.connect('instance/alumni_system_dev.db')
    cursor = conn.cursor()

    # 总体统计
    cursor.execute('SELECT COUNT(*) FROM visit_records')
    total_count = cursor.fetchone()[0]

    print(f"\n总访问记录数: {total_count}")

    # 按访问者类型统计
    cursor.execute('''
        SELECT visitor_type, COUNT(*) as count
        FROM visit_records
        GROUP BY visitor_type
        ORDER BY count DESC
    ''')

    print_section("按访问者类型统计")
    type_stats = cursor.fetchall()
    for visitor_type, count in type_stats:
        type_name = {
            'parent': '家长',
            'alumni': '校友',
            'visitor': '访客',
            'teacher': '教师',
            'student': '学生'
        }.get(visitor_type, visitor_type)
        print(f"  {type_name}: {count}次")

    # 详细记录列表
    print_section("最新10条访问记录详情")

    cursor.execute('''
        SELECT vr.id, u.real_name, vr.visitor_type, vr.visit_purpose,
               vr.destination, vr.host_person, vr.guard_name,
               vr.entry_time, vr.info_complete
        FROM visit_records vr
        JOIN users u ON vr.user_id = u.id
        ORDER BY vr.created_at DESC
        LIMIT 10
    ''')

    records = cursor.fetchall()

    print(f"\n{'ID':<5} {'姓名':<15} {'类型':<10} {'目的':<20} {'目的地':<15} {'接待人':<10} {'门卫':<10} {'完整':<10} {'时间':<20}")
    print("-" * 130)

    type_names = {
        'parent': '家长',
        'alumni': '校友',
        'visitor': '访客',
        'teacher': '教师',
        'student': '学生'
    }

    for record in records:
        record_id, name, vtype, purpose, dest, host, guard, entry_time, complete = record

        type_name = type_names.get(vtype, vtype or '未知')
        complete_str = "是" if complete else "否"

        # 处理时间格式
        if entry_time:
            if isinstance(entry_time, str):
                time_str = entry_time[:16]  # YYYY-MM-DD HH:MM
            else:
                time_str = entry_time.strftime('%Y-%m-%d %H:%M')
        else:
            time_str = 'N/A'

        print(f"{record_id:<5} {name:<15} {type_name:<10} {(purpose or '-')[:20]:<20} {(dest or '-')[:15]:<15} {(host or '-')[:10]:<10} {(guard or '-')[:10]:<10} {complete_str:<10} {time_str:<20}")

    # 信息完整度统计
    cursor.execute('''
        SELECT info_complete, COUNT(*) as count
        FROM visit_records
        GROUP BY info_complete
    ''')

    print_section("信息完整度统计")
    complete_stats = cursor.fetchall()
    for complete, count in complete_stats:
        status = "完整" if complete else "不完整"
        print(f"  {status}: {count}条")

    # 目的地统计
    cursor.execute('''
        SELECT destination, COUNT(*) as count
        FROM visit_records
        WHERE destination IS NOT NULL AND destination != ''
        GROUP BY destination
        ORDER BY count DESC
    ''')

    print_section("访问目的地统计（Top 5）")
    dest_stats = cursor.fetchall()
    for dest, count in dest_stats[:5]:
        print(f"  {dest}: {count}次")

    conn.close()

    print_section("统计完成")

    print("""
字段说明:
- visitor_type: 访问者类型（家长/校友/访客）
- destination: 访问目的地（如"教务处"、"图书馆"）
- host_person: 接待人姓名
- guard_name: 门卫放行人姓名
- info_complete: 信息是否完整（有手机和邮箱）
- visit_purpose: 访问目的

时间闭环:
- created_at: 用户预约提交时间
- approval_time: 老师审批确认时间
- visit_date: 预期访问日期
- entry_time: 实际进门时间
""")

if __name__ == "__main__":
    main()
