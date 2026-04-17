import sqlite3

conn = sqlite3.connect('backend/instance/alumni_system_dev.db')
cursor = conn.cursor()

# 查找张小明妈妈(ID:5)和她关联的学生
cursor.execute('''
    SELECT u1.id, u1.real_name, u1.phone, u1.user_type
    FROM users u1
    WHERE u1.id = 5
''')

parent = cursor.fetchone()
print(f"家长信息: ID={parent[0]}, 姓名={parent[1]}, 手机={parent[2]}, 类型={parent[3]}")

# 查找这个家长关联的学生
cursor.execute('''
    SELECT u.id, u.real_name, u.student_id, u.grade, u.class_id
    FROM users u
    WHERE u.parent_student_id = 5
''')

students = cursor.fetchall()
print(f"\n关联的学生数量: {len(students)}")
for student in students:
    print(f"  学生: ID={student[0]}, 姓名={student[1]}, 学号={student[2]}, 年级={student[3]}, 班级={student[4]}")

# 也检查反向关联 - 通过student_parent_id
cursor.execute('''
    SELECT u.id, u.real_name, u.student_id, u.grade, u.class_id, u.student_parent_id
    FROM users u
    WHERE u.student_parent_id = 5
''')

students_reverse = cursor.fetchall()
print(f"\n反向关联的学生数量: {len(students_reverse)}")
for student in students_reverse:
    print(f"  学生: ID={student[0]}, 姓名={student[1]}, 学号={student[2]}, 年级={student[3]}, 班级={student[4]}, parent_id={student[5]}")

conn.close()
