# -*- coding: utf-8 -*-
"""
TimeLog Web Server
提供网页界面管理时间记录
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import json
import os
from datetime import datetime, date, timedelta
from collections import defaultdict
import webbrowser
import threading
import time
from io import BytesIO

# 复用 timelog_simple.py 中的数据处理函数
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
    current_session = get_current_session(data)
    
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

def get_recent_stats(days=7):
    """获取最近N天的统计数据"""
    data = load_data()
    today = date.today()
    
    # 收集每日统计
    daily_data = {}
    total_study = 0
    total_game = 0
    total_other = 0
    max_daily_study = 0
    active_days = 0
    
    for i in range(days-1, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.isoformat()
        
        # 使用包含当前任务的统计
        day_stats, current_session = get_current_stats_with_active(data, day_str)
        
        # 转换为小时
        study_hours = round(day_stats["study"] / 60, 1)
        game_hours = round(day_stats["game"] / 60, 1)
        other_hours = round(day_stats["other"] / 60, 1)
        
        # 累计统计
        total_study += study_hours
        total_game += game_hours
        total_other += other_hours
        
        # 最大单日学习时间
        max_daily_study = max(max_daily_study, study_hours)
        
        # 活跃天数（有任何活动的天数）
        if study_hours + game_hours + other_hours > 0:
            active_days += 1
        
        # 格式化日期显示
        if i == 0:
            date_display = "今天"
        elif i == 1:
            date_display = "昨天"
        else:
            date_display = day.strftime("%m-%d")
        
        daily_data[date_display] = {
            "study": study_hours,
            "game": game_hours,
            "other": other_hours
        }
    
    return {
        "daily_stats": daily_data,
        "total_study": total_study,
        "total_game": total_game,
        "total_other": total_other,
        "max_daily_study": max_daily_study,
        "active_days": active_days
    }

# 创建 Flask 应用
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/')
def index():
    """首页仪表板"""
    data = load_data()
    current_session = get_current_session(data)
    
    # 今日统计（包含当前正在进行的任务）
    today = date.today().isoformat()
    today_stats_raw, _ = get_current_stats_with_active(data, today)
    
    today_stats = {
        "study": round(today_stats_raw["study"] / 60, 1),
        "game": round(today_stats_raw["game"] / 60, 1),
        "other": round(today_stats_raw["other"] / 60, 1)
    }
    
    # 当前会话信息
    current_info = None
    if current_session:
        start_time = datetime.fromisoformat(current_session["start"])
        duration = (datetime.now() - start_time).total_seconds() / 60
        current_info = {
            "task": current_session["task"],
            "category": current_session["category"],
            "duration": round(duration, 1),
            "start_time": start_time.strftime("%H:%M")
        }
    
    return render_template('index.html', 
                         current_session=current_info,
                         today_stats=today_stats,
                         current_date=datetime.now().strftime("%Y年%m月%d日"))

@app.route('/tasks')
def tasks():
    """任务管理页面"""
    data = load_data()
    current_session = get_current_session(data)
    
    current_info = None
    if current_session:
        start_time = datetime.fromisoformat(current_session["start"])
        duration = (datetime.now() - start_time).total_seconds() / 60
        current_info = {
            "task": current_session["task"],
            "category": current_session["category"],
            "duration": round(duration, 1),
            "start_time": start_time.strftime("%H:%M")
        }
    
    return render_template('tasks.html', current_session=current_info)

@app.route('/stats')
def stats():
    """统计分析页面"""
    # 从URL参数获取天数，默认为今天
    days_param = request.args.get('days', 'today')
    
    # 处理"今天"选项
    if days_param == 'today':
        days = 1
        selected_days = 'today'
    else:
        days = int(days_param)
        selected_days = days
        # 限制天数范围
        if days not in [7, 14, 30, 90]:
            days = 7
            selected_days = 7
    
    recent_stats = get_recent_stats(days)
    
    # 如果是"今天"选项，还需要获取7天的趋势数据用于图表
    trend_stats = None
    if selected_days == 'today':
        trend_stats = get_recent_stats(7)
    
    return render_template('stats.html', 
                         recent_stats=recent_stats, 
                         selected_days=selected_days,
                         trend_stats=trend_stats)

@app.route('/history')
def history():
    """历史记录页面"""
    data = load_data()
    sessions = data.get("sessions", [])
    
    # 获取最近30天的会话，同时保留原始索引
    cutoff_date = datetime.now() - timedelta(days=30)
    recent_sessions_with_index = []
    
    for i, session in enumerate(sessions):
        if datetime.fromisoformat(session["start"]) >= cutoff_date:
            recent_sessions_with_index.append((i, session))
    
    # 按时间排序（最新的在前）
    recent_sessions_with_index.sort(key=lambda x: x[1]["start"], reverse=True)
    
    # 处理会话数据
    processed_sessions = []
    for original_index, session in recent_sessions_with_index:
        start_time = datetime.fromisoformat(session["start"])
        
        if session.get("end"):
            end_time = datetime.fromisoformat(session["end"])
            duration = calculate_duration(session["start"], session["end"])
            end_time_str = end_time.strftime("%H:%M")
            end_date_str = end_time.strftime("%Y-%m-%d")
            duration_hours = duration / 60.0  # 转换为小时
        else:
            duration = (datetime.now() - start_time).total_seconds() / 60
            end_time_str = None
            end_date_str = None
            duration_hours = duration / 60.0  # 转换为小时
        
        processed_sessions.append({
            "original_index": original_index,  # 保留原始索引
            "task": session["task"],
            "category": session["category"],
            "date": start_time.strftime("%Y-%m-%d"),
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time_str,
            "end_date": end_date_str,
            "duration_hours": round(duration_hours, 1) if duration_hours > 0 else None
        })
    
    return render_template('history.html', sessions=processed_sessions)

@app.route('/api/start_task', methods=['POST'])
def start_task():
    """开始任务 API"""
    task_name = request.json.get('task')
    category = request.json.get('category', 'study')
    
    if not task_name:
        return jsonify({"success": False, "message": "任务名不能为空"})
    
    data = load_data()
    
    # 检查是否有正在进行的任务
    current_session = get_current_session(data)
    if current_session:
        current_session["end"] = datetime.now().isoformat()
        update_daily_stats(data, current_session)
    
    # 开始新任务
    session = {
        "task": task_name,
        "category": category,
        "start": datetime.now().isoformat(),
        "end": None
    }
    
    if "sessions" not in data:
        data["sessions"] = []
    
    data["sessions"].append(session)
    save_data(data)
    
    return jsonify({"success": True, "message": f"已开始{category}任务: {task_name}"})

@app.route('/api/stop_task', methods=['POST'])
def stop_task():
    """停止任务 API"""
    data = load_data()
    current_session = get_current_session(data)
    
    if not current_session:
        return jsonify({"success": False, "message": "没有正在进行的任务"})
    
    current_session["end"] = datetime.now().isoformat()
    duration = calculate_duration(current_session["start"], current_session["end"])
    update_daily_stats(data, current_session)
    save_data(data)
    
    return jsonify({
        "success": True, 
        "message": f"已结束任务: {current_session['task']}",
        "duration": round(duration, 1)
    })

@app.route('/api/current_status')
def current_status():
    """获取当前状态 API"""
    data = load_data()
    current_session = get_current_session(data)
    
    if current_session:
        start_time = datetime.fromisoformat(current_session["start"])
        duration = (datetime.now() - start_time).total_seconds() / 60
        return jsonify({
            "active": True,
            "task": current_session["task"],
            "category": current_session["category"],
            "duration": round(duration, 1),
            "start_time": start_time.strftime("%H:%M")
        })
    else:
        return jsonify({"active": False})

@app.route('/api/stats_data')
def stats_data():
    """获取统计数据 API"""
    days_param = request.args.get('days', 'today')
    
    # 处理"今天"选项
    if days_param == 'today':
        days = 1
    else:
        days = int(days_param)
    
    stats = get_recent_stats(days)
    return jsonify(stats)

@app.route('/api/get_session/<int:session_id>')
def get_session(session_id):
    """获取单个任务详情"""
    data = load_data()
    sessions = data.get("sessions", [])
    
    if 0 <= session_id < len(sessions):
        session = sessions[session_id]
        return jsonify({
            "success": True,
            "session": {
                "id": session_id,
                "task": session["task"],
                "category": session["category"],
                "start": session["start"],
                "end": session.get("end"),
                "start_date": session["start"][:10],
                "start_time": session["start"][11:16],
                "end_date": session["end"][:10] if session.get("end") else "",
                "end_time": session["end"][11:16] if session.get("end") else ""
            }
        })
    else:
        return jsonify({"success": False, "message": "任务不存在"})

@app.route('/api/update_session/<int:session_id>', methods=['POST'])
def update_session(session_id):
    """更新任务信息"""
    data = load_data()
    sessions = data.get("sessions", [])
    
    if not (0 <= session_id < len(sessions)):
        return jsonify({"success": False, "message": "任务不存在"})
    
    session = sessions[session_id]
    old_session = session.copy()
    
    # 获取更新数据
    update_data = request.json
    
    try:
        # 更新任务名称
        if "task" in update_data:
            session["task"] = update_data["task"]
        
        # 更新类别
        if "category" in update_data:
            if update_data["category"] not in ["study", "game", "other"]:
                return jsonify({"success": False, "message": "无效的任务类别"})
            session["category"] = update_data["category"]
        
        # 更新时间
        if "start_date" in update_data and "start_time" in update_data:
            new_start = f"{update_data['start_date']}T{update_data['start_time']}:00"
            # 验证时间格式
            datetime.fromisoformat(new_start)
            session["start"] = new_start
        
        if "end_date" in update_data and "end_time" in update_data and update_data["end_time"]:
            # 如果提供了结束日期，使用提供的日期；否则使用开始日期
            end_date = update_data["end_date"] if update_data["end_date"] else session["start"][:10]
            new_end = f"{end_date}T{update_data['end_time']}:00"
            # 验证时间格式
            datetime.fromisoformat(new_end)
            session["end"] = new_end
        elif "end_time" in update_data and update_data["end_time"]:
            # 兼容旧版本：如果只提供了结束时间，使用开始日期
            start_date = session["start"][:10]
            new_end = f"{start_date}T{update_data['end_time']}:00"
            # 验证时间格式
            datetime.fromisoformat(new_end)
            session["end"] = new_end
        elif "end_time" in update_data and not update_data["end_time"]:
            # 清除结束时间（设为正在进行）
            session.pop("end", None)
        
        # 验证时间逻辑
        if session.get("end"):
            start_dt = datetime.fromisoformat(session["start"])
            end_dt = datetime.fromisoformat(session["end"])
            if end_dt <= start_dt:
                return jsonify({"success": False, "message": "结束时间必须晚于开始时间"})
        
        # 更新每日统计
        # 首先移除旧的统计
        if old_session.get("end"):
            old_start = datetime.fromisoformat(old_session["start"])
            old_end = datetime.fromisoformat(old_session["end"])
            old_date = old_start.date().isoformat()
            old_duration = (old_end - old_start).total_seconds() / 60
            old_category = old_session["category"]
            
            if "daily_stats" in data and old_date in data["daily_stats"]:
                data["daily_stats"][old_date][old_category] -= old_duration
                if data["daily_stats"][old_date][old_category] < 0:
                    data["daily_stats"][old_date][old_category] = 0
        
        # 添加新的统计
        if session.get("end"):
            update_daily_stats(data, session)
        
        save_data(data)
        
        return jsonify({
            "success": True,
            "message": "任务更新成功",
            "session": {
                "id": session_id,
                "task": session["task"],
                "category": session["category"],
                "start": session["start"],
                "end": session.get("end")
            }
        })
        
    except ValueError as e:
        return jsonify({"success": False, "message": f"时间格式错误: {str(e)}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"更新失败: {str(e)}"})

@app.route('/api/delete_session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除任务"""
    data = load_data()
    sessions = data.get("sessions", [])
    
    if not (0 <= session_id < len(sessions)):
        return jsonify({"success": False, "message": "任务不存在"})
    
    session = sessions[session_id]
    
    # 从每日统计中移除
    if session.get("end"):
        start_time = datetime.fromisoformat(session["start"])
        session_date = start_time.date().isoformat()
        duration = calculate_duration(session["start"], session["end"])
        category = session["category"]
        
        if "daily_stats" in data and session_date in data["daily_stats"]:
            data["daily_stats"][session_date][category] -= duration
            if data["daily_stats"][session_date][category] < 0:
                data["daily_stats"][session_date][category] = 0
    
    # 删除任务
    sessions.pop(session_id)
    save_data(data)
    
    return jsonify({"success": True, "message": "任务删除成功"})

