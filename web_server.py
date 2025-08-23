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

if __name__ == '__main__':
    run_server()
