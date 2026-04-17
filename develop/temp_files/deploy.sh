#!/bin/bash

# 校友入校登记系统部署脚本
# 运行命令: bash deploy.sh

echo "============================================"
echo "校友入校登记系统 - 部署脚本"
echo "============================================"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本"
    exit 1
fi

# 设置变量
APP_DIR="/var/www/lsalumni"
SERVICE_NAME="lsalumni"
NGINX_CONFIG="/etc/nginx/sites-available/lsalumni"
SYSTEMD_SERVICE="/etc/systemd/system/lsalumni.service"

echo "正在安装Python依赖..."
source $APP_DIR/venv/bin/activate
pip install -r $APP_DIR/requirements_prod.txt

echo "正在配置Nginx..."
cp $APP_DIR/nginx_config.conf $NGINX_CONFIG
ln -sf $NGINX_CONFIG /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx配置测试通过"
    systemctl reload nginx
else
    echo "Nginx配置错误，请检查配置文件"
    exit 1
fi

echo "正在配置系统服务..."
cp $APP_DIR/systemd_service.service $SYSTEMD_SERVICE
systemctl daemon-reload
systemctl enable $SERVICE_NAME

echo "正在设置环境变量..."
cat > $APP_DIR/.env << EOF
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=mysql+pymysql://root:Sy6787687.@localhost/lsalumni
UPLOAD_FOLDER=$APP_DIR/uploads
LOG_LEVEL=INFO
EOF

echo "正在初始化数据库..."
cd $APP_DIR
source venv/bin/activate

# 创建数据库表
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('数据库表创建成功')
"

# 创建管理员账户
python -c "
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # 检查管理员账户是否存在
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            real_name='系统管理员',
            email='admin@pofeclife.top',
            phone='13800138001',
            user_type='admin',
            status='active'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('管理员账户创建成功 - 用户名: admin, 密码: admin123')
    else:
        print('管理员账户已存在')
"

echo "正在启动服务..."
systemctl start $SERVICE_NAME

# 检查服务状态
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ 服务启动成功"
    systemctl status $SERVICE_NAME --no-pager -l
else
    echo "❌ 服务启动失败，请检查日志："
    journalctl -u $SERVICE_NAME --no-pager -l
    exit 1
fi

echo "============================================"
echo "🎉 部署完成!"
echo "============================================"
echo "应用地址: https://www.pofeclife.top/lsalumni"
echo "管理员账户: admin / admin123"
echo ""
echo "常用命令:"
echo "查看服务状态: systemctl status $SERVICE_NAME"
echo "重启服务: systemctl restart $SERVICE_NAME"
echo "查看服务日志: journalctl -u $SERVICE_NAME -f"
echo "查看Nginx日志: tail -f /var/log/nginx/lsalumni_*.log"
echo "============================================"