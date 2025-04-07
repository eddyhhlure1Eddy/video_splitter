# -*- coding: utf-8 -*-
import os
import threading
import time
import subprocess
import shlex
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np
from moviepy.editor import VideoFileClip

# 设置主题和外观
ctk.set_appearance_mode("System")  # 系统主题（跟随系统）
ctk.set_default_color_theme("blue")  # 蓝色主题

class VideoSplitterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.title("视频分割工具 (FFmpeg版)")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # 初始化变量
        self.video_files = []
        self.output_directory = ""
        self.is_processing = False
        self.segment_duration = 3.0  # 默认片段时长为3秒
        
        # 创建UI
        self.create_ui()
        
    def create_ui(self):
        # 创建左右面板
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=5)
        self.grid_rowconfigure(0, weight=1)
        
        # 左侧控制面板
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # 右侧文件列表和日志面板
        self.display_frame = ctk.CTkFrame(self)
        self.display_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # 设置左侧控制面板
        self.setup_control_panel()
        
        # 设置右侧文件列表和日志面板
        self.setup_display_panel()
    
    def setup_control_panel(self):
        # 控制面板布局
        self.control_frame.grid_columnconfigure(0, weight=1)
        
        # 标题
        title_label = ctk.CTkLabel(
            self.control_frame, 
            text="视频分割工具 (FFmpeg版)", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # 描述
        desc_label = ctk.CTkLabel(
            self.control_frame,
            text="高效将长视频分割成短片段",
            font=ctk.CTkFont(size=14)
        )
        desc_label.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # 分割线
        separator = ctk.CTkFrame(self.control_frame, height=2, width=200)
        separator.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # 输入视频选择
        input_label = ctk.CTkLabel(
            self.control_frame,
            text="输入视频:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        input_label.grid(row=3, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.input_button = ctk.CTkButton(
            self.control_frame,
            text="选择视频文件",
            command=self.select_input_files
        )
        self.input_button.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # 输出目录选择
        output_label = ctk.CTkLabel(
            self.control_frame,
            text="输出目录:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        output_label.grid(row=5, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.output_button = ctk.CTkButton(
            self.control_frame,
            text="选择输出目录",
            command=self.select_output_directory
        )
        self.output_button.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # 片段长度设置
        segment_label = ctk.CTkLabel(
            self.control_frame,
            text="片段长度 (秒):",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        segment_label.grid(row=7, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.segment_var = ctk.DoubleVar(value=3.0)
        
        segment_slider = ctk.CTkSlider(
            self.control_frame,
            from_=1.0,
            to=10.0,
            number_of_steps=90,
            variable=self.segment_var,
            command=self.update_segment_value
        )
        segment_slider.grid(row=8, column=0, padx=20, pady=(0, 0), sticky="ew")
        
        self.segment_value_label = ctk.CTkLabel(
            self.control_frame,
            text=f"{self.segment_var.get():.1f} 秒",
            font=ctk.CTkFont(size=12)
        )
        self.segment_value_label.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="e")
        
        # FFmpeg高级选项
        options_label = ctk.CTkLabel(
            self.control_frame,
            text="FFmpeg选项:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        options_label.grid(row=10, column=0, padx=20, pady=(10, 5), sticky="w")
        
        # 编码质量选择
        self.quality_var = ctk.StringVar(value="中等")
        quality_label = ctk.CTkLabel(
            self.control_frame,
            text="编码质量:",
        )
        quality_label.grid(row=11, column=0, padx=20, pady=(5, 0), sticky="w")
        
        quality_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        quality_frame.grid(row=12, column=0, padx=20, pady=(0, 5), sticky="ew")
        quality_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        quality_low = ctk.CTkRadioButton(
            quality_frame,
            text="低",
            variable=self.quality_var,
            value="低"
        )
        quality_low.grid(row=0, column=0, padx=5, pady=5)
        
        quality_med = ctk.CTkRadioButton(
            quality_frame,
            text="中等",
            variable=self.quality_var,
            value="中等"
        )
        quality_med.grid(row=0, column=1, padx=5, pady=5)
        
        quality_high = ctk.CTkRadioButton(
            quality_frame,
            text="高",
            variable=self.quality_var,
            value="高"
        )
        quality_high.grid(row=0, column=2, padx=5, pady=5)
        
        # 分割线
        separator2 = ctk.CTkFrame(self.control_frame, height=2, width=200)
        separator2.grid(row=13, column=0, padx=20, pady=10, sticky="ew")
        
        # 处理按钮
        self.process_button = ctk.CTkButton(
            self.control_frame,
            text="开始处理",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            command=self.start_processing
        )
        self.process_button.grid(row=14, column=0, padx=20, pady=(20, 0), sticky="ew")
        
        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self.control_frame)
        self.progress_bar.grid(row=15, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.progress_bar.set(0)
        
        # 版本信息
        version_label = ctk.CTkLabel(
            self.control_frame,
            text="v1.1.0 FFmpeg",
            font=ctk.CTkFont(size=10)
        )
        version_label.grid(row=16, column=0, padx=20, pady=(20, 10), sticky="e")
    
    def setup_display_panel(self):
        self.display_frame.grid_columnconfigure(0, weight=1)
        self.display_frame.grid_rowconfigure(0, weight=1)
        self.display_frame.grid_rowconfigure(1, weight=2)
        
        # 文件列表框架
        file_list_frame = ctk.CTkFrame(self.display_frame)
        file_list_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        file_list_frame.grid_columnconfigure(0, weight=1)
        file_list_frame.grid_rowconfigure(1, weight=1)
        
        # 文件列表标题
        file_list_label = ctk.CTkLabel(
            file_list_frame,
            text="选定的文件",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        file_list_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # 文件列表
        self.file_list = ctk.CTkTextbox(file_list_frame, state="disabled")
        self.file_list.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # 日志框架
        log_frame = ctk.CTkFrame(self.display_frame)
        log_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        
        # 日志标题
        log_label = ctk.CTkLabel(
            log_frame,
            text="处理日志",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # 日志内容
        self.log_text = ctk.CTkTextbox(log_frame)
        self.log_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.log_text.configure(state="disabled")
    
    def update_segment_value(self, value):
        self.segment_duration = float(value)
        self.segment_value_label.configure(text=f"{self.segment_duration:.1f} 秒")
    
    def select_input_files(self):
        files = filedialog.askopenfilenames(
            title="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm"),
                ("所有文件", "*.*")
            ]
        )
        
        if files:
            self.video_files = list(files)
            self.update_file_list()
            self.log(f"已选择 {len(self.video_files)} 个文件")
    
    def select_output_directory(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_directory = directory
            self.log(f"输出目录: {self.output_directory}")
    
    def update_file_list(self):
        self.file_list.configure(state="normal")
        self.file_list.delete("0.0", "end")
        
        for i, file in enumerate(self.video_files, 1):
            filename = os.path.basename(file)
            self.file_list.insert("end", f"{i}. {filename}\n")
        
        self.file_list.configure(state="disabled")
    
    def log(self, message):
        """向日志区添加消息"""
        self.log_text.configure(state="normal")
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def start_processing(self):
        if not self.video_files:
            messagebox.showerror("错误", "请先选择视频文件")
            return
            
        if not self.output_directory:
            messagebox.showerror("错误", "请选择输出目录")
            return
        
        if self.is_processing:
            messagebox.showinfo("提示", "正在处理中，请稍候")
            return
        
        # 检查是否有FFmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            messagebox.showerror(
                "错误", 
                "未检测到FFmpeg。请确保FFmpeg已安装并添加到系统PATH中。\n"
                "您可以从https://ffmpeg.org/download.html下载FFmpeg。"
            )
            return
            
        # 开始处理
        self.is_processing = True
        self.process_button.configure(state="disabled", text="处理中...")
        self.progress_bar.set(0)
        
        # 在新线程中运行视频处理，避免UI卡顿
        threading.Thread(target=self.process_videos_ffmpeg, daemon=True).start()
    
    def process_videos_ffmpeg(self):
        try:
            total_files = len(self.video_files)
            
            for i, video_file in enumerate(self.video_files, 1):
                filename = os.path.basename(video_file)
                base_name = os.path.splitext(filename)[0]
                
                self.log(f"处理 ({i}/{total_files}): {filename}")
                
                # 创建视频的输出子目录
                video_output_dir = os.path.join(self.output_directory, base_name)
                os.makedirs(video_output_dir, exist_ok=True)
                
                # 获取视频时长
                self.log(f"分析视频: {filename}")
                try:
                    # 使用FFprobe获取视频时长
                    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", 
                          "default=noprint_wrappers=1:nokey=1", video_file]
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    duration = float(result.stdout.strip())
                    self.log(f"视频时长: {duration:.2f}秒")
                except:
                    # 如果FFprobe失败，则尝试使用moviepy
                    self.log("使用备用方法获取视频时长...")
                    video = VideoFileClip(video_file)
                    duration = video.duration
                    video.close()
                    self.log(f"视频时长: {duration:.2f}秒")
                
                # 计算分割数量
                num_segments = int(np.ceil(duration / self.segment_duration))
                self.log(f"将分割为 {num_segments} 个片段")
                
                # 设置编码参数（基于选择的质量）
                crf = "23"  # 默认中等质量
                if self.quality_var.get() == "低":
                    crf = "28"
                elif self.quality_var.get() == "高":
                    crf = "18"
                
                # 分割视频
                for j in range(num_segments):
                    # 计算片段的开始和结束时间
                    start_time = j * self.segment_duration
                    end_time = min((j + 1) * self.segment_duration, duration)
                    segment_duration = end_time - start_time
                    
                    # 输出文件名
                    output_filename = f"{base_name}_segment_{j+1:03d}.mp4"
                    output_path = os.path.join(video_output_dir, output_filename)
                    
                    # 构建FFmpeg命令
                    cmd = [
                        "ffmpeg", "-y", "-ss", str(start_time), "-i", video_file,
                        "-t", str(segment_duration), "-c:v", "libx264", "-crf", crf,
                        "-preset", "fast", "-c:a", "aac", "-b:a", "128k",
                        "-movflags", "+faststart", output_path
                    ]
                    
                    # 执行FFmpeg命令
                    self.log(f"处理片段 {j+1}/{num_segments} (时间: {start_time:.2f}s - {end_time:.2f}s)")
                    process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        universal_newlines=True
                    )
                    
                    # 等待处理完成
                    process.wait()
                    
                    # 检查结果
                    if process.returncode != 0:
                        stderr = process.stderr.read()
                        self.log(f"警告: 处理片段 {j+1} 时出错: {stderr[:100]}...")
                    else:
                        self.log(f"完成片段 {j+1}/{num_segments}: {output_filename}")
                    
                    # 更新进度
                    segment_progress = (j + 1) / num_segments
                    overall_progress = (i - 1 + segment_progress) / total_files
                    self.update_progress(overall_progress)
                
                self.log(f"完成处理: {filename}")
            
            self.log("所有视频处理完成!")
            messagebox.showinfo("完成", "所有视频已处理完成!")
        
        except Exception as e:
            self.log(f"错误: {str(e)}")
            messagebox.showerror("错误", f"处理过程中出错:\n{str(e)}")
        
        finally:
            # 重置UI状态
            self.is_processing = False
            self.process_button.configure(state="normal", text="开始处理")
            self.progress_bar.set(1)  # 完成状态
    
    def update_progress(self, value):
        """更新进度条，这个方法会从工作线程调用"""
        self.after(0, lambda: self.progress_bar.set(value))

if __name__ == "__main__":
    app = VideoSplitterApp()
    app.mainloop() 