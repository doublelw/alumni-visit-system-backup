# 校友入校登记系统 - 自动部署脚本
# PowerShell脚本，用于自动化部署过程

param(
    [string]$ServerIP = "8.146.210.18",
    [string]$Username = "root",
    [string]$Password = "Sy6787687.",
    [string]$DeployPath = "/var/www/lsalumni"
)

Write-Host "============================================" -ForegroundColor Green
Write-Host "校友入校登记系统 - 自动部署脚本" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Host "服务器配置:" -ForegroundColor Yellow
Write-Host "IP地址: $ServerIP" -ForegroundColor White
Write-Host "用户名: $Username" -ForegroundColor White
Write-Host "部署路径: $DeployPath" -ForegroundColor White
Write-Host ""

# 检查本地部署包
$LocalPath = "D:\Project\校友入校登记\upload_package"
if (-not (Test-Path $LocalPath)) {
    Write-Host "错误: 找不到部署包目录 $LocalPath" -ForegroundColor Red
    Write-Host "请先运行 prepare_upload.py 创建部署包" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 找到本地部署包: $LocalPath" -ForegroundColor Green
Write-Host ""

Write-Host "请选择部署方式:" -ForegroundColor Yellow
Write-Host "1. 手动部署 (推荐)"
Write-Host "2. 尝试自动部署 (需要SSH工具)"
Write-Host ""

$choice = Read-Host "请输入选择 (1 或 2)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "手动部署步骤:" -ForegroundColor Cyan
    Write-Host "1. 使用 SFTP 工具连接到服务器" -ForegroundColor White
    Write-Host "   - 主机: $ServerIP" -ForegroundColor Gray
    Write-Host "   - 用户名: $Username" -ForegroundColor Gray
    Write-Host "   - 密码: $Password" -ForegroundColor Gray
    Write-Host "   - 端口: 22" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. 上传文件到服务器" -ForegroundColor White
    Write-Host "   - 将 $LocalPath 上传到 $DeployPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. SSH连接并运行部署脚本" -ForegroundColor White
    Write-Host "   ssh $Username@$ServerIP" -ForegroundColor Gray
    Write-Host "   cd $DeployPath" -ForegroundColor Gray
    Write-Host "   bash server_setup.sh" -ForegroundColor Gray
    Write-Host "   bash deploy.sh" -ForegroundColor Gray
    Write-Host ""

    # 打开部署指南
    $guidePath = "D:\Project\校友入校登记\MANUAL_DEPLOYMENT_GUIDE.md"
    if (Test-Path $guidePath) {
        Write-Host "正在打开部署指南文档..." -ForegroundColor Green
        Start-Process $guidePath
    }

} elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "尝试自动部署..." -ForegroundColor Cyan
    Write-Host "注意: 这需要系统上有SSH客户端工具" -ForegroundColor Yellow
    Write-Host ""

    # 尝试使用PowerShell SSH
    try {
        Write-Host "测试SSH连接..." -ForegroundColor White
        $sshCommand = "echo 'SSH连接测试成功'"
        $result = ssh $Username@$ServerIP $sshCommand 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ SSH连接成功!" -ForegroundColor Green

            Write-Host "正在检查服务器环境..." -ForegroundColor White
            $checkCmd = "hostname && whoami && pwd"
            ssh $Username@$ServerIP $checkCmd

            Write-Host ""
            Write-Host "准备在服务器上创建部署目录..." -ForegroundColor White
            $mkdirCmd = "mkdir -p $DeployPath && echo '部署目录创建成功'"
            ssh $Username@$ServerIP $mkdirCmd

            Write-Host ""
            Write-Host "现在需要手动上传文件到服务器，然后运行:" -ForegroundColor Yellow
            Write-Host "ssh $Username@$ServerIP" -ForegroundColor Gray
            Write-Host "cd $DeployPath" -ForegroundColor Gray
            Write-Host "bash server_setup.sh" -ForegroundColor Gray
            Write-Host "bash deploy.sh" -ForegroundColor Gray

        } else {
            Write-Host "❌ SSH连接失败" -ForegroundColor Red
            Write-Host "错误信息: $result" -ForegroundColor Red
            Write-Host ""
            Write-Host "请使用手动部署方式" -ForegroundColor Yellow
        }

    } catch {
        Write-Host "❌ SSH连接失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "可能的原因:" -ForegroundColor Yellow
        Write-Host "1. 系统未安装SSH客户端" -ForegroundColor White
        Write-Host "2. 服务器SSH服务未运行" -ForegroundColor White
        Write-Host "3. 网络连接问题" -ForegroundColor White
        Write-Host "4. 认证失败" -ForegroundColor White
        Write-Host ""
        Write-Host "请使用手动部署方式" -ForegroundColor Yellow
    }

} else {
    Write-Host "无效选择，退出脚本" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "部署完成后，您可以通过以下地址访问:" -ForegroundColor Green
Write-Host "https://www.pofeclife.top/lsalumni" -ForegroundColor Cyan
Write-Host "管理员账户: admin / admin123" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")