@app.route('/api/create_session', methods=['POST'])
def create_session():
    """创建新任务"""
    data = load_data()
    create_data = request.json
    
    try:
        # 验证必需字段
        required_fields = ["task", "category", "start_date", "start_time"]
        for field in required_fields:
            if field not in create_data or not create_data[field]:
                return jsonify({"success": False, "message": f"缺少必需字段: {field}"})
        
        # 验证类别
        if create_data["category"] not in ["study", "game", "other"]:
            return jsonify({"success": False, "message": "无效的任务类别"})
        
        # 构建时间
        start_datetime = f"{create_data['start_date']}T{create_data['start_time']}:00"
        end_datetime = None
        
        if create_data.get("end_time"):
            # 如果提供了结束日期，使用提供的日期；否则使用开始日期
            end_date = create_data.get("end_date", create_data["start_date"])
            end_datetime = f"{end_date}T{create_data['end_time']}:00"
        
        # 验证时间格式
        start_dt = datetime.fromisoformat(start_datetime)
        if end_datetime:
            end_dt = datetime.fromisoformat(end_datetime)
            if end_dt <= start_dt:
                return jsonify({"success": False, "message": "结束时间必须晚于开始时间"})
        
        # 创建新任务
        new_session = {
            "task": create_data["task"],
            "category": create_data["category"],
            "start": start_datetime
        }
        
        if end_datetime:
            new_session["end"] = end_datetime
        
        # 添加到会话列表
        if "sessions" not in data:
            data["sessions"] = []
        data["sessions"].append(new_session)
        
        # 更新每日统计
        if end_datetime:
            update_daily_stats(data, new_session)
        
        save_data(data)
        
        return jsonify({
            "success": True,
            "message": "任务创建成功",
            "session": new_session
        })
        
    except ValueError as e:
        return jsonify({"success": False, "message": f"时间格式错误: {str(e)}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"创建失败: {str(e)}"})

@app.route('/api/clear_data', methods=['POST'])
def clear_data():
    """清除所有数据 API"""
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    return jsonify({"success": True, "message": "所有数据已清除"})

def open_browser():
    """延迟打开浏览器"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

def run_server(port=5000, debug=False, open_browser_flag=True):
    """运行服务器"""
    if open_browser_flag:
        threading.Thread(target=open_browser, daemon=True).start()
    
    print(f"🌐 TimeLog Web 服务器启动中...")
    print(f"📱 访问地址: http://localhost:{port}")
    print(f"⏹️  按 Ctrl+C 停止服务器")
    
    app.run(host='localhost', port=port, debug=debug)

@app.route('/api/export_data')
def export_data():
    """导出历史数据API"""
    format_type = request.args.get('format', 'csv')
    encoding = request.args.get('encoding', 'utf-8')
    
    data = load_data()
    sessions = data.get("sessions", [])
    
    # 获取最近30天的会话
    cutoff_date = datetime.now() - timedelta(days=30)
    recent_sessions = [s for s in sessions 
                      if datetime.fromisoformat(s["start"]) >= cutoff_date]
    
    # 按时间排序（最新的在前）
    recent_sessions.sort(key=lambda x: x["start"], reverse=True)
    
    if format_type == 'json':
        # JSON格式
        export_data = {
            "exportDate": datetime.now().isoformat(),
            "totalRecords": len(recent_sessions),
            "sessions": recent_sessions
        }
        
        response = jsonify(export_data)
        response.headers['Content-Disposition'] = f'attachment; filename=timelog_export_{datetime.now().strftime("%Y%m%d")}.json'
        return response
        
    else:
        # CSV格式
        csv_lines = ["开始日期,开始时间,结束日期,结束时间,任务,类别,时长(小时)"]
        
        for session in recent_sessions:
            start_time = datetime.fromisoformat(session["start"])
            start_date = start_time.strftime("%Y-%m-%d")
            start_time_str = start_time.strftime("%H:%M")
            
            if session.get("end"):
                end_time = datetime.fromisoformat(session["end"])
                end_date = end_time.strftime("%Y-%m-%d")
                end_time_str = end_time.strftime("%H:%M")
                duration = calculate_duration(session["start"], session["end"])
                duration_hours = round(duration / 60.0, 1)
            else:
                end_date = ""
                end_time_str = ""
                duration_hours = ""
            
            # 处理类别显示
            category_map = {
                'study': '📚 学习',
                'game': '🎮 游戏', 
                'other': '📋 其他'
            }
            category_display = category_map.get(session["category"], session["category"])
            
            csv_line = f'"{start_date}","{start_time_str}","{end_date}","{end_time_str}","{session["task"]}","{category_display}","{duration_hours}"'
            csv_lines.append(csv_line)
        
        csv_content = '\n'.join(csv_lines)
        
        # 根据编码创建响应
        if encoding == 'gbk':
            try:
                csv_bytes = csv_content.encode('gbk')
                response = Response(csv_bytes, mimetype='text/csv; charset=gbk')
            except UnicodeEncodeError:
                # 如果GBK编码失败，使用UTF-8
                csv_bytes = ('\ufeff' + csv_content).encode('utf-8')
                response = Response(csv_bytes, mimetype='text/csv; charset=utf-8')
        else:
            # UTF-8编码，添加BOM
            csv_bytes = ('\ufeff' + csv_content).encode('utf-8')
            response = Response(csv_bytes, mimetype='text/csv; charset=utf-8')
        
        filename = f'timelog_export_{datetime.now().strftime("%Y%m%d")}.csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response

@app.route('/api/export_pdf')
def export_pdf():
    """导出统计数据为PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch, mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as ReportLabImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.graphics.shapes import Drawing, Circle, Rect, String
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics import renderPDF
        import matplotlib
        matplotlib.use('Agg')  # 使用非交互式后端
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        from io import BytesIO
        import base64
        
        # 注册中文字体
        try:
            # Windows 系统字体路径
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc"   # 宋体
            ]
            
            chinese_font = 'Helvetica'  # 默认字体
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        chinese_font = 'ChineseFont'
                        break
                    except:
                        continue
        except:
            chinese_font = 'Helvetica'
        
        # 设置matplotlib中文字体
        try:
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass
        
    except ImportError as e:
        missing_libs = []
        if 'reportlab' in str(e):
            missing_libs.append('reportlab')
        if 'matplotlib' in str(e):
            missing_libs.append('matplotlib')
        return jsonify({"success": False, "message": f"PDF功能需要安装库: pip install {' '.join(missing_libs)}"})
    
    # 获取参数
    days_param = request.args.get('days', 'today')
    
    # 处理"今天"选项
    if days_param == 'today':
        days = 1
        selected_days = 'today'
        period_name = "今天"
    else:
        days = int(days_param)
        selected_days = days
        period_name = f"最近{days}天"
    
    # 获取统计数据
    recent_stats = get_recent_stats(days)
    
    # 获取详细任务数据
    data = load_data()
    sessions = data.get("sessions", [])
    cutoff_date = datetime.now() - timedelta(days=days if selected_days != 'today' else 1)
    
    if selected_days == 'today':
        # 今天的任务
        today_date = date.today()
        detailed_sessions = [s for s in sessions 
                           if datetime.fromisoformat(s["start"]).date() == today_date]
    else:
        # 指定天数内的任务
        detailed_sessions = [s for s in sessions 
                           if datetime.fromisoformat(s["start"]) >= cutoff_date]
    
    # 按时间排序
    detailed_sessions.sort(key=lambda x: x["start"], reverse=True)
    
    # 创建PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=50, 
        topMargin=50, 
        bottomMargin=50
    )
    
    # 自定义样式
    styles = getSampleStyleSheet()
    
    # 标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName=chinese_font,
        fontSize=28,
        spaceAfter=30,
        alignment=1,  # 居中
        textColor=colors.HexColor('#2C3E50'),
        borderWidth=1,
        borderColor=colors.HexColor('#3498DB'),
        borderRadius=5,
        backColor=colors.HexColor('#ECF0F1'),
        borderPadding=20
    )
    
    # 副标题样式
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=14,
        spaceAfter=20,
        alignment=1,
        textColor=colors.HexColor('#7F8C8D')
    )
    
    # 章节标题样式
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=18,
        spaceAfter=15,
        spaceBefore=20,
        textColor=colors.HexColor('#2980B9'),
        borderWidth=0,
        borderColor=colors.HexColor('#3498DB'),
        backColor=colors.HexColor('#F8F9FA'),
        leftIndent=10,
        borderPadding=8
    )
    
    # 正文样式
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=11,
        spaceAfter=8,
        leading=16
    )
    
    # 重点文本样式
    highlight_style = ParagraphStyle(
        'Highlight',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=12,
        textColor=colors.HexColor('#E74C3C'),
        spaceAfter=6
    )
    
    # 构建PDF内容
    story = []
    
    # 封面
    story.append(Spacer(1, 50))
    story.append(Paragraph("TimeLog 统计报告", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"统计周期：{period_name} | 生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}", subtitle_style))
    story.append(Spacer(1, 60))
    
    # 创建时间分布饼图
    total_time = recent_stats['total_study'] + recent_stats['total_game'] + recent_stats['total_other']
    if total_time > 0:
        # 添加饼图标题
        story.append(Paragraph("时间分布统计", heading_style))
        story.append(Spacer(1, 15))
        
        fig, ax = plt.subplots(figsize=(10, 10))  # 增大figure尺寸
        # 调整子图位置，为标题留更多空间
        plt.subplots_adjust(top=0.85, bottom=0.15, left=0.15, right=0.85)
        
        sizes = [recent_stats['total_study'], recent_stats['total_game'], recent_stats['total_other']]
        labels = ['学习', '游戏', '其他']
        colors_pie = ['#3498DB', '#E74C3C', '#F39C12']
        
        # 只显示非零的部分
        non_zero_data = [(size, label, color) for size, label, color in zip(sizes, labels, colors_pie) if size > 0]
        if non_zero_data:
            sizes_nz, labels_nz, colors_nz = zip(*non_zero_data)
            
            wedges, texts, autotexts = ax.pie(sizes_nz, labels=labels_nz, colors=colors_nz, 
                                             autopct='%1.1f%%', startangle=90,
                                             textprops={'fontsize': 28})  # 进一步增大标签字体
            ax.set_title(f'{period_name}时间分布', fontsize=32, fontweight='bold', pad=40)  # 进一步增大标题字体
            ax.set_aspect('equal')  # 确保饼图为正圆
            
            # 美化饼图 - 进一步增大所有字体
            for text in texts:
                text.set_fontsize(26)  # 进一步增大标签字体
                text.set_fontweight('bold')
                
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(24)  # 进一步增大百分比字体
        
        # 不使用tight_layout，手动控制布局
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches=None,  # 使用None而不是tight
                   facecolor='white', edgecolor='none')  # 确保背景和边缘设置
        img_buffer.seek(0)
        plt.close()
        
        # 将图片添加到PDF，调整合适尺寸
        img_size = 400  # 稍微缩小饼图尺寸
        story.append(ReportLabImage(img_buffer, width=img_size, height=img_size))
        story.append(Spacer(1, 30))
    
    # 每日统计图表
    if recent_stats['daily_stats']:
        story.append(Paragraph("每日时间趋势", heading_style))
        story.append(Spacer(1, 15))
        
        # 创建每日统计柱状图
        fig, ax = plt.subplots(figsize=(12, 8))  # 增大纵向尺寸从6到8
        
        # 准备数据
        dates = list(recent_stats['daily_stats'].keys())
        study_hours = [recent_stats['daily_stats'][date]['study'] for date in dates]
        game_hours = [recent_stats['daily_stats'][date]['game'] for date in dates]
        other_hours = [recent_stats['daily_stats'][date]['other'] for date in dates]
        
        # 设置柱状图
        x = range(len(dates))
        width = 0.6
        
        # 堆叠柱状图
        bars1 = ax.bar(x, study_hours, width, label='学习', color='#3498DB', alpha=0.8)
        bars2 = ax.bar(x, game_hours, width, bottom=study_hours, label='游戏', color='#E74C3C', alpha=0.8)
        bars3 = ax.bar(x, other_hours, width, bottom=[i+j for i,j in zip(study_hours, game_hours)], 
                      label='其他', color='#F39C12', alpha=0.8)
        
        # 设置标签和标题
        ax.set_xlabel('日期', fontsize=18, fontweight='bold')  # 增大X轴标签字体
        ax.set_ylabel('时间(小时)', fontsize=18, fontweight='bold')  # 增大Y轴标签字体
        ax.set_title('每日时间分布趋势', fontsize=22, fontweight='bold', pad=25)  # 增大标题字体
        ax.set_xticks(x)
        ax.set_xticklabels(dates, rotation=45 if len(dates) > 7 else 0, fontsize=16)  # 增大X轴刻度字体
        ax.legend(fontsize=16)  # 增大图例字体
        
        # 设置Y轴刻度字体
        ax.tick_params(axis='y', labelsize=14)
        
        # 添加数值标签
        for i, (study, game, other) in enumerate(zip(study_hours, game_hours, other_hours)):
            total = study + game + other
            if total > 0:
                ax.text(i, total + 0.1, f'{total:.1f}h', ha='center', va='bottom', 
                       fontweight='bold', fontsize=14)  # 增大数值标签字体
        
        # 美化图表
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, max([sum([s, g, o]) for s, g, o in zip(study_hours, game_hours, other_hours)]) * 1.1)
        
        plt.tight_layout()
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # 将图片添加到PDF，增大纵向尺寸
        story.append(ReportLabImage(img_buffer, width=500, height=333))  # 增大高度，保持12:8的比例
        story.append(Spacer(1, 20))
    
    # 详细任务记录
    if detailed_sessions:
        story.append(Paragraph("详细任务记录", heading_style))
        story.append(Spacer(1, 15))
        
        task_data = [['开始时间', '结束时间', '任务名称', '类别', '时长', '状态']]
        
        for session in detailed_sessions[:20]:  # 只显示最近20个任务
            start_time = datetime.fromisoformat(session["start"])
            category_map = {'study': '学习', 'game': '游戏', 'other': '其他'}
            category_display = category_map.get(session["category"], session["category"])
            
            if session.get("end"):
                end_time = datetime.fromisoformat(session["end"])
                duration = calculate_duration(session["start"], session["end"])
                status = "已完成"
                end_time_str = end_time.strftime("%H:%M")
                duration_str = f"{duration:.0f}分钟"
            else:
                duration = (datetime.now() - start_time).total_seconds() / 60
                status = "进行中"
                end_time_str = "-"
                duration_str = f"{duration:.0f}分钟"
            
            # 任务名称截取（避免过长）
            task_name = session["task"]
            if len(task_name) > 15:
                task_name = task_name[:12] + "..."
            
            task_data.append([
                start_time.strftime("%m-%d %H:%M"),
                end_time_str,
                task_name,
                category_display,
                duration_str,
                status
            ])
        
        task_table = Table(task_data, colWidths=[80, 70, 110, 70, 70, 80])  # 稍微增大列宽
        task_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D35400')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 14),  # 增大表头字体
            ('FONTSIZE', (0, 1), (-1, -1), 12),  # 增大内容字体
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),  # 增大表头底部间距
            ('TOPPADDING', (0, 0), (-1, 0), 12),  # 增加表头顶部间距
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),  # 增加内容行底部间距
            ('TOPPADDING', (0, 1), (-1, -1), 10),  # 增加内容行顶部间距
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FDF2E9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FDF2E9')])
        ]))
        
        story.append(task_table)
        
        if len(detailed_sessions) > 20:
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"... 还有 {len(detailed_sessions) - 20} 个任务记录", normal_style))
    
    # 页脚信息
    story.append(Spacer(1, 30))
    story.append(Paragraph("───────────────────────────────────────", subtitle_style))
    story.append(Paragraph("本报告由 TimeLog 自动生成 | 持续改进，追求卓越", subtitle_style))
    
    # 生成PDF
    doc.build(story)
    buffer.seek(0)
    
    # 返回PDF文件
    if selected_days == 'today':
        filename = f'timelog_report_today_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    else:
        filename = f'timelog_report_{days}days_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    
    response = Response(buffer.getvalue(), mimetype='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

if __name__ == '__main__':
    run_server()
