# -*- coding: utf-8 -*-
"""
TimeLog - 时间记录工具
简化版本，无需复杂模块结构
"""

import click
import json
import os
import sys
from datetime import datetime, date, timedelta
from collections import defaultdict

# 设置 Windows 下的编码
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DATA_FILE = os.path.expanduser("~/.timelog.json")

def load_data():
    """加载时间日志数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"sessions": [], "daily_stats": {}}

def save_data(data):
    """保存时间日志数据"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_current_session(data):
    """获取当前正在进行的会话"""
    for session in reversed(data.get("sessions", [])):
        if session.get("end") is None:
            return session
    return None

def calculate_duration(start_time, end_time):
    """计算时长（分钟）"""
    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)
    return (end - start).total_seconds() / 60

def update_daily_stats(data, session):
    """更新每日统计"""
    if session.get("end") is None:
        return
    
    session_date = datetime.fromisoformat(session["start"]).date().isoformat()
    category = session["category"]
    duration = calculate_duration(session["start"], session["end"])
    
    if "daily_stats" not in data:
        data["daily_stats"] = {}
    
    if session_date not in data["daily_stats"]:
        data["daily_stats"][session_date] = {"study": 0, "game": 0, "other": 0}
    
    data["daily_stats"][session_date][category] += duration

def get_current_stats_with_active(data, target_date=None):
    """获取包含当前正在进行任务的统计数据"""
    if target_date is None:
        target_date = date.today().isoformat()
    
    # 获取已完成任务的统计
    daily_stats = data.get("daily_stats", {})
    current_stats = daily_stats.get(target_date, {"study": 0, "game": 0, "other": 0}).copy()
    
    # 检查是否有正在进行的任务
    current_session = None
    for session in data.get("sessions", []):
        if session.get("end") is None:
            current_session = session
            break
    
    # 如果有正在进行的任务，计算其到当前时间的时长
    if current_session:
        session_start = datetime.fromisoformat(current_session["start"])
        session_date = session_start.date().isoformat()
        
        # 只有当任务是在目标日期开始的才计入该日期
        if session_date == target_date:
            current_duration = (datetime.now() - session_start).total_seconds() / 60
            category = current_session["category"]
            current_stats[category] += current_duration
    
    return current_stats, current_session

@click.group()
def cli():
    """时间记录工具 - 记录学习和游戏时间"""
    pass

@cli.command()
@click.argument("task")
@click.option("--category", "-c", type=click.Choice(['study', 'game', 'other']), 
              default='study', help="任务类别：study(学习), game(游戏), other(其他)")
def start(task, category):
    """开始一个任务
    
    示例:
    timelog start "数学作业" -c study
    timelog start "三角洲行动" -c game
    """
    data = load_data()
    
    # 检查是否有正在进行的任务
    current_session = get_current_session(data)
    if current_session:
        click.echo(f"警告：当前有正在进行的任务 '{current_session['task']}'")
        if click.confirm("是否结束当前任务并开始新任务？"):
            current_session["end"] = datetime.now().isoformat()
            update_daily_stats(data, current_session)
        else:
            return
    
    # 开始新任务
    session = {
        "task": task,
        "category": category,
        "start": datetime.now().isoformat(),
        "end": None
    }
    
    if "sessions" not in data:
        data["sessions"] = []
    
    data["sessions"].append(session)
    save_data(data)
    
    category_name = {"study": "学习", "game": "游戏", "other": "其他"}[category]
    click.echo(f"🎯 开始{category_name}任务: {task}")
    click.echo(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")

@cli.command()
def stop():
    """结束当前任务"""
    data = load_data()
    current_session = get_current_session(data)
    
    if not current_session:
        click.echo("❌ 没有正在进行的任务！")
        return
    
    current_session["end"] = datetime.now().isoformat()
    duration = calculate_duration(current_session["start"], current_session["end"])
    update_daily_stats(data, current_session)
    save_data(data)
    
    category_name = {"study": "学习", "game": "游戏", "other": "其他"}[current_session["category"]]
    click.echo(f"✅ 结束{category_name}任务: {current_session['task']}")
    click.echo(f"⏱️  持续时间: {duration:.1f} 分钟 ({duration/60:.1f} 小时)")

@cli.command()
def status():
    """查看当前状态"""
    data = load_data()
    current_session = get_current_session(data)
    
    if current_session:
        start_time = datetime.fromisoformat(current_session["start"])
        duration = (datetime.now() - start_time).total_seconds() / 60
        category_name = {"study": "学习", "game": "游戏", "other": "其他"}[current_session["category"]]
        
        click.echo(f"🔄 当前正在进行: {current_session['task']} ({category_name})")
        click.echo(f"⏰ 已进行: {duration:.1f} 分钟 ({duration/60:.1f} 小时)")
    else:
        click.echo("😴 当前没有正在进行的任务")

@cli.command()
@click.option("--date", "-d", "date_param", help="查看指定日期 (YYYY-MM-DD)")
@click.option("--days", "-n", default=7, help="查看最近N天")
def stats(date_param, days):
    """查看统计信息"""
    data = load_data()
    
    if date_param:
        # 查看指定日期
        target_date = date_param
        stats_data, current_session = get_current_stats_with_active(data, target_date)
        
        if stats_data["study"] > 0 or stats_data["game"] > 0 or stats_data["other"] > 0:
            click.echo(f"\n📅 {target_date} 的时间统计:")
            click.echo(f"📚 学习: {stats_data['study']:.1f} 分钟 ({stats_data['study']/60:.1f} 小时)")
            click.echo(f"🎮 游戏: {stats_data['game']:.1f} 分钟 ({stats_data['game']/60:.1f} 小时)")
            click.echo(f"📋 其他: {stats_data['other']:.1f} 分钟 ({stats_data['other']/60:.1f} 小时)")
            total = stats_data['study'] + stats_data['game'] + stats_data['other']
            click.echo(f"⏰ 总计: {total:.1f} 分钟 ({total/60:.1f} 小时)")
            
            # 如果有正在进行的任务，特别标注
            if current_session and target_date == date.today().isoformat():
                click.echo(f"\n🔄 正在进行: {current_session['task']} ({current_session['category']})")
        else:
            click.echo(f"❌ {target_date} 没有记录")
    else:
        # 查看最近N天
        today = date.today()
        click.echo(f"\n📊 最近 {days} 天的时间统计:")
        click.echo("=" * 50)
        
        total_study = 0
        total_game = 0
        total_other = 0
        
        for i in range(days):
            day = (today - timedelta(days=i)).isoformat()
            stats_data, current_session = get_current_stats_with_active(data, day)
            
            study_hours = stats_data["study"] / 60
            game_hours = stats_data["game"] / 60
            other_hours = stats_data["other"] / 60
            total_hours = study_hours + game_hours + other_hours
            
            total_study += stats_data["study"]
            total_game += stats_data["game"] 
            total_other += stats_data["other"]
            
            if total_hours > 0:
                status_indicator = " 🔄" if current_session and day == today.isoformat() else ""
                click.echo(f"{day}: 📚{study_hours:.1f}h 🎮{game_hours:.1f}h 📋{other_hours:.1f}h (总计{total_hours:.1f}h){status_indicator}")
            else:
                click.echo(f"{day}: 无记录")
        
        click.echo("=" * 50)
        click.echo(f"总计 - 📚学习: {total_study/60:.1f}h 🎮游戏: {total_game/60:.1f}h 📋其他: {total_other/60:.1f}h")
        
        if total_study + total_game > 0:
            study_ratio = total_study / (total_study + total_game) * 100
            click.echo(f"学习/游戏比例: {study_ratio:.1f}% / {100-study_ratio:.1f}%")

@cli.command()
@click.option("--days", "-n", default=30, help="查看最近N天")
def log(days):
    """查看详细的任务记录"""
    data = load_data()
    sessions = data.get("sessions", [])
    
    click.echo(f"\n📝 最近 {days} 天的任务记录:")
    click.echo("=" * 80)
    
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_sessions = [s for s in sessions 
                      if datetime.fromisoformat(s["start"]) >= cutoff_date]
    
    if not recent_sessions:
        click.echo("📭 没有找到记录")
        return
    
    for session in sorted(recent_sessions, key=lambda x: x["start"], reverse=True):
        start_time = datetime.fromisoformat(session["start"])
        category_emoji = {"study": "📚", "game": "🎮", "other": "📋"}[session["category"]]
        
        if session.get("end"):
            end_time = datetime.fromisoformat(session["end"])
            duration = calculate_duration(session["start"], session["end"])
            status = f"✅ {duration:.1f}分钟"
        else:
            duration = (datetime.now() - start_time).total_seconds() / 60
            status = f"🔄 进行中 {duration:.1f}分钟"
        
        click.echo(f"{category_emoji} {session['task']}")
        click.echo(f"   {start_time.strftime('%Y-%m-%d %H:%M')} - {status}")
        click.echo()

@cli.command()
def clear():
    """清除所有数据"""
    if click.confirm("⚠️  确定要清除所有时间记录数据吗？此操作不可恢复！"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        click.echo("🗑️  所有数据已清除")
    else:
        click.echo("❌ 操作已取消")

@cli.command()
@click.option("--days", "-n", default=7, help="显示最近N天")
def chart(days):
    """生成简单的文本图表"""
    data = load_data()
    daily_stats = data.get("daily_stats", {})
    
    click.echo(f"\n📈 最近 {days} 天的时间图表:")
    click.echo("=" * 60)
    
    today = date.today()
    max_hours = 0
    
    # 收集数据并找出最大值
    chart_data = []
    for i in range(days-1, -1, -1):
        day = (today - timedelta(days=i)).isoformat()
        stats = daily_stats.get(day, {"study": 0, "game": 0, "other": 0})
        
        study_hours = stats["study"] / 60
        game_hours = stats["game"] / 60
        other_hours = stats["other"] / 60
        total_hours = study_hours + game_hours + other_hours
        
        chart_data.append({
            "date": day,
            "study": study_hours,
            "game": game_hours,
            "other": other_hours,
            "total": total_hours
        })
        
        max_hours = max(max_hours, total_hours)
    
    # 绘制文本图表
    if max_hours == 0:
        click.echo("📭 没有数据可显示")
        return
    
    scale = 40 / max_hours if max_hours > 0 else 1
    
    for data_point in chart_data:
        date_str = data_point["date"][-5:]  # 只显示 MM-DD
        study_bar = "█" * int(data_point["study"] * scale)
        game_bar = "▓" * int(data_point["game"] * scale)
        other_bar = "░" * int(data_point["other"] * scale)
        
        total_hours = data_point["total"]
        
        if total_hours > 0:
            click.echo(f"{date_str} |{study_bar}{game_bar}{other_bar} {total_hours:.1f}h")
        else:
            click.echo(f"{date_str} | (无记录)")
    
    click.echo("=" * 60)
    click.echo("图例: █学习 ▓游戏 ░其他")
    
    # 显示总结
    total_study = sum(d["study"] for d in chart_data)
    total_game = sum(d["game"] for d in chart_data)
    total_other = sum(d["other"] for d in chart_data)
    
    click.echo(f"\n📊 {days}天总计:")
    click.echo(f"📚 学习: {total_study:.1f} 小时")
    click.echo(f"🎮 游戏: {total_game:.1f} 小时")
    click.echo(f"📋 其他: {total_other:.1f} 小时")
    
    if total_study + total_game > 0:
        study_ratio = total_study / (total_study + total_game) * 100
        click.echo(f"学习/游戏比例: {study_ratio:.1f}% / {100-study_ratio:.1f}%")

@cli.command()
@click.option("--port", "-p", default=5000, help="Web服务器端口")
@click.option("--no-browser", is_flag=True, help="不自动打开浏览器")
def web(port, no_browser):
    """启动Web界面服务器"""
    try:
        # 检查Flask是否已安装
        import flask
    except ImportError:
        click.echo("❌ 需要安装 Flask 才能使用Web界面")
        click.echo("请运行: pip install flask")
        return
    
    try:
        # 直接导入web_server模块
        try:
            import web_server
        except ImportError:
            # 如果直接导入失败，尝试动态导入
            import importlib.util
            import sys
            
            # 检查是否在打包环境中
            if getattr(sys, 'frozen', False):
                # 打包环境：从临时目录查找
                application_path = sys._MEIPASS
                web_server_path = os.path.join(application_path, "web_server.py")
            else:
                # 开发环境：从脚本目录查找
                script_dir = os.path.dirname(os.path.abspath(__file__))
                web_server_path = os.path.join(script_dir, "web_server.py")
            
            if not os.path.exists(web_server_path):
                click.echo(f"❌ 找不到web_server.py文件: {web_server_path}")
                return
            
            # 动态导入web_server模块
            spec = importlib.util.spec_from_file_location("web_server", web_server_path)
            web_server = importlib.util.module_from_spec(spec)
            sys.modules["web_server"] = web_server
            spec.loader.exec_module(web_server)
        
        # 启动服务器
        click.echo("🚀 启动TimeLog Web界面...")
        web_server.run_server(port=port, debug=False, open_browser_flag=not no_browser)
        
    except KeyboardInterrupt:
        click.echo("\n👋 Web服务器已停止")
    except Exception as e:
        click.echo(f"❌ 启动Web服务器失败: {str(e)}")
        click.echo("请检查端口是否被占用或重试")

if __name__ == "__main__":
    cli()